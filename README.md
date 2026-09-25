# gtfs-mcp-assistant

Telegram-ассистент по расписанию общественного транспорта Каунаса
(Литва), отвечающий на вопросы пассажира естественным языком, беря
каждый факт из GTFS-данных через инструменты MCP.

Полный отчёт с архитектурой, метриками и разбором ошибок — [REPORT.md](REPORT.md).
Описание инструментов MCP-сервера — [TOOLS.md](TOOLS.md).
Журнал решений (в форме трассы TFW) — [TRACE.md](TRACE.md).

## Структура проекта

```
gtfs-mcp-assistant/
├── data/
│   ├── raw/                 # GTFS zip-архив (не в Git, см. Замена города)
│   └── gtfs.db               # SQLite-база, собирается из архива
├── src/
│   ├── gtfs_loader.py         # zip -> SQLite
│   ├── gtfs_queries.py        # вся логика расчётов (поиск, расписание, маршруты)
│   ├── server.py              # MCP-сервер, 5 инструментов
│   ├── agent.py                # CLI-агент на Gemini поверх MCP-сервера
│   └── bot.py                  # Telegram-бот поверх той же агентной логики
├── evaluation/
│   ├── questions.json          # 50 проверочных вопросов с эталонами
│   ├── check.py, check_trip.py # независимое получение эталонов (не через бота)
│   └── run_eval.py             # автоматический прогон агента на всём наборе
├── GOAL.md, TASKS.md, TRACE.md, MEMORY.md   # артефакты TFW
├── REPORT.md, TOOLS.md
└── requirements.txt
```

## Требования

- Python 3.11+
- Node.js (для MCP Inspector)
- Java 11+ (для GTFS Validator, опционально — для повторной проверки данных)
- Аккаунт Google AI Studio с API-ключом Gemini (бесплатный тариф подходит)
- Telegram-бот, созданный через @BotFather (токен)

## Установка

```
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
```

Создайте файл `.env` в корне проекта (не коммитится, см. `.gitignore`):
```
GEMINI_API_KEY=ваш_ключ
GEMINI_MODEL=gemini-3.1-flash-lite
TELEGRAM_BOT_TOKEN=ваш_токен_от_botfather
```

## Запуск каждой части отдельно

### 1. Собрать базу данных из GTFS-фида
```
python src\gtfs_loader.py data\raw\<имя_фида>.zip data\gtfs.db
```

### 2. MCP-сервер — проверка без модели и без Telegram
```
npx @modelcontextprotocol/inspector python src\server.py
```
Откроется веб-интерфейс, где видны все 5 инструментов и можно вызывать
их вручную с произвольными параmetrами.

### 3. Агент — консольный диалог с моделью
```
python src\agent.py
```
Задаёте вопросы в терминале, диалог держит контекст в пределах одного
запуска (Ctrl+C или пустая строка — выход).

### 4. Telegram-бот
```
python src\bot.py
```
Бот работает, пока запущен процесс. Найдите бота в Telegram по имени,
заданному в @BotFather, отправьте `/start`.

### 5. Проверочный контур — одной командой, без Telegram
```
python evaluation\run_eval.py
```
Прогоняет все 50 вопросов через агента, пишет `evaluation/results.json`
(полный лог) и `evaluation/report.md` (сводка метрик + разбор ошибок).
Занимает 10–20 минут из-за пауз на лимит запросов бесплатного тарифа API.

## Замена города

1. Скачайте GTFS Schedule нужного города (≥50 маршрутов) с
   [Mobility Database](https://database.mobilitydata.org), положите
   zip-архив в `data/raw/`.
2. Пересоберите базу: `python src\gtfs_loader.py data\raw\<новый_фид>.zip data\gtfs.db`.
3. Перезапустите сервер/агента/бота — никакой код менять не нужно, вся
   логика работает с любым корректным GTFS Schedule.

## Известные ограничения

См. раздел "Известные ограничения" в [REPORT.md](REPORT.md) — в
частности, `plan_trip` не учитывает рейсы после полуночи, а
автоматический грейдер `run_eval.py` — эвристика по ключевым словам,
не семантическая проверка.
