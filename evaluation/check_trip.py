import sqlite3, sys
from datetime import datetime

db = sqlite3.connect("data/gtfs.db")
db.row_factory = sqlite3.Row

start, end, date, time = sys.argv[1:5]

d = datetime.strptime(date, "%Y-%m-%d")
day = d.strftime("%A").lower()
ymd = d.strftime("%Y%m%d")

ids = [x[0] for x in db.execute(
    f"SELECT service_id FROM calendar WHERE {day}='1' AND start_date<=? AND end_date>=?",
    (ymd, ymd)
)]

for service, kind in db.execute(
    "SELECT service_id, exception_type FROM calendar_dates WHERE date=?",
    (ymd,)
):
    if kind == "1" and service not in ids:
        ids.append(service)
    elif kind == "2" and service in ids:
        ids.remove(service)

marks = ",".join("?" * len(ids))
after = time + ":00"

direct = db.execute(f"""
SELECT r.route_short_name, a.departure_time, b.arrival_time
FROM stop_times a
JOIN stop_times b ON a.trip_id=b.trip_id
JOIN trips t ON t.trip_id=a.trip_id
JOIN routes r ON r.route_id=t.route_id
WHERE a.stop_id=? AND b.stop_id=?
AND CAST(a.stop_sequence AS INTEGER)<CAST(b.stop_sequence AS INTEGER)
AND a.departure_time>=?
AND t.service_id IN ({marks})
ORDER BY a.departure_time LIMIT 5
""", [start, end, after, *ids]).fetchall()

if direct:
    print("DIRECT")
    print([tuple(x) for x in direct])
    sys.exit()

transfer = db.execute(f"""
SELECT r1.route_short_name, a.departure_time,
       s.stop_name, c1.arrival_time,
       r2.route_short_name, c2.departure_time, b.arrival_time
FROM stop_times a
JOIN stop_times c1 ON a.trip_id=c1.trip_id
JOIN trips t1 ON t1.trip_id=a.trip_id
JOIN routes r1 ON r1.route_id=t1.route_id
JOIN stop_times c2 ON c2.stop_id=c1.stop_id
JOIN stop_times b ON b.trip_id=c2.trip_id
JOIN trips t2 ON t2.trip_id=c2.trip_id
JOIN routes r2 ON r2.route_id=t2.route_id
JOIN stops s ON s.stop_id=c1.stop_id
WHERE a.stop_id=? AND b.stop_id=?
AND CAST(a.stop_sequence AS INTEGER)<CAST(c1.stop_sequence AS INTEGER)
AND CAST(c2.stop_sequence AS INTEGER)<CAST(b.stop_sequence AS INTEGER)
AND a.trip_id!=c2.trip_id
AND a.departure_time>=?
AND c2.departure_time>=time(c1.arrival_time, '+3 minutes')
AND t1.service_id IN ({marks})
AND t2.service_id IN ({marks})
ORDER BY b.arrival_time LIMIT 5
""", [start, end, after, *ids, *ids]).fetchall()

print("ONE TRANSFER")
print([tuple(x) for x in transfer])