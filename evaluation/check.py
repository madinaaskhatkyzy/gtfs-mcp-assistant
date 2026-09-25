import sqlite3, sys
from datetime import datetime

db = sqlite3.connect("data/gtfs.db")

if sys.argv[1] == "stop":
    name = f"%{sys.argv[2]}%"
    print(db.execute(
        "SELECT stop_id, stop_name FROM stops WHERE stop_name LIKE ?", (name,)
    ).fetchall())

elif sys.argv[1] == "departures":
    stop, date, time = sys.argv[2:5]
    d = datetime.strptime(date, "%Y-%m-%d")
    day = d.strftime("%A").lower()
    ymd = d.strftime("%Y%m%d")

    services = db.execute(
        f"""SELECT service_id FROM calendar
            WHERE {day}='1' AND start_date<=? AND end_date>=?""",
        (ymd, ymd)
    ).fetchall()

    ids = [x[0] for x in services]

    exceptions = db.execute(
        "SELECT service_id, exception_type FROM calendar_dates WHERE date=?",
        (ymd,)
    ).fetchall()

    for service, kind in exceptions:
        if kind == "1" and service not in ids:
            ids.append(service)
        elif kind == "2" and service in ids:
            ids.remove(service)

    marks = ",".join("?" * len(ids))

    print(db.execute(
        f"""SELECT st.departure_time, r.route_short_name
            FROM stop_times st
            JOIN trips t ON st.trip_id=t.trip_id
            JOIN routes r ON t.route_id=r.route_id
            WHERE st.stop_id=? AND st.departure_time>=?
            AND t.service_id IN ({marks})
            ORDER BY st.departure_time LIMIT 5""",
        [stop, time + ":00", *ids]
    ).fetchall())

elif sys.argv[1] == "routes":
    stop = sys.argv[2]
    print(db.execute(
        """SELECT DISTINCT r.route_short_name
           FROM stop_times st
           JOIN trips t ON st.trip_id=t.trip_id
           JOIN routes r ON t.route_id=r.route_id
           WHERE st.stop_id=?
           ORDER BY r.route_short_name""",
        (stop,)
    ).fetchall())