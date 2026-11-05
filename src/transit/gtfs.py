"""Service supply from a GTFS static zip: trips and headways."""
from __future__ import annotations

import zipfile
from pathlib import Path

import pandas as pd


def read_gtfs(path: Path) -> dict[str, pd.DataFrame]:
    with zipfile.ZipFile(path) as z:
        return {n.removesuffix(".txt"): pd.read_csv(z.open(n), dtype=str)
                for n in z.namelist()
                # Skip macOS junk files (__MACOSX/._stops.txt) that some feeds ship with.
                if n.endswith(".txt") and "/" not in n and not n.startswith("._")}


def _to_seconds(hms: pd.Series) -> pd.Series:
    # GTFS times can exceed 24:00:00 for after-midnight trips, so parse by hand.
    parts = hms.str.split(":", expand=True).astype(int)
    return parts[0] * 3600 + parts[1] * 60 + parts[2]


def _expand_frequencies(first: pd.DataFrame, freq: pd.DataFrame) -> pd.DataFrame:
    """Frequency-based feeds list one template trip plus "every N seconds from A to B".

    Rapid KL rail and bus feeds work this way, so without this step a route that really runs
    every 3 minutes would look like it runs once. We turn each window into individual departures.
    """
    f = freq.copy()
    f["a"], f["b"], f["h"] = _to_seconds(f["start_time"]), _to_seconds(f["end_time"]), f["headway_secs"].astype(int)
    rows = [(r.trip_id, t) for r in f.itertuples() for t in range(r.a, r.b, r.h)]
    expanded = pd.DataFrame(rows, columns=["trip_id", "dep_s"])
    scheduled = first[~first.trip_id.isin(f.trip_id)][["trip_id", "dep_s"]]
    return pd.concat([scheduled, expanded], ignore_index=True)


def first_departures(g: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """One row per departure: route, direction, service_id and the start time.

    Note: with frequencies.txt one trip_id can appear many times (once per departure).
    """
    st = g["stop_times"].copy()
    st["dep_s"] = _to_seconds(st["departure_time"])
    st["stop_sequence"] = st["stop_sequence"].astype(int)
    first = st.sort_values("stop_sequence").groupby("trip_id", as_index=False).first()
    if "frequencies" in g:
        first = _expand_frequencies(first, g["frequencies"])
    trips = g["trips"][["trip_id", "route_id", "service_id"] + (["direction_id"] if "direction_id" in g["trips"] else [])]
    return first[["trip_id", "dep_s"]].merge(trips, on="trip_id")


def peak_headways(g: dict[str, pd.DataFrame], start_h: int = 7, end_h: int = 9) -> pd.DataFrame:
    """Average minutes between trip starts per route in the peak window (one service_id day pattern)."""
    t = first_departures(g)
    t = t[(t.dep_s >= start_h * 3600) & (t.dep_s < end_h * 3600)]
    keys = ["route_id", "service_id"] + (["direction_id"] if "direction_id" in t else [])
    t = t.sort_values(keys + ["dep_s"])
    t["gap_min"] = t.groupby(keys)["dep_s"].diff() / 60
    out = t.groupby(keys).agg(trips=("dep_s", "count"), avg_headway_min=("gap_min", "mean")).reset_index()
    routes = g["routes"][["route_id", "route_short_name", "route_long_name"]].copy()
    # The MRT feeder feed leaves short names empty and puts the code (e.g. T117) in the long name.
    routes["route_short_name"] = routes["route_short_name"].fillna(routes["route_long_name"])
    return out.merge(routes, on="route_id", how="left").sort_values("avg_headway_min", ascending=False)
