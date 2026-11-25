#!/usr/bin/env python3
"""Exportiert UV-Daten aus einem icon-uv-Grid für das Scriptable-Widget.

Schreibt zwei Dateien in --out-dir:
  daily-uv.json   Tagesspitzen im offiziellen icon-uv-Vertrag ("daily-uv")
  hourly-uv.json  kompakte Stundenmittel (Prognose + wolkenlos) und
                  Schnee-Albedo pro Tag für alle Punktstandorte

Aufruf (nach `icon-uv run ... --output work/uv.nc`):
  python build_widget_json.py --grid work/uv.nc --catalog locations.json \
      --issued-at 2026-10-29T05:20:00Z --days 4 --out-dir docs
"""

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import xarray as xr

from icon_uv import compute_points, export_daily_file, load_locations

TZ = ZoneInfo("Europe/Zurich")
DAYLIGHT_THRESHOLD = 0.02  # UVI; kleinere Werte (Nacht/Dämmerung) werden weggelassen


def _num(value, digits=2):
    value = float(value)
    return round(value, digits) if math.isfinite(value) else None


def _member_median(da):
    """Ensemble-Median für die Anzeige; CTRL-Läufe bleiben unverändert."""
    return da.median("member", skipna=True) if "member" in da.dims else da


def _iso_utc(t):
    return np.datetime_as_string(np.datetime64(t, "s"), unit="m") + "Z"


def _local_date(t):
    seconds = np.datetime64(t, "s").astype("int64")
    return datetime.fromtimestamp(int(seconds), tz=timezone.utc).astimezone(TZ).date().isoformat()


def hourly_payload(grid_path, catalog, daily):
    valid_dates = set(daily["valid_dates"])
    with xr.open_dataset(grid_path) as grid:
        points = compute_points(grid, catalog.points)

    uvi = _member_median(points["uvi"])
    clear = _member_median(points["clear_sky_uvi"])
    albedo = _member_median(points["uv_albedo"]) if "uv_albedo" in points else None
    times = points["time"].values

    out = {}
    for j, location in enumerate(catalog.points):
        series, albedo_by_date = [], {}
        for i, t in enumerate(times):
            date = _local_date(t)
            if date not in valid_dates:
                continue
            u = float(uvi.isel(poi=j, time=i))
            c = float(clear.isel(poi=j, time=i))
            if not (math.isfinite(c) and c >= DAYLIGHT_THRESHOLD):
                continue
            series.append([_iso_utc(t), _num(u), _num(c)])
            if albedo is not None:
                a = float(albedo.isel(poi=j, time=i) if "time" in albedo.dims else albedo.isel(poi=j))
                if math.isfinite(a):
                    albedo_by_date[date] = max(albedo_by_date.get(date, 0.0), round(a, 2))
        out[location.id] = {
            "label": location.label or location.id,
            "altitude_m": location.altitude_m,
            "series": series,
            "uv_albedo_max": albedo_by_date,
        }

    return {
        "schema": "widget-hourly-uv",
        "version": 1,
        "issued_at": daily["issued_at"],
        "timezone": "Europe/Zurich",
        "sources": daily["sources"],
        "valid_dates": daily["valid_dates"],
        "series_format": ["interval_mid_utc", "uvi", "clear_sky_uvi"],
        "notes": "Stundenmittel am Punkt (Ensemble: Median der Member); "
                 "uv_albedo_max ist die experimentelle Schnee-Albedo aus ICON SNOWC.",
        "points": out,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--grid", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--issued-at", required=True)
    parser.add_argument("--days", type=int, default=4)
    parser.add_argument("--out-dir", type=Path, default=Path("docs"))
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    catalog = load_locations(args.catalog)

    daily = export_daily_file(args.grid, catalog, issued_at=args.issued_at,
                              days=args.days, output=args.out_dir / "daily-uv.json")
    hourly = hourly_payload(args.grid, catalog, daily)

    target = args.out_dir / "hourly-uv.json"
    tmp = target.with_suffix(".tmp")
    tmp.write_text(json.dumps(hourly, ensure_ascii=False, allow_nan=False, separators=(",", ":")),
                   encoding="utf-8")
    tmp.replace(target)

    for entry in daily["entries"]:
        if entry["day"] == 0:
            loc = entry["location"]
            print(f"{loc.get('label', loc['id']):>16} {loc.get('altitude_m', ''):>6} m  "
                  f"UVI {entry.get('display_uvi')}  ({entry['status']})")


if __name__ == "__main__":
    main()
