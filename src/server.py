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

from gtfs_queries import (
    find_stops,
    next_departures,
    routes_through_stop,
    get_fare_info,
    plan_direct_trip,
    plan_one_transfer_trip,
)


# Корень проекта — папка на уровень выше src/ (там, где server.py).
# Считаем путь от неё, а не от текущей рабочей папки запуска.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = str(PROJECT_ROOT / "data" / "gtfs.db")
DB_PATH = os.environ.get("GTFS_DB_PATH", DEFAULT_DB_PATH)


mcp = MCPServer("gtfs-assistant")


# ---------------------------------------------------------------------
# Инструмент 1: поиск остановки
# ---------------------------------------------------------------------

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
    return find_stops(
        DB_PATH,
        query=query,
        lat=lat,
        lon=lon,
    )


# ---------------------------------------------------------------------
# Инструмент 2: ближайшие отправления
# ---------------------------------------------------------------------

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

    date — опционально, формат YYYY-MM-DD.
    time — опционально, формат HH:MM.

    Возвращает список ближайших отправлений: route_short_name,
    trip_headsign (направление), departure_time.

    Если список пуст — значит на этот день/время рейсов по данным нет;
    так и скажи пользователю, не придумывай время.
    """

    if date and time:
        target = datetime.strptime(
            f"{date} {time}",
            "%Y-%m-%d %H:%M",
        )
    elif date:
        target = datetime.strptime(
            date,
            "%Y-%m-%d",
        )
    else:
        target = datetime.now()

    return next_departures(
        DB_PATH,
        stop_id=stop_id,
        route_short_name=route_short_name,
        target_datetime=target,
    )


# ---------------------------------------------------------------------
# Инструмент 3: маршруты через остановку
# ---------------------------------------------------------------------

@mcp.tool()
def get_routes_through_stop(
    stop_id: str,
) -> list[dict]:
    """Какие маршруты проходят через остановку stop_id — со всеми
    направлениями (headsign) и часами работы.

    stop_id бери из результата find_stop.

    Для вопроса "что ходит сейчас/сегодня" используй
    get_next_departures, а не этот инструмент.

    Возвращает список: route_short_name, trip_headsign,
    first_departure, last_departure.

    Один маршрут может встретиться несколько раз —
    по одному разу на каждое направление.
    """
    return routes_through_stop(
        DB_PATH,
        stop_id=stop_id,
    )


# ---------------------------------------------------------------------
# Инструмент 4: информация о цене
# ---------------------------------------------------------------------

@mcp.tool()
def get_fare(
    route_short_name: str,
) -> dict:
    """Цена проезда для маршрута route_short_name, если она есть
    в данных GTFS-фида.

    Возвращает:
    {"available": true, "price": "...", "currency": "..."}
    если цена найдена.

    Если данных нет:
    {"available": false}

    Если available=false — не придумывай цену.

    Для вопросов о живой позиции транспорта ("автобус сейчас где?")
    инструмента нет: GTFS Schedule не содержит realtime-позиции.
    """
    return get_fare_info(
        DB_PATH,
        route_short_name=route_short_name,
    )


# ---------------------------------------------------------------------
# Инструмент 5: маршрут A -> B, максимум одна пересадка
# ---------------------------------------------------------------------

@mcp.tool()
def plan_trip(
    from_stop_id: str,
    to_stop_id: str,
    date: str | None = None,
    time: str | None = None,
) -> list[dict]:
    """Найти поездку от остановки A до остановки B.

    from_stop_id и to_stop_id бери из результата find_stop.

    date — дата поездки в формате YYYY-MM-DD.
    time — желаемое время отправления в формате HH:MM.

    Сначала ищет прямой маршрут A -> B.

    Если прямого маршрута после указанного времени нет,
    ищет маршрут A -> C -> B с одной пересадкой.

    Если подходящего варианта нет — возвращает пустой список.
    """

    if date and time:
        target = datetime.strptime(
            f"{date} {time}",
            "%Y-%m-%d %H:%M",
        )
    elif date:
        target = datetime.strptime(
            date,
            "%Y-%m-%d",
        )
    else:
        target = datetime.now()

    # Сначала пытаемся найти прямой маршрут.
    direct = plan_direct_trip(
        DB_PATH,
        from_stop_id=from_stop_id,
        to_stop_id=to_stop_id,
        target_datetime=target,
    )

    if direct:
        return direct

    # Если прямого маршрута нет — ищем одну пересадку.
    return plan_one_transfer_trip(
        DB_PATH,
        from_stop_id=from_stop_id,
        to_stop_id=to_stop_id,
        target_datetime=target,
    )


# ---------------------------------------------------------------------
# Запуск MCP-сервера
# ---------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()