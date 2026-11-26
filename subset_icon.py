#!/usr/bin/env python3
"""Schneidet die ICON-Datei auf die Zellen zu, die das Widget wirklich braucht.

Behalten werden alle Zellen innerhalb von --radius-km um jeden Punktstandort
und alle Zellen in den Boxen der Höhenbänder. Das spart den grössten Teil der
Rechenzeit von `icon-uv run`, ohne die Ergebnisse zu ändern.

  python subset_icon.py --icon work/icon.nc --catalog locations.json --output work/icon_sub.nc
"""

import argparse
import json
from pathlib import Path

import numpy as np
import xarray as xr

from icon_uv.data import write_netcdf


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--icon", type=Path, required=True)
    p.add_argument("--catalog", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--radius-km", type=float, default=15.0)
    args = p.parse_args()

    entries = json.loads(args.catalog.read_text(encoding="utf-8"))["entries"]
    with xr.open_dataset(args.icon) as ds:
        lat = ds.latitude.values
        lon = ds.longitude.values
        keep = np.zeros(lat.size, dtype=bool)
        for e in entries:
            if e.get("kind") == "region_altitude":
                w, s, east, n = e["bbox"]
                keep |= (lon >= w) & (lon <= east) & (lat >= s) & (lat <= n)
            else:
                phi, origin = np.deg2rad(lat), np.deg2rad(e["latitude"])
                a = (np.sin((phi - origin) / 2) ** 2
                     + np.cos(phi) * np.cos(origin) * np.sin(np.deg2rad(lon - e["longitude"]) / 2) ** 2)
                keep |= 12742 * np.arcsin(np.sqrt(np.clip(a, 0, 1))) <= args.radius_km
        idx = np.flatnonzero(keep)
        print(f"ICON-Zellen: {lat.size} → {idx.size} behalten")
        sub = ds.isel(cell=idx).load()
    write_netcdf(sub, args.output)


if __name__ == "__main__":
    main()
