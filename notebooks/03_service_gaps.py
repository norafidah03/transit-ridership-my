# %% [markdown]
# # 03 · Service gaps and crowding (Q3, Q4)
# Questions:
# - **Q3**: which rail lines carry the most riders for the service they run? (a crowding proxy)
# - **Q4**: which bus routes and stops have the longest waits in the morning peak (7 to 9am)?
#
# Data: Prasarana GTFS timetables (a snapshot of the *current* timetable, see the file date) and
# daily ridership. Everything here is for **a normal weekday**.
#
# How GTFS works, in one paragraph: `routes` = lines, `trips` = one run of a vehicle,
# `stop_times` = when each trip reaches each stop, `calendar` = which days a trip runs, and
# `frequencies` (Rapid KL uses this) = "repeat this trip every N seconds between A and B".

# %%
import sys
from pathlib import Path

ROOT = Path.cwd() if (Path.cwd() / "src").exists() else Path.cwd().parent
sys.path.insert(0, str(ROOT))

import pandas as pd
import plotly.express as px
from src.transit import config, gtfs
from src.transit.clean import flag_outliers, to_long
from src.transit.patterns import add_calendar, holiday_calendar

def latest(cat):  # newest downloaded snapshot of a feed
    return sorted(config.RAW.glob(f"gtfs_{cat}_*.zip"))[-1]

feeds = {}
for cat in config.GTFS_CATEGORIES:
    g = gtfs.read_gtfs(latest(cat))
    sids = gtfs.weekday_service_ids(g)
    feeds[cat] = dict(g=g, deps=gtfs.all_departures(g, sids))
    print(f"{cat}: weekday service_ids {sids}, {feeds[cat]['deps'].trip_id.nunique():,} trips per weekday")

# %% [markdown]
# ## 1. Rail: how often do trains come?

# %%
rail = feeds["rapid-rail-kl"]
rail_peak = gtfs.route_peak_service(rail["deps"], rail["g"]["routes"])
rail_peak.groupby(["route_short_name", "route_long_name"])[["peak_trips", "avg_headway_min"]].first()

# %% [markdown]
# ## 2. Q3 · Crowding proxy: riders per train
# Weekday riders (last 12 months, holidays removed) divided by
# - scheduled trains per day, and
# - **train-hours** per day (trains x end-to-end run time). This is fairer: one trip on a long line
#   carries many groups of people as they get on and off along the way.
#
# This is a *proxy*: the timetable says what is planned, not how full each train actually is, and
# trains on different lines have different sizes.

# %%
wide = pd.read_parquet(config.RAW / "ridership_headline.parquet")
long = add_calendar(flag_outliers(to_long(wide)), holiday_calendar())
recent = long[(long.date > long.date.max() - pd.Timedelta(days=365)) & ~long.is_weekend & ~long.is_holiday]
weekday_riders = recent.groupby(["series", "line"])["riders"].mean().reset_index()

supply = gtfs.line_supply(rail["deps"])
supply["series"] = supply.route_id.map(config.RAIL_ROUTE_TO_SERIES)
by_series = (supply.dropna(subset=["series"]).groupby("series")
             .agg(daily_trips=("daily_trips", "sum"), train_hours=("vehicle_hours", "sum")).reset_index())
crowd = by_series.merge(weekday_riders, on="series")
crowd["riders_per_trip"] = (crowd.riders / crowd.daily_trips).round(0)
crowd["riders_per_train_hour"] = (crowd.riders / crowd.train_hours).round(0)
crowd = crowd.sort_values("riders_per_train_hour", ascending=False)
crowd[["line", "riders", "daily_trips", "train_hours", "riders_per_trip", "riders_per_train_hour"]].round(0)

# %%
px.bar(crowd, x="riders_per_train_hour", y="line", orientation="h",
       title="Weekday riders per scheduled train-hour (higher = more stretched)").update_yaxes(categoryorder="total ascending")

# %% [markdown]
# ## 3. Q4 · Bus routes with the longest morning-peak waits
# avg_headway_min = 120 minutes / number of buses starting between 7 and 9am, per direction.

# %%
bus_routes = pd.concat([
    gtfs.route_peak_service(feeds[c]["deps"], feeds[c]["g"]["routes"]).assign(feed=c)
    for c in ["rapid-bus-kl", "rapid-bus-mrtfeeder"]
])
print(f"{len(bus_routes)} route-directions; {(bus_routes.avg_headway_min > 20).mean():.0%} wait more than 20 min at peak")
bus_routes.sort_values("avg_headway_min", ascending=False).head(20)

# %%
px.histogram(bus_routes, x="avg_headway_min", color="feed", nbins=24,
             title="Morning-peak wait between buses, per route and direction")

# %% [markdown]
# ## 4. Q4 · Bus stops: how many buses per hour in the morning peak?
# Counts every route that stops there. Fewer than 2 buses an hour means an average wait over 15 min
# (if you arrive at a random time you wait half the gap on average).

# %%
stops = pd.concat([
    gtfs.stop_peak_service(feeds[c]["deps"], feeds[c]["g"]["stops"]).assign(feed=c)
    for c in ["rapid-bus-kl", "rapid-bus-mrtfeeder"]
])
stops["band"] = pd.cut(stops.per_hour, [-0.1, 0, 2, 4, 8, 1000],
                       labels=["none at peak", "under 2/h", "2–4/h", "4–8/h", "8+/h"])
stops.band.value_counts().sort_index()

# %%
px.scatter_map(stops, lat="stop_lat", lon="stop_lon", color="band", hover_name="stop_name",
               hover_data={"per_hour": True, "routes": True, "stop_lat": False, "stop_lon": False},
               category_orders={"band": ["none at peak", "under 2/h", "2–4/h", "4–8/h", "8+/h"]},
               color_discrete_sequence=["#7f0000", "#d7301f", "#fc8d59", "#91bfdb", "#4575b4"],
               zoom=10, height=700, title="Buses per hour at each stop, weekday 7–9am")

# %% [markdown]
# ## 5. Your own commute
# Change these to your stop names and see your stop's numbers.

# %%
MY_STOPS = ["KL SENTRAL"]
stops[stops.stop_name.str.contains("|".join(MY_STOPS), case=False)].sort_values("per_hour", ascending=False).head(10)
