"""
Загрузка GTFS-фида (zip-архив с таблицами agency, stops, routes, trips,
stop_times, calendar, calendar_dates и т.д.) в локальную базу SQLite.

Почему SQLite: удобные JOIN'ы для запросов вида "маршруты через остановку
с учётом календаря" и "маршрут A->B с пересадкой", не нужно поднимать
отдельный сервер БД, файл базы можно пересоздавать при смене города.

Запуск как скрипта:
    python src/gtfs_loader.py data/raw/mdb-1041-202609210002.zip data/gtfs.db
"""

import sqlite3
import zipfile
import csv
import io
import sys
from pathlib import Path

# Таблицы, которые пытаемся загрузить, если они есть в архиве.
# agency, stops, routes, trips, stop_times обязательны по GTFS Schedule;
# calendar и calendar_dates — хотя бы одна из двух должна быть обязательно.
GTFS_TABLES = [
    "agency",
    "stops",
    "routes",
    "trips",
    "stop_times",
    "calendar",
    "calendar_dates",
    "fare_attributes",
    "fare_rules",
    "shapes",
]


def _read_csv_from_zip(zf: zipfile.ZipFile, filename: str):
    """Читает filename.txt из архива как список словарей (csv.DictReader).
    Возвращает None, если файла нет в архиве (необязательные файлы)."""
    try:
        with zf.open(f"{filename}.txt") as raw:
            # GTFS обычно в UTF-8, некоторые фиды — с BOM.
            text = io.TextIOWrapper(raw, encoding="utf-8-sig")
            reader = csv.DictReader(text)
            rows = list(reader)
            fieldnames = reader.fieldnames or []
            return fieldnames, rows
    except KeyError:
        return None


def load_gtfs(zip_path: str, db_path: str) -> None:
    """Распаковывает и загружает GTFS zip в SQLite-базу db_path.
    Каждая таблица из GTFS_TABLES становится таблицей в SQLite с теми же
    именами колонок (все колонки — TEXT, конвертация типов делается
    на этапе запросов, не хранения — так надёжнее для "грязных" полей)."""

    zip_path = Path(zip_path)
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Пересоздаём базу с нуля при каждой загрузке — проще, чем мигрировать.
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()

    with zipfile.ZipFile(zip_path) as zf:
        for table in GTFS_TABLES:
            result = _read_csv_from_zip(zf, table)
            if result is None:
                print(f"  [пропущено] {table}.txt отсутствует в фиде")
                continue

            fieldnames, rows = result
            if not fieldnames:
                continue

            # Создаём таблицу: все колонки TEXT.
            cols_sql = ", ".join(f'"{c}" TEXT' for c in fieldnames)
            cur.execute(f'DROP TABLE IF EXISTS "{table}"')
            cur.execute(f'CREATE TABLE "{table}" ({cols_sql})')

            placeholders = ", ".join("?" for _ in fieldnames)
            insert_sql = f'INSERT INTO "{table}" VALUES ({placeholders})'
            cur.executemany(
                insert_sql,
                [tuple(row.get(c, "") for c in fieldnames) for row in rows],
            )
            print(f"  [ok] {table}.txt -> {len(rows)} строк")

    # Индексы под наши будущие запросы — сильно ускоряют JOIN и фильтры.
    index_statements = [
        'CREATE INDEX IF NOT EXISTS idx_stop_times_stop ON stop_times(stop_id)',
        'CREATE INDEX IF NOT EXISTS idx_stop_times_trip ON stop_times(trip_id)',
        'CREATE INDEX IF NOT EXISTS idx_trips_route ON trips(route_id)',
        'CREATE INDEX IF NOT EXISTS idx_trips_service ON trips(service_id)',
        'CREATE INDEX IF NOT EXISTS idx_calendar_dates_service '
        'ON calendar_dates(service_id, date)',
    ]
    for stmt in index_statements:
        try:
            cur.execute(stmt)
        except sqlite3.OperationalError as e:
            # Например, если таблицы calendar_dates нет в этом фиде.
            print(f"  [индекс пропущен] {stmt} -> {e}")

    conn.commit()
    conn.close()
    print(f"Готово: {db_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Использование: python gtfs_loader.py <путь_к_zip> <путь_к_db>")
        sys.exit(1)
    load_gtfs(sys.argv[1], sys.argv[2])
