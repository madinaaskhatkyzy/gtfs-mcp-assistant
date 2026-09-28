"""
Проверочный контур: прогоняет все вопросы из evaluation/questions.json
через реального агента (тот же MCP-сервер + та же модель, что в agent.py)
и честно сверяет ответы с заранее известными эталонами.

Запуск ОДНОЙ командой, без Telegram (как требует ТЗ):
    python evaluation/run_eval.py

Результат:
    evaluation/results.json — полный лог по каждому вопросу (вопрос,
        эталон, реальный ответ агента, какие инструменты вызывались,
        вердикт)
    evaluation/report.md — сводка метрик по категориям + разбор ошибок

ЧЕСТНОСТЬ ИЗМЕРЕНИЙ — что видит и чего не видит этот скрипт:
  - stop_search / next_departures / routes_through_stop / unsupported:
    вердикт ставится автоматически через поиск ключевых слов/чисел в
    тексте ответа агента. Это грубая проверка: она не понимает смысл,
    только присутствие ожидаемых токенов в тексте. Ложные "верно" в
    теории возможны, если агент случайно упомянул правильное число
    в неправильном контексте — при разборе ошибок стоит выборочно
    перечитать несколько "верно" вручную, не только "неверно".
  - trip_planning: автоматический вердикт НЕ ставится вообще — эталон
    здесь текстовое описание маршрута, а не список токенов, и
    надёжно сверить это строкой было бы нечестно. Ответы агента
    сохраняются в results.json и report.md для вопросов этой
    категории помечены как "требует ручной проверки" — их нужно
    прочитать самому и оценить.
  - Каждый вопрос запускается с ЧИСТОЙ историей диалога (без памяти
    предыдущих вопросов проверочного набора) — так эталоны остаются
    независимыми друг от друга, но это же означает, что контроль
    "контекста на 1 шаг" (например "а следующий?") этим прогоном
    НЕ проверяется — для него нужен отдельный ручной тест (см. agent.py).
"""

import asyncio
import json
import os
import re
import time
from pathlib import Path

from google import genai
from google.genai import types
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

PROJECT_ROOT = Path(__file__).resolve().parent.parent
QUESTIONS_PATH = PROJECT_ROOT / "evaluation" / "questions.json"
RESULTS_PATH = PROJECT_ROOT / "evaluation" / "results.json"
REPORT_PATH = PROJECT_ROOT / "evaluation" / "report.md"

MAX_TOOL_STEPS = 8
DELAY_BETWEEN_QUESTIONS_SEC = 2  # чтобы не упереться в лимит запросов/минуту

# Слова-маркеры честного "не знаю" для категории unsupported.
NO_DATA_MARKERS = [
    "не знаю", "нет данных", "не могу", "нет информации",
    "не располагаю", "недоступ", "не содержит", "не предоставляет",
    "реальном времени", "realtime", "нет возможности",
]


def load_env():
    env_path = PROJECT_ROOT / ".env"
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            if "=" in line and not line.strip().startswith("#"):
                key, value = line.strip().split("=", 1)
                os.environ[key] = value


def _safe_generate(client, model, contents, config):
    try:
        return client.models.generate_content(
            model=model, contents=contents, config=config
        ), None
    except Exception as e:
        return None, str(e)


async def ask_agent(session, client, model, config, question: str):
    """Один вопрос — чистая история. Возвращает (текст_ответа | None,
    список вызванных инструментов с параметрами, текст_ошибки | None)."""
    history = [types.Content(role="user", parts=[types.Part(text=question)])]
    tool_log = []

    for _ in range(MAX_TOOL_STEPS):
        response, error = _safe_generate(client, model, history, config)
        if error:
            return None, tool_log, error

        candidate = response.candidates[0]
        part = candidate.content.parts[0]

        if not part.function_call:
            return response.text, tool_log, None

        call = part.function_call
        tool_log.append({"tool": call.name, "args": dict(call.args)})

        result = await session.call_tool(call.name, arguments=dict(call.args))
        tool_text = "\n".join(
            item.text for item in result.content if hasattr(item, "text")
        )

        history.append(candidate.content)
        history.append(
            types.Content(
                role="user",
                parts=[
                    types.Part.from_function_response(
                        name=call.name, response={"result": tool_text}
                    )
                ],
            )
        )

    return None, tool_log, f"Превышен лимит {MAX_TOOL_STEPS} шагов инструментов"


# ---------------------------------------------------------------------
# Автоматические вердикты по категориям
# ---------------------------------------------------------------------

def _grade_stop_search(answer: str, expected: list[str]) -> tuple[str, str]:
    low = answer.lower()
    found = [name for name in expected if name.lower() in low]
    if len(found) == len(expected):
        return "correct", f"все {len(expected)} ожидаемых названий найдены в ответе"
    if found:
        return "partial", f"найдено {len(found)}/{len(expected)}: {found}"
    return "incorrect", "ни одно из ожидаемых названий не найдено в ответе"


def _grade_departures_or_fallback(answer: str, expected: list[str]) -> tuple[str, str]:
    """Для next_departures эталон вида "10:01 №4" — проверяем, что и
    время, и номер маршрута встречаются в ответе (не обязательно рядом,
    это и есть заявленное ограничение метода)."""
    low = answer.lower()
    hits = 0
    for item in expected:
        m = re.match(r"(\d{2}:\d{2})\s*№?\s*(\S+)", item)
        if not m:
            continue
        time_str, route = m.group(1), m.group(2)
        if time_str in answer and re.search(
            rf"\b{re.escape(route)}\b", answer
        ):
            hits += 1
    if hits == len(expected):
        return "correct", f"все {len(expected)} пар время+маршрут найдены"
    if hits > 0:
        return "partial", f"найдено {hits}/{len(expected)} пар время+маршрут"
    return "incorrect", "ни одна пара время+маршрут не найдена"


def _grade_routes_through_stop(answer: str, expected: list[str]) -> tuple[str, str]:
    found = [r for r in expected if re.search(rf"\b{re.escape(r)}\b", answer)]
    if len(found) == len(expected):
        return "correct", f"все {len(expected)} маршрутов найдены"
    if found:
        return "partial", f"найдено {len(found)}/{len(expected)}: {found}"
    return "incorrect", "ни один ожидаемый маршрут не найден в ответе"


def _grade_unsupported(answer: str) -> tuple[str, str]:
    low = answer.lower()
    if any(marker in low for marker in NO_DATA_MARKERS):
        return "correct", "ответ содержит маркер честного 'не знаю'"
    return "incorrect", "в ответе не найдено явного признания отсутствия данных"


def grade(category: str, answer: str | None, expected) -> tuple[str, str]:
    if answer is None:
        return "error", "агент не дал ответа (ошибка API или превышен лимит шагов)"
    if category == "stop_search":
        return _grade_stop_search(answer, expected)
    if category == "next_departures":
        return _grade_departures_or_fallback(answer, expected)
    if category == "routes_through_stop":
        return _grade_routes_through_stop(answer, expected)
    if category == "unsupported":
        return _grade_unsupported(answer)
    if category == "trip_planning":
        return "manual_review", "автоматический вердикт не ставится (см. докстринг)"
    return "unknown_category", ""


# ---------------------------------------------------------------------
# Основной прогон
# ---------------------------------------------------------------------

async def main():
    load_env()
    model = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    questions = json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))

    server = StdioServerParameters(
        command="python", args=[str(PROJECT_ROOT / "src" / "server.py")]
    )

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
                    "ВАЖНО: если find_stop вернул НЕСКОЛЬКО остановок для "
                    "одного названия — НЕ выбирай и не перебирай их сама "
                    "по очереди. Вместо этого сразу дай текстовый ответ "
                    "со списком найденных остановок и спроси, какую имели "
                    "в виду. "
                    "Если данных нет (например, вопрос про живую позицию "
                    "автобуса) — честно скажи 'не знаю', не вызывай "
                    "инструмент наугад и не выдумывай ответ."
                ),
            )

            results = []
            total = sum(len(v) for v in questions.values())
            done = 0

            for category, items in questions.items():
                for item in items:
                    done += 1
                    print(f"[{done}/{total}] ({category}) {item['question']}")

                    answer, tool_log, error = await ask_agent(
                        session, client, model, config, item["question"]
                    )
                    verdict, reason = grade(
                        category, answer, item.get("expected")
                    )

                    results.append(
                        {
                            "category": category,
                            "question": item["question"],
                            "expected": item.get("expected"),
                            "answer": answer,
                            "api_error": error,
                            "tool_calls": tool_log,
                            "verdict": verdict,
                            "reason": reason,
                        }
                    )

                    print(f"    -> {verdict}: {reason}")
                    time.sleep(DELAY_BETWEEN_QUESTIONS_SEC)

    RESULTS_PATH.write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    write_report(results, questions.keys())
    print(f"\nГотово. Полный лог: {RESULTS_PATH}\nОтчёт: {REPORT_PATH}")


def write_report(results: list[dict], categories) -> None:
    lines = ["# Отчёт проверочного контура", ""]
    lines.append(f"Всего вопросов: {len(results)}\n")

    lines.append("## Сводка по категориям\n")
    lines.append("| Категория | correct | partial | incorrect | error | manual_review |")
    lines.append("|---|---|---|---|---|---|")
    for cat in categories:
        cat_results = [r for r in results if r["category"] == cat]
        counts = {}
        for r in cat_results:
            counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
        lines.append(
            f"| {cat} | {counts.get('correct', 0)} | {counts.get('partial', 0)} | "
            f"{counts.get('incorrect', 0)} | {counts.get('error', 0)} | "
            f"{counts.get('manual_review', 0)} |"
        )

    lines.append("\n## Что эта таблица НЕ видит\n")
    lines.append(
        "- stop_search / next_departures / routes_through_stop / unsupported: "
        "вердикт — автоматический поиск ключевых слов/чисел в тексте ответа, "
        "не проверка смысла. Возможны ложные 'correct', если нужное число "
        "упомянуто не в том контексте.\n"
        "- trip_planning: вердикт не автоматизирован вообще, все ответы "
        "в этой категории требуют ручного прочтения (см. ниже).\n"
        "- Каждый вопрос запускался с чистой историей — эта таблица не "
        "проверяет память диалога ('а следующий?').\n"
    )

    lines.append("## Разбор: incorrect и error\n")
    for r in results:
        if r["verdict"] in ("incorrect", "error"):
            lines.append(f"### [{r['category']}] {r['question']}")
            lines.append(f"- Эталон: {r['expected']}")
            lines.append(f"- Ответ агента: {r['answer']}")
            lines.append(f"- Вердикт: {r['verdict']} — {r['reason']}")
            if r["api_error"]:
                lines.append(f"- Ошибка API: {r['api_error']}")
            lines.append("")

    lines.append("## Требуют ручной проверки: trip_planning\n")
    for r in results:
        if r["category"] == "trip_planning":
            lines.append(f"### {r['question']}")
            lines.append(f"- Эталон: {r['expected']}")
            lines.append(f"- Ответ агента: {r['answer']}")
            lines.append("- Ваш вердикт: _______\n")

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    asyncio.run(main())
