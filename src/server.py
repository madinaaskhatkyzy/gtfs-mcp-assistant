"""
MCP-сервер для GTFS-ассистента.

Запуск для проверки через MCP Inspector (без модели, без Telegram):
    npx @modelcontextprotocol/inspector python src/server.py

Путь к базе SQLite берётся из переменной окружения GTFS_DB_PATH,
по умолчанию data/gtfs.db (создаётся скриптом gtfs_loader.py).
"""

import os
from datetime import datetime
from pathlib import Path

from mcp.server.mcpserver import MCPServer

from gtfs_queries import find_stops, next_departures, routes_through_stop, get_fare_info

# Корень проекта — папка на уровень выше src/ (там, где server.py).
# Считаем путь от неё, а не от текущей рабочей папки запуска: иначе
# запуск командой "cd src && python server.py" ищет базу в src/data/...
# вместо настоящего расположения data/gtfs.db в корне проекта.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = str(PROJECT_ROOT / "data" / "gtfs.db")
DB_PATH = os.environ.get("GTFS_DB_PATH", DEFAULT_DB_PATH)

mcp = MCPServer("gtfs-assistant")


@mcp.tool()
def find_stop(
    query: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
) -> list[dict]:
    """Найти остановку по неточному названию ИЛИ по координатам
    (геопозиция пассажира). Передай либо query, либо (lat и lon).

    Если найдено несколько остановок — верни их пользователю как список
    для уточнения, не выбирай молча первую попавшуюся.

    Возвращает список остановок: stop_id, stop_name, координаты,
    и (при поиске по координатам) distance_m — расстояние в метрах.
    """
    return find_stops(DB_PATH, query=query, lat=lat, lon=lon)


@mcp.tool()
def get_next_departures(
    stop_id: str,
    route_short_name: str | None = None,
    date: str | None = None,
    time: str | None = None,
) -> list[dict]:
    """Ближайшие отправления с остановки stop_id.

    stop_id бери из результата find_stop (не выдумывай его).
    route_short_name — опционально, например "12", чтобы отфильтровать
    только нужный маршрут.
    date — опционально, формат YYYY-MM-DD (например "2026-09-28" для
    "в воскресенье"). Если не передано — берётся сегодняшняя дата.
    time — опционально, формат HH:MM (например "06:00"). Если не
    передано — берётся текущее время.

    Возвращает список ближайших отправлений: route_short_name,
    trip_headsign (направление), departure_time.
    Если список пуст — значит на этот день/время рейсов по данным нет;
    так и скажи пользователю, не придумывай время.
    """
    if date and time:
        target = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    elif date:
        target = datetime.strptime(date, "%Y-%m-%d")
    else:
        target = datetime.now()

    return next_departures(
        DB_PATH,
        stop_id=stop_id,
        route_short_name=route_short_name,
        target_datetime=target,
    )


@mcp.tool()
def get_routes_through_stop(stop_id: str) -> list[dict]:
    """Какие маршруты проходят через остановку stop_id — со всеми
    направлениями (headsign) и часами работы (первое/последнее
    отправление за весь период данных, без фильтра по дню недели).

    stop_id бери из результата find_stop.

    Для вопроса "что ходит сейчас/сегодня" используй get_next_departures,
    а не этот инструмент — здесь общие часы работы маршрута, не "сегодня".

    Возвращает список: route_short_name, trip_headsign,
    first_departure, last_departure. Один маршрут может встретиться
    несколько раз — по разу на каждое направление.
    """
    return routes_through_stop(DB_PATH, stop_id=stop_id)


@mcp.tool()
def get_fare(route_short_name: str) -> dict:
    """Цена проезда для маршрута route_short_name, если она есть
    в данных фида.

    Возвращает {"available": true, "price": "...", "currency": "..."}
    если цена найдена, иначе {"available": false}.

    Если available=false — так и скажи пользователю: данных о цене для
    этого маршрута нет. НЕ придумывай число.

    Для вопросов о живой позиции транспорта ("автобус сейчас где?")
    инструмента нет вообще — таких данных в GTFS Schedule не бывает
    никогда. На такие вопросы отвечай "не знаю", не вызывая никакой
    инструмент.
    """
    return get_fare_info(DB_PATH, route_short_name=route_short_name)


if __name__ == "__main__":
    mcp.run()
