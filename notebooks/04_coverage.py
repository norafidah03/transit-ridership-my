# %% [markdown]
# # 04 · Coverage vs population (Q5)
# Question: which areas have many people but little public transport?
#
# The method, step by step:
# 1. Put every bus stop and rail station in an area, using the council code at the start of each
#    stop code (see `src/transit/coverage.py` for why, and its limits).
# 2. Count service per area on a normal weekday morning peak (7 to 9am): bus and train departures.
# 3. Divide by population (OpenDOSM, 2026) to get **departures per 1,000 residents**. This puts big
#    and small areas on the same scale.

# %%
import sys
from pathlib import Path

ROOT = Path.cwd() if (Path.cwd() / "src").exists() else Path.cwd().parent
sys.path.insert(0, str(ROOT))

import pandas as pd
import plotly.express as px
from src.transit import config, gtfs
from src.transit.coverage import area_population, assign_area, label_bus_stops

def latest(cat):
    return sorted(config.RAW.glob(f"gtfs_{cat}_*.zip"))[-1]

PEAK = (7 * 3600, 9 * 3600)

# %% [markdown]
# ## 1. Population per area

# %%
pop = area_population(pd.read_parquet(config.RAW / "population_district.parquet"))
pop.sort_values("population", ascending=False)

# %% [markdown]
# ## 2. Put every stop in an area, and count peak departures at it

# %%
bus_stops, rail_stops = [], None
for cat in config.GTFS_CATEGORIES:
    g = gtfs.read_gtfs(latest(cat))
    deps = gtfs.all_departures(g, gtfs.weekday_service_ids(g))
    peak = deps[(deps.dep_s >= PEAK[0]) & (deps.dep_s < PEAK[1])]
    per_stop = peak.groupby("stop_id").size().rename("peak_departures").reset_index()
    if cat == "rapid-rail-kl":
        rail_stops = g["stops"].merge(per_stop, on="stop_id", how="left").fillna({"peak_departures": 0})
    else:
        s = label_bus_stops(g["stops"]).merge(per_stop, on="stop_id", how="left").fillna({"peak_departures": 0})
        bus_stops.append(s.assign(feed=cat))
bus_stops = pd.concat(bus_stops, ignore_index=True)
print(bus_stops.area_from.value_counts())

# KTM Komuter (a separate feed). Keep only the two Klang Valley Komuter lines.
k = gtfs.read_gtfs(latest("ktmb"))
k["trips"] = k["trips"][k["trips"].route_id.isin(config.KTM_KOMUTER_KV_ROUTES)]
kdeps = gtfs.all_departures(k, gtfs.weekday_service_ids(k))
kpeak = kdeps[(kdeps.dep_s >= PEAK[0]) & (kdeps.dep_s < PEAK[1])].groupby("stop_id").size().rename("peak_departures")
ktm_stops = k["stops"][k["stops"].stop_id.isin(kdeps.stop_id)].merge(kpeak, on="stop_id", how="left").fillna({"peak_departures": 0})
rail_stops = pd.concat([rail_stops.assign(operator="Rapid Rail"), ktm_stops.assign(operator="KTM Komuter")], ignore_index=True)

# Rail stations take the area of the nearest bus stop. Stations more than 5 km from any Rapid KL
# stop (e.g. Seremban, Tanjung Malim) are outside our areas and are dropped.
rail_stops[["stop_lat", "stop_lon"]] = rail_stops[["stop_lat", "stop_lon"]].astype(float)
rail_stops["area"] = assign_area(rail_stops, bus_stops, max_km=5)
print("dropped (outside Klang Valley):", rail_stops[rail_stops.area.isna()].stop_name.tolist())
rail_stops = rail_stops.dropna(subset=["area"])
rail_stops.groupby(["area", "operator"]).size().unstack(fill_value=0)

# %% [markdown]
# ## 3. Service per 1,000 residents
# - `bus_stops` and `rail_stations`: how many places you can board.
# - `bus_peak_per_1k`: bus departures from stops in the area, 7–9am, per 1,000 residents.
#   (One bus passing 30 stops counts 30 times: it measures how much service people can reach.)
# - `rail_peak_per_1k`: the same for trains stopping at stations.

# %%
bus = bus_stops.groupby("area").agg(bus_stops=("stop_id", "count"), bus_peak=("peak_departures", "sum"))
rail = rail_stops.groupby("area").agg(rail_stations=("stop_id", "count"), rail_peak=("peak_departures", "sum"))
cov = pop.set_index("area").join(bus).join(rail).fillna(0)
cov["residents_per_bus_stop"] = (cov.population / cov.bus_stops).round(0)
cov["bus_peak_per_1k"] = (1000 * cov.bus_peak / cov.population).round(1)
cov["rail_peak_per_1k"] = (1000 * cov.rail_peak / cov.population).round(1)
cov["total_peak_per_1k"] = cov.bus_peak_per_1k + cov.rail_peak_per_1k
cov = cov.sort_values("total_peak_per_1k")
cov

# %%
fig = px.scatter(cov.reset_index(), x="population", y="total_peak_per_1k", size="population", text="area",
                 color="rail_stations", log_x=True,
                 labels={"total_peak_per_1k": "Peak departures per 1,000 residents (bus + rail)",
                         "population": "Residents (2026, log scale)", "rail_stations": "Rail stations"},
                 title="Many people, little service? Areas low on this chart are under-served")
fig.update_traces(textposition="top center")

# %% [markdown]
# ## 4. Where are the stops? (map)
# Each dot is a bus stop, coloured by area. Rail stations are black. Gaps between dots inside
# built-up areas are places with no Rapid KL bus at all.

# %%
m = pd.concat([bus_stops[["stop_name", "stop_lat", "stop_lon", "area", "peak_departures"]],
               rail_stops[["stop_name", "stop_lat", "stop_lon", "peak_departures"]].assign(area="Rail station")])
px.scatter_map(m, lat="stop_lat", lon="stop_lon", color="area", hover_name="stop_name",
               hover_data={"peak_departures": True, "stop_lat": False, "stop_lon": False},
               zoom=9, height=700, title="Rapid KL stops by area")

# %% [markdown]
# ## 5. Write down what surprised you
# Which area would you add buses to first, and why? Put it in docs/FINDINGS_04.md.
