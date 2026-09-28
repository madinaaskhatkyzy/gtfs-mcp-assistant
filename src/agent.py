"""
Агент на Gemini поверх MCP-сервера.

Что изменилось по сравнению с прошлой версией:
1. Многошаговые вызовы инструментов: пока модель просит вызвать
   инструмент — выполняем и отдаём результат обратно, и так по кругу
   (с ограничением MAX_TOOL_STEPS), пока модель не даст финальный
   текстовый ответ. Раньше был только один вызов инструмента и всё.
2. Память диалога: история сообщений (history) копится в списке,
   пока работает этот запуск программы, — поэтому "а следующий?"
   понимается в пределах одной сессии (не переживает перезапуск
   agent.py, но по ТЗ и не требуется: "контекст хотя бы на один шаг").

Запуск:
    python src/agent.py
Дальше просто общаешься в цикле, вопрос за вопросом, в одном и том же
запуске. Выход — пустая строка или Ctrl+C.
"""

import asyncio
import os

from google import genai
from google.genai import types
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

DEFAULT_MODEL = "gemini-3.8-flash"
MAX_TOOL_STEPS = 8  # защита от зацикливания, если модель не остановится


def load_env():
    with open(".env", encoding="utf-8") as f:
        for line in f:
            if "=" in line:
                key, value = line.strip().split("=", 1)
                os.environ[key] = value


def _safe_generate(client, contents, config):
    """Обёртка над generate_content с обработкой 503 (перегрузка Gemini)
    и 429 (исчерпана квота), чтобы падение модели не роняло всю программу."""
    model = os.environ.get("GEMINI_MODEL", DEFAULT_MODEL)
    try:
        return client.models.generate_content(
            model=model,
            contents=contents,
            config=config,
        )
    except Exception as e:
        text = str(e)
        if "429" in text and "PerDay" in text:
            print(
                f"\n[Дневная квота free tier для {model} исчерпана. "
                "Повтор через секунды не поможет — квота сбросится завтра. "
                "Можно указать другую модель через GEMINI_MODEL в .env.]\n"
            )
        elif "429" in text:
            print(f"\n[Слишком много запросов в минуту к {model}, подождите немного.]\n")
        else:
            print(f"\n[Gemini временно недоступен: {e}]\n")
        return None


async def main():
    load_env()

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    server = StdioServerParameters(command="python", args=["src/server.py"])

    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            gemini_tools = [
                types.FunctionDeclaration(
                    name=t.name,
                    description=t.description,
                    parameters_json_schema=t.input_schema,
                )
                for t in tools.tools
            ]

            config = types.GenerateContentConfig(
                tools=[types.Tool(function_declarations=gemini_tools)],
                automatic_function_calling=types.AutomaticFunctionCallingConfig(
                    disable=True
                ),
                system_instruction=(
                    "Ты ассистент по общественному транспорту Kaunas. "
                    "Все факты о расписании получай только через инструменты. "
                    "Не выдумывай stop_id, время, маршрут или цену. "
                    "Если для ответа нужно несколько шагов (например, сначала "
                    "найти остановку по названию, потом построить маршрут) — "
                    "вызывай инструменты по очереди, пока не получишь всё "
                    "необходимое для ответа. "
                    "ВАЖНО: если find_stop вернул НЕСКОЛЬКО остановок для "
                    "одного названия — НЕ выбирай и не перебирай их сама "
                    "по очереди. Вместо этого сразу дай текстовый ответ "
                    "со списком найденных остановок и спроси пользователя, "
                    "какую именно он имел в виду. Продолжай (find_stop для "
                    "второй точки маршрута, затем plan_trip и т.д.) только "
                    "после того, как получишь однозначный stop_id — либо "
                    "потому что find_stop сразу вернул одну остановку, либо "
                    "потому что пользователь уточнил, какую из нескольких "
                    "он имеет в виду. "
                    "Если данных нет (например, вопрос про живую позицию "
                    "автобуса) — честно скажи 'не знаю', не вызывай инструмент "
                    "наугад и не выдумывай ответ."
                ),
            )

            # История диалога копится здесь и передаётся целиком при
            # каждом вызове модели — это и даёт понимание "а следующий?".
            history: list[types.Content] = []

            print("Ассистент готов. Пустая строка — выход.\n")

            while True:
                question = input("Вопрос: ").strip()
                if not question:
                    break

                # Запоминаем длину истории, чтобы при сбое Gemini откатить
                # недоделанный обмен (вопрос + промежуточные вызовы
                # инструментов) и не оставлять в истории "висящий" tool call.
                history_len_before = len(history)
                history.append(
                    types.Content(
                        role="user",
                        parts=[types.Part(text=question)],
                    )
                )

                # Цикл вызовов инструментов на один вопрос пользователя.
                for step in range(MAX_TOOL_STEPS):
                    response = _safe_generate(client, history, config)
                    if response is None:
                        # Gemini недоступен — откатываем историю, вопрос
                        # можно будет задать заново.
                        del history[history_len_before:]
                        break

                    candidate = response.candidates[0]
                    part = candidate.content.parts[0]

                    if not part.function_call:
                        # Финальный текстовый ответ — печатаем и сохраняем
                        # в историю, чтобы следующий вопрос имел контекст.
                        print("\nОтвет:", response.text, "\n")
                        history.append(candidate.content)
                        break

                    call = part.function_call
                    print(f"  [шаг {step + 1}] вызываю {call.name}({dict(call.args)})")

                    result = await session.call_tool(
                        call.name, arguments=dict(call.args)
                    )
                    tool_text = "\n".join(
                        item.text for item in result.content if hasattr(item, "text")
                    )

                    # Добавляем в историю: (1) само решение модели вызвать
                    # инструмент, (2) результат этого вызова. Модель увидит
                    # оба при следующей итерации цикла и решит, что делать
                    # дальше — ответить или вызвать ещё один инструмент.
                    history.append(candidate.content)
                    history.append(
                        types.Content(
                            role="user",
                            parts=[
                                types.Part.from_function_response(
                                    name=call.name,
                                    response={"result": tool_text},
                                )
                            ],
                        )
                    )
                else:
                    print(
                        f"\n[Остановлено: превышено {MAX_TOOL_STEPS} шагов "
                        "вызовов инструментов на один вопрос]\n"
                    )


if __name__ == "__main__":
    asyncio.run(main())