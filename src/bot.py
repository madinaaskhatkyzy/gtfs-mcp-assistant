"""
Telegram-бот — интерфейс поверх уже готового агента (MCP + Gemini).

Принимает текст и геопозицию, ведёт диалог с контекстом в пределах
одного чата (история хранится в памяти, per chat_id — этого достаточно
для "контекст хотя бы на один шаг", как требует ТЗ; при перезапуске
бота история, как и в agent.py, не сохраняется).

Запуск:
    python src/bot.py

Один MCP-сервер и одна сессия на всё время жизни бота (не поднимаем
новый сервер на каждое сообщение) — сервер стартует один раз при
запуске бота и работает, пока бот не остановлен.
"""

import asyncio
import os
from pathlib import Path

from google import genai
from google.genai import types
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MAX_TOOL_STEPS = 8
MAX_RETRIES_ON_RATE_LIMIT = 5


def load_env():
    env_path = PROJECT_ROOT / ".env"
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            if "=" in line and not line.strip().startswith("#"):
                key, value = line.strip().split("=", 1)
                os.environ[key] = value


def _extract_retry_delay(error_text: str) -> float:
    import re

    m = re.search(r"retry in ([\d.]+)s", error_text)
    if m:
        return float(m.group(1)) + 1
    return 8.0


async def _safe_generate(client, model, contents, config):
    last_error = None
    for attempt in range(MAX_RETRIES_ON_RATE_LIMIT):
        try:
            return (
                client.models.generate_content(
                    model=model, contents=contents, config=config
                ),
                None,
            )
        except Exception as e:
            last_error = str(e)
            if "429" in last_error or "503" in last_error:
                wait = _extract_retry_delay(last_error)
                await asyncio.sleep(wait)
                continue
            break
    return None, last_error


async def ask_agent(session, client, model, config, history: list, question: str):
    """Тот же цикл многошаговых вызовов инструментов, что в agent.py,
    но работает на истории конкретного чата (передаётся снаружи) —
    так каждый чат в Telegram ведёт свой независимый диалог."""
    history.append(types.Content(role="user", parts=[types.Part(text=question)]))
    start_len = len(history) - 1  # для отката при ошибке

    for _ in range(MAX_TOOL_STEPS):
        response, error = await _safe_generate(client, model, history, config)
        if error:
            del history[start_len:]  # откатываем незавершённый обмен
            return None, error

        candidate = response.candidates[0]
        part = candidate.content.parts[0]

        if not part.function_call:
            history.append(candidate.content)
            return response.text, None

        call = part.function_call
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

    del history[start_len:]
    return None, f"Превышен лимит {MAX_TOOL_STEPS} шагов вызовов инструментов"


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я помогу узнать расписание автобусов Каунаса.\n\n"
        "Можно спросить, например:\n"
        "— Когда следующий 12-й от Klinikos?\n"
        "— Что ходит через Ateities pl.?\n"
        "— Как доехать от вокзала до аэропорта?\n\n"
        "Также можно прислать геопозицию — найду остановки рядом."
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    question = update.message.text

    histories = context.application.bot_data["histories"]
    history = histories.setdefault(chat_id, [])

    session = context.application.bot_data["session"]
    client = context.application.bot_data["client"]
    model = context.application.bot_data["model"]
    config = context.application.bot_data["config"]

    await update.message.chat.send_action("typing")
    answer, error = await ask_agent(session, client, model, config, history, question)

    if answer is None:
        await update.message.reply_text(
            "Извините, не получилось ответить (временная проблема с моделью). "
            "Попробуйте, пожалуйста, ещё раз."
        )
        return

    await update.message.reply_text(answer)


async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lat = update.message.location.latitude
    lon = update.message.location.longitude
    question = (
        f"Пользователь отправил геопозицию: широта {lat}, долгота {lon}. "
        "Найди ближайшие остановки."
    )

    chat_id = update.effective_chat.id
    histories = context.application.bot_data["histories"]
    history = histories.setdefault(chat_id, [])

    session = context.application.bot_data["session"]
    client = context.application.bot_data["client"]
    model = context.application.bot_data["model"]
    config = context.application.bot_data["config"]

    await update.message.chat.send_action("typing")
    answer, error = await ask_agent(session, client, model, config, history, question)

    if answer is None:
        await update.message.reply_text(
            "Извините, не получилось найти остановки рядом. Попробуйте ещё раз."
        )
        return

    await update.message.reply_text(answer)


async def run_bot():
    load_env()
    model = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

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
                    "Ты ассистент по общественному транспорту Kaunas в Telegram. "
                    "Все факты о расписании получай только через инструменты. "
                    "Не выдумывай stop_id, время, маршрут или цену. "
                    "ВАЖНО: если find_stop вернул НЕСКОЛЬКО остановок для "
                    "одного названия или координат — НЕ выбирай сама. "
                    "Дай текстовый ответ со списком найденных остановок и "
                    "спроси, какую пользователь имел в виду. "
                    "Если данных нет (например, вопрос про живую позицию "
                    "автобуса) — честно скажи 'не знаю', не выдумывай ответ. "
                    "Отвечай кратко и по делу — это переписка в Telegram, "
                    "не отчёт."
                ),
            )

            application = Application.builder().token(
                os.environ["TELEGRAM_BOT_TOKEN"]
            ).build()

            application.bot_data["session"] = session
            application.bot_data["client"] = client
            application.bot_data["model"] = model
            application.bot_data["config"] = config
            application.bot_data["histories"] = {}

            application.add_handler(CommandHandler("start", start_command))
            application.add_handler(
                MessageHandler(filters.LOCATION, handle_location)
            )
            application.add_handler(
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)
            )

            print("Бот запущен. Ctrl+C для остановки.")
            await application.initialize()
            await application.start()
            await application.updater.start_polling()

            # Держим процесс живым, пока не прервут вручную.
            try:
                await asyncio.Event().wait()
            finally:
                await application.updater.stop()
                await application.stop()
                await application.shutdown()


if __name__ == "__main__":
    asyncio.run(run_bot())
