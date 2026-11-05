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


# ---------------------------------------------------------------------------------------------
# Q3 / Q4: service on a typical weekday
# ---------------------------------------------------------------------------------------------

def weekday_service_ids(g: dict[str, pd.DataFrame], day: str = "wednesday") -> set[str]:
    """service_ids that run on a normal mid-week day and are actually used by trips.

    Each feed names its weekday pattern differently ("weekday", "MonFri", "26103001"), so we read
    calendar.txt instead of hard-coding names. Wednesday avoids Monday/Friday special patterns.
    """
    cal = g["calendar"]
    active = set(cal.loc[cal[day] == "1", "service_id"])
    return active & set(g["trips"]["service_id"])


def all_departures(g: dict[str, pd.DataFrame], service_ids: set[str] | None = None) -> pd.DataFrame:
    """Every scheduled departure at every stop: trip_id, route_id, direction_id, stop_id, dep_s.

    For frequency-based trips, the template trip's stop times are shifted to each start time
    ("every 3 min from 06:00 to 09:00" becomes 60 trips, each with its own stop times).
    """
    trips = g["trips"]
    if service_ids is not None:
        trips = trips[trips.service_id.isin(service_ids)]
    keep = ["trip_id", "route_id"] + (["direction_id"] if "direction_id" in trips else [])
    st = g["stop_times"][["trip_id", "stop_id", "stop_sequence", "departure_time"]].copy()
    st = st[st.trip_id.isin(trips.trip_id) & st.departure_time.notna()]
    st["dep_s"] = _to_seconds(st["departure_time"])
    st["offset"] = st["dep_s"] - st.groupby("trip_id")["dep_s"].transform("min")

    if "frequencies" in g:
        f = g["frequencies"][g["frequencies"].trip_id.isin(trips.trip_id)].copy()
        f["a"], f["b"], f["h"] = _to_seconds(f["start_time"]), _to_seconds(f["end_time"]), f["headway_secs"].astype(int)
        starts = pd.DataFrame([(r.trip_id, t) for r in f.itertuples() for t in range(r.a, r.b, r.h)],
                              columns=["trip_id", "start_s"])
        starts["run"] = starts.groupby("trip_id").cumcount()
        freq_st = st[st.trip_id.isin(f.trip_id)].merge(starts, on="trip_id")
        freq_st["dep_s"] = freq_st["start_s"] + freq_st["offset"]
        freq_st["trip_id"] = freq_st["trip_id"] + "#" + freq_st["run"].astype(str)
        st = pd.concat([st[~st.trip_id.isin(f.trip_id)], freq_st[st.columns]], ignore_index=True)

    st["base_trip"] = st["trip_id"].str.split("#").str[0]
    out = st.merge(trips[keep].rename(columns={"trip_id": "base_trip"}), on="base_trip")
    return out[["trip_id"] + keep[1:] + ["stop_id", "stop_sequence", "dep_s"]]


def route_peak_service(deps: pd.DataFrame, routes: pd.DataFrame, start_h: int = 7,
                       end_h: int = 9) -> pd.DataFrame:
    """Trips per route and direction starting in the peak window, and the average wait.

    avg_headway_min = window length / number of trips. With only 1 or 2 trips this is more honest
    than averaging the gaps between them (one gap says little, and one trip gives no gap at all).
    """
    first = deps.sort_values("dep_s").groupby("trip_id").first().reset_index()
    peak = first[(first.dep_s >= start_h * 3600) & (first.dep_s < end_h * 3600)]
    keys = ["route_id"] + (["direction_id"] if "direction_id" in deps else [])
    out = peak.groupby(keys).size().rename("peak_trips").reset_index()
    out["avg_headway_min"] = (60 * (end_h - start_h) / out["peak_trips"]).round(0)
    daily = first.groupby(keys).size().rename("daily_trips").reset_index()
    out = daily.merge(out, on=keys, how="left").fillna({"peak_trips": 0})
    r = routes[["route_id", "route_short_name", "route_long_name"]].copy()
    r["route_short_name"] = r["route_short_name"].fillna(r["route_long_name"])
    return out.merge(r, on="route_id", how="left").sort_values("avg_headway_min", ascending=False)


def stop_peak_service(deps: pd.DataFrame, stops: pd.DataFrame, start_h: int = 7,
                      end_h: int = 9) -> pd.DataFrame:
    """Buses per hour at each stop in the peak window, counting all routes that serve it."""
    peak = deps[(deps.dep_s >= start_h * 3600) & (deps.dep_s < end_h * 3600)]
    per_stop = peak.groupby("stop_id").agg(departures=("trip_id", "count"),
                                           routes=("route_id", "nunique")).reset_index()
    per_stop["per_hour"] = per_stop["departures"] / (end_h - start_h)
    s = stops[["stop_id", "stop_name", "stop_lat", "stop_lon"]].copy()
    s[["stop_lat", "stop_lon"]] = s[["stop_lat", "stop_lon"]].astype(float)
    # Stops with no peak departures at all still matter: keep them with 0.
    out = s.merge(per_stop, on="stop_id", how="left").fillna({"departures": 0, "routes": 0, "per_hour": 0})
    return out.sort_values("per_hour")


def line_supply(deps: pd.DataFrame) -> pd.DataFrame:
    """Per route: scheduled trips per day and train/bus-hours per day (trips x run time).

    Train-hours matter because a trip on a long line (Kelana Jaya, ~98 min end to end) serves far
    more passengers than a trip on a short one (Monorail, ~26 min).
    """
    t = deps.groupby("trip_id").agg(route_id=("route_id", "first"), a=("dep_s", "min"), b=("dep_s", "max"))
    t["hours"] = (t.b - t.a) / 3600
    return t.groupby("route_id").agg(daily_trips=("hours", "size"), vehicle_hours=("hours", "sum"),
                                     run_time_min=("hours", lambda h: 60 * h.median())).reset_index()
