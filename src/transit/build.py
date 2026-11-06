"""Build the small data files the dashboard reads, into app/data/.

Run from the project root after fetching:
    python -m src.transit.build

Why: data/raw is not committed to git (too big, and it's someone else's data to re-download), but the
deployed dashboard on Streamlit Cloud only sees what is in the repo. So we pre-compute every table the
dashboard shows here, save them as small parquet files (~1 MB total), and commit those.
"""
from __future__ import annotations

import json

import pandas as pd

from . import config, gtfs
from .clean import flag_outliers, recovery_index, to_long
from .coverage import area_population, assign_area, label_bus_stops
from .patterns import add_calendar, dow_profile, festival_curve, holiday_calendar, holiday_effect

OUT = config.ROOT / "app" / "data"
PEAK = (7 * 3600, 9 * 3600)


def _latest(cat: str):
    return sorted(config.RAW.glob(f"gtfs_{cat}_*.zip"))[-1]


def _save(df: pd.DataFrame, name: str) -> None:
    df.to_parquet(OUT / f"{name}.parquet", index=False)
    print(f"  {name}: {len(df):,} rows")


def build() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    meta = {}

    # Ridership (Q1, Q2)
    cal = holiday_calendar()
    long = add_calendar(flag_outliers(to_long(pd.read_parquet(config.RAW / "ridership_headline.parquet"))), cal)
    meta["ridership_from"], meta["ridership_to"] = str(long.date.min().date()), str(long.date.max().date())
    _save(long[["date", "series", "mode", "line", "riders", "expected", "pct_of_normal", "dow",
                "is_weekend", "is_holiday", "holiday", "group", "is_outlier"]], "ridership")
    _save(recovery_index(long), "recovery")
    _save(dow_profile(long).reset_index(), "dow_profile")
    _save(holiday_effect(long).reset_index(), "holiday_effect")
    _save(pd.concat([festival_curve(long, cal, g, before=7, after=10).assign(festival=g)
                     for g in ["Hari Raya Aidilfitri", "Chinese New Year", "Deepavali"]]), "festival_curves")

    # Timetables (Q3, Q4)
    feeds = {}
    for cat in config.GTFS_CATEGORIES:
        g = gtfs.read_gtfs(_latest(cat))
        feeds[cat] = (g, gtfs.all_departures(g, gtfs.weekday_service_ids(g)))
    meta["gtfs_snapshot"] = _latest("rapid-rail-kl").stem.rsplit("_", 1)[-1]

    rg, rdeps = feeds["rapid-rail-kl"]
    _save(gtfs.route_peak_service(rdeps, rg["routes"]), "rail_peak")

    recent = long[(long.date > long.date.max() - pd.Timedelta(days=365)) & ~long.is_weekend & ~long.is_holiday]
    riders = recent.groupby(["series", "line"])["riders"].mean().reset_index()
    sup = gtfs.line_supply(rdeps)
    sup["series"] = sup.route_id.map(config.RAIL_ROUTE_TO_SERIES)
    crowd = (sup.dropna(subset=["series"]).groupby("series")
             .agg(daily_trips=("daily_trips", "sum"), train_hours=("vehicle_hours", "sum")).reset_index()
             .merge(riders, on="series"))
    crowd["riders_per_trip"] = crowd.riders / crowd.daily_trips
    crowd["riders_per_train_hour"] = crowd.riders / crowd.train_hours
    _save(crowd, "crowding")

    bus_routes, bus_stops = [], []
    for cat in ["rapid-bus-kl", "rapid-bus-mrtfeeder"]:
        g, deps = feeds[cat]
        bus_routes.append(gtfs.route_peak_service(deps, g["routes"]).assign(feed=cat))
        s = gtfs.stop_peak_service(deps, g["stops"])
        lab = label_bus_stops(g["stops"])[["stop_id", "area"]]
        bus_stops.append(s.merge(lab, on="stop_id").assign(feed=cat))
    bus_stops = pd.concat(bus_stops, ignore_index=True)
    _save(pd.concat(bus_routes, ignore_index=True), "bus_routes")
    _save(bus_stops, "bus_stops")

    # Coverage (Q5): rail stations from Rapid Rail + KTM Komuter
    peak_count = lambda d: (d[(d.dep_s >= PEAK[0]) & (d.dep_s < PEAK[1])]
                            .groupby("stop_id").size().rename("peak_departures"))
    rail = rg["stops"].merge(peak_count(rdeps), on="stop_id", how="left").assign(operator="Rapid Rail")
    k = gtfs.read_gtfs(_latest("ktmb"))
    k["trips"] = k["trips"][k["trips"].route_id.isin(config.KTM_KOMUTER_KV_ROUTES)]
    kdeps = gtfs.all_departures(k, gtfs.weekday_service_ids(k))
    ktm = (k["stops"][k["stops"].stop_id.isin(kdeps.stop_id)]
           .merge(peak_count(kdeps), on="stop_id", how="left").assign(operator="KTM Komuter"))
    rail = pd.concat([rail, ktm], ignore_index=True).fillna({"peak_departures": 0})
    rail[["stop_lat", "stop_lon"]] = rail[["stop_lat", "stop_lon"]].astype(float)
    bus_stops["peak_departures"] = bus_stops["departures"]
    rail["area"] = assign_area(rail, bus_stops, max_km=5)
    rail = rail.dropna(subset=["area"])[["stop_id", "stop_name", "stop_lat", "stop_lon", "operator", "area", "peak_departures"]]
    _save(rail, "rail_stations")

    pop = area_population(pd.read_parquet(config.RAW / "population_district.parquet"))
    meta["population_year"] = int(pop.year.iloc[0])
    cov = (pop.set_index("area")
           .join(bus_stops.groupby("area").agg(bus_stops=("stop_id", "count"), bus_peak=("departures", "sum")))
           .join(rail.groupby("area").agg(rail_stations=("stop_id", "count"), rail_peak=("peak_departures", "sum")))
           .fillna(0).reset_index())
    cov["residents_per_bus_stop"] = cov.population / cov.bus_stops
    cov["bus_peak_per_1k"] = 1000 * cov.bus_peak / cov.population
    cov["rail_peak_per_1k"] = 1000 * cov.rail_peak / cov.population
    cov["total_peak_per_1k"] = cov.bus_peak_per_1k + cov.rail_peak_per_1k
    _save(cov, "coverage")

    (OUT / "meta.json").write_text(json.dumps(meta, indent=2))
    print("  meta:", meta)


if __name__ == "__main__":
    build()
