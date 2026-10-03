"""Print a chart in a layout that is easy to compare against Jagannatha Hora / AstroSage.

python -m app.cli 1990-05-17 14:35 Asia/Kolkata 12.9716 77.5946
python -m app.cli 1990-05-17 14:35 Asia/Kolkata 12.9716 77.5946 --json
"""

import argparse
import sys
from datetime import datetime

from app.engine.chart import compute_chart

ROW = "{:8} {:12} {:>11}  {:18} {:>4} {:>5}  {:13} {}"


def dms(degrees: float) -> str:
    total_seconds = round(degrees * 3600)
    d, rem = divmod(total_seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{d:2d}°{m:02d}'{s:02d}\""


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("date", help="YYYY-MM-DD (local)")
    parser.add_argument("time", help="HH:MM or HH:MM:SS (local wall-clock)")
    parser.add_argument("tz", help="IANA timezone, e.g. Asia/Kolkata")
    parser.add_argument("lat", type=float, help="latitude, north positive")
    parser.add_argument("lon", type=float, help="longitude, east positive")
    parser.add_argument("--fold", type=int, choices=[0, 1], help="which repeated DST hour")
    parser.add_argument("--json", action="store_true", help="print the full chart JSON")
    args = parser.parse_args()

    time_fmt = "%H:%M:%S" if args.time.count(":") == 2 else "%H:%M"
    local = datetime.strptime(f"{args.date} {args.time}", f"%Y-%m-%d {time_fmt}")
    chart = compute_chart(local, args.tz, args.lat, args.lon, args.fold)

    sys.stdout.reconfigure(encoding="utf-8")  # degree signs on Windows consoles
    if args.json:
        print(chart.model_dump_json(indent=2))
        return

    m = chart.meta
    local_str = f"{m.local_time:%Y-%m-%d %H:%M:%S} {m.tz_name} (UTC{m.utc_offset})"
    print(f"Local {local_str}  ->  UTC {m.utc:%Y-%m-%d %H:%M:%S}")
    print(f"Ayanamsa {m.ayanamsa} {dms(m.ayanamsa_value)}  nodes={m.node_type}\n")

    print(ROW.format("Body", "Sign", "Degree", "Nakshatra", "Pada", "House", "Dignity", "Flags"))
    a = chart.ascendant
    print(ROW.format("Asc", a.sign, dms(a.degree_in_sign), a.nakshatra, a.pada, 1, "", ""))
    for p in chart.planets:
        retro = p.retrograde and p.name not in ("Rahu", "Ketu")  # nodes are always retrograde
        flags = ("R" if retro else "") + ("C" if p.combust else "")
        row = (p.name, p.sign, dms(p.degree_in_sign), p.nakshatra, p.pada, p.house)
        print(ROW.format(*row, p.dignity or "-", flags))

    d9 = chart.divisional["D9"]
    placements = ", ".join(f"{p.name} {p.sign}" for p in d9.planets)
    print(f"\nD9 ascendant {d9.ascendant_sign}: {placements}")


if __name__ == "__main__":
    main()
