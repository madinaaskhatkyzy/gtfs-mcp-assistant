"""
Запросы к SQLite-базе, загруженной gtfs_loader.py.

Здесь — вся логика вычислений (поиск остановки, ближайшие отправления
с учётом календаря). MCP-сервер (server.py) только вызывает эти функции
и оборачивает результат в ответ инструмента — сам не считает расписание,
как требует ТЗ ("модель не считает расписание сама").
"""

import sqlite3
import math
from datetime import date, datetime, timedelta

EARTH_RADIUS_M = 6371000


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _haversine_m(lat1, lon1, lat2, lon2) -> float:
    """Расстояние между двумя точками в метрах (для поиска ближайших
    остановок по координатам)."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


def _gtfs_time_to_seconds(t: str) -> int:
    """GTFS-время вида "HH:MM:SS", час может быть >= 24 (рейс после
    полуночи). Переводим в секунды от начала "сервисных суток"."""
    h, m, s = (int(x) for x in t.strip().split(":"))
    return h * 3600 + m * 60 + s


def _seconds_to_hhmm(sec: int) -> str:
    sec = sec % (24 * 3600)
    h, rem = divmod(sec, 3600)
    m, _ = divmod(rem, 60)
    return f"{h:02d}:{m:02d}"


# ---------------------------------------------------------------------
# Инструмент 1: поиск остановки по координатам или неточному названию
# ---------------------------------------------------------------------

def find_stops(
    db_path: str,
    query: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
    radius_m: float = 500,
    limit: int = 5,
) -> list[dict]:
    """Ищет остановки одним из двух способов:
      - по координатам (lat, lon): все остановки в радиусе radius_m,
        отсортированы по расстоянию;
      - по названию (query): нечёткий поиск по подстроке (без учёта
        регистра), отсортирован по длине совпавшего имени (короче — точнее).

    Нужен хотя бы один из способов. Если совпадений несколько — сервер
    возвращает их все (limit штук), решение "уточнить у пользователя,
    а не выбрать молча" остаётся за агентом/ботом, не за сервером.

    Возвращает список словарей: stop_id, stop_name, stop_lat, stop_lon,
    и, для поиска по координатам, distance_m.
    """
    conn = _connect(db_path)
    try:
        if lat is not None and lon is not None:
            rows = conn.execute(
                "SELECT stop_id, stop_name, stop_lat, stop_lon FROM stops"
            ).fetchall()
            scored = []
            for r in rows:
                try:
                    slat, slon = float(r["stop_lat"]), float(r["stop_lon"])
                except (TypeError, ValueError):
                    continue
                dist = _haversine_m(lat, lon, slat, slon)
                if dist <= radius_m:
                    scored.append(
                        {
                            "stop_id": r["stop_id"],
                            "stop_name": r["stop_name"],
                            "stop_lat": slat,
                            "stop_lon": slon,
                            "distance_m": round(dist),
                        }
                    )
            scored.sort(key=lambda x: x["distance_m"])
            return scored[:limit]

        if query:
            like = f"%{query.strip()}%"
            rows = conn.execute(
                "SELECT stop_id, stop_name, stop_lat, stop_lon FROM stops "
                "WHERE stop_name LIKE ? COLLATE NOCASE",
                (like,),
            ).fetchall()
            result = [
                {
                    "stop_id": r["stop_id"],
                    "stop_name": r["stop_name"],
                    "stop_lat": r["stop_lat"],
                    "stop_lon": r["stop_lon"],
                }
                for r in rows
            ]
            result.sort(key=lambda x: len(x["stop_name"] or ""))
            return result[:limit]

        raise ValueError("Нужно передать либо (lat, lon), либо query")
    finally:
        conn.close()


# ---------------------------------------------------------------------
# Инструмент 2: ближайшие отправления маршрута с остановки
# ---------------------------------------------------------------------

def _active_service_ids(conn: sqlite3.Connection, target_date: date) -> set[str]:
    """Определяет, какие service_id активны на target_date, объединяя
    calendar.txt (регулярное расписание по дням недели, диапазон дат)
    и calendar_dates.txt (исключения: добавить/убрать конкретный день)."""
    active: set[str] = set()

    weekday_col = [
        "monday", "tuesday", "wednesday", "thursday",
        "friday", "saturday", "sunday",
    ][target_date.weekday()]
    date_str = target_date.strftime("%Y%m%d")

    try:
        rows = conn.execute(
            f'SELECT service_id, start_date, end_date, "{weekday_col}" '
            f"FROM calendar"
        ).fetchall()
        for r in rows:
            if (
                r[weekday_col] == "1"
                and r["start_date"] <= date_str <= r["end_date"]
            ):
                active.add(r["service_id"])
    except sqlite3.OperationalError:
        pass  # в этом фиде может не быть calendar.txt

    try:
        rows = conn.execute(
            "SELECT service_id, exception_type FROM calendar_dates "
            "WHERE date = ?",
            (date_str,),
        ).fetchall()
        for r in rows:
            if r["exception_type"] == "1":
                active.add(r["service_id"])
            elif r["exception_type"] == "2":
                active.discard(r["service_id"])
    except sqlite3.OperationalError:
        pass  # в этом фиде может не быть calendar_dates.txt

    return active


def next_departures(
    db_path: str,
    stop_id: str,
    route_short_name: str | None = None,
    target_datetime: datetime | None = None,
    limit: int = 5,
) -> list[dict]:
    """Ближайшие отправления с остановки stop_id на момент target_datetime
    (по умолчанию — сейчас), опционально отфильтрованные по номеру
    маршрута route_short_name.

    Учитывает calendar/calendar_dates: рейс попадает в выдачу, только
    если его service_id активен в тот календарный день. Также проверяет
    рейсы, у которых departure_time >= 24:00:00 и которые фактически
    относятся к предыдущему календарному дню (рейс после полуночи).

    Возвращает список словарей: route_short_name, trip_headsign,
    departure_time (HH:MM), stop_sequence.
    """
    if target_datetime is None:
        target_datetime = datetime.now()

    conn = _connect(db_path)
    try:
        results = []

        # Проверяем "сегодня" и "вчера" (рейсы вчерашнего дня после
        # полуночи, записанные как 24:xx:xx-29:xx:xx, могут ещё идти).
        for day_offset in (0, -1):
            check_date = target_datetime.date() + timedelta(days=day_offset)
            active_services = _active_service_ids(conn, check_date)
            if not active_services:
                continue

            # Секунды с начала check_date до target_datetime.
            target_seconds = (
                target_datetime - datetime.combine(check_date, datetime.min.time())
            ).total_seconds()

            placeholders = ", ".join("?" for _ in active_services)
            sql = f"""
                SELECT
                    r.route_short_name AS route_short_name,
                    t.trip_headsign AS trip_headsign,
                    st.departure_time AS departure_time,
                    st.stop_sequence AS stop_sequence
                FROM stop_times st
                JOIN trips t ON t.trip_id = st.trip_id
                JOIN routes r ON r.route_id = t.route_id
                WHERE st.stop_id = ?
                  AND t.service_id IN ({placeholders})
            """
            params: list = [stop_id, *active_services]
            if route_short_name:
                sql += " AND r.route_short_name = ?"
                params.append(route_short_name)

            rows = conn.execute(sql, params).fetchall()
            for r in rows:
                try:
                    dep_sec = _gtfs_time_to_seconds(r["departure_time"])
                except (ValueError, AttributeError):
                    continue
                if dep_sec >= target_seconds:
                    results.append(
                        {
                            "route_short_name": r["route_short_name"],
                            "trip_headsign": r["trip_headsign"],
                            "departure_time": _seconds_to_hhmm(dep_sec),
                            "_sort_key": (check_date.toordinal() * 86400)
                            + dep_sec,
                        }
                    )

        results.sort(key=lambda x: x["_sort_key"])
        for r in results:
            del r["_sort_key"]
        return results[:limit]
    finally:
        conn.close()


# ---------------------------------------------------------------------
# Инструмент 3: маршруты, проходящие через остановку
# ---------------------------------------------------------------------

def routes_through_stop(db_path: str, stop_id: str) -> list[dict]:
    """Какие маршруты проходят через остановку stop_id, с направлениями
    (headsign) и часами работы (первое и последнее отправление среди
    ВСЕХ дней недели, без фильтра по календарю — это "часы работы
    маршрута вообще", а не "сегодня"; для "сегодня" используй
    get_next_departures).

    Возвращает список словарей: route_short_name, trip_headsign,
    first_departure (HH:MM), last_departure (HH:MM).
    Одна и та же route_short_name может встретиться несколько раз —
    по одному разу на каждое уникальное направление (headsign).
    """
    conn = _connect(db_path)
    try:
        rows = conn.execute(
            """
            SELECT
                r.route_short_name AS route_short_name,
                t.trip_headsign AS trip_headsign,
                st.departure_time AS departure_time
            FROM stop_times st
            JOIN trips t ON t.trip_id = st.trip_id
            JOIN routes r ON r.route_id = t.route_id
            WHERE st.stop_id = ?
            """,
            (stop_id,),
        ).fetchall()

        # Группируем по (маршрут, направление), ищем мин/макс время.
        grouped: dict[tuple[str, str], list[int]] = {}
        for r in rows:
            try:
                dep_sec = _gtfs_time_to_seconds(r["departure_time"])
            except (ValueError, AttributeError):
                continue
            key = (r["route_short_name"], r["trip_headsign"] or "")
            grouped.setdefault(key, []).append(dep_sec)

        result = []
        for (route, headsign), times in grouped.items():
            result.append(
                {
                    "route_short_name": route,
                    "trip_headsign": headsign,
                    "first_departure": _seconds_to_hhmm(min(times)),
                    "last_departure": _seconds_to_hhmm(max(times)),
                }
            )
        result.sort(key=lambda x: (x["route_short_name"], x["trip_headsign"]))
        return result
    finally:
        conn.close()


# ---------------------------------------------------------------------
# Инструмент 4: информация о цене проезда (честно "не знаю", если нет)
# ---------------------------------------------------------------------

def get_fare_info(db_path: str, route_short_name: str) -> dict:
    """Цена проезда для маршрута route_short_name, если она есть в
    данных (fare_attributes.txt + fare_rules.txt). Это НЕ инструмент
    "живой позиции автобуса" — такой информации в GTFS Schedule нет
    никогда, для неё вообще нет инструмента, и агент должен сам сказать
    "не знаю", не пытаясь вызвать что-то для этого случая.

    Возвращает {"available": True, "price": ..., "currency": ...}
    если данные есть, иначе {"available": False} — агент должен
    сказать пользователю, что цены для этого маршрута в данных нет,
    а не придумывать число.
    """
    conn = _connect(db_path)
    try:
        row = conn.execute(
            """
            SELECT fa.price AS price, fa.currency_type AS currency
            FROM fare_rules fr
            JOIN fare_attributes fa ON fa.fare_id = fr.fare_id
            JOIN routes r ON r.route_id = fr.route_id
            WHERE r.route_short_name = ?
            LIMIT 1
            """,
            (route_short_name,),
        ).fetchone()

        if row is None:
            return {"available": False}
        return {
            "available": True,
            "price": row["price"],
            "currency": row["currency"],
        }
    finally:
        conn.close()
