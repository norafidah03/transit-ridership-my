"""Klang Valley public transport dashboard.

Run locally:   streamlit run app/streamlit_app.py
Data:          app/data/*.parquet, built by `python -m src.transit.build` (committed to git, so the
               deployed app on Streamlit Community Cloud works without downloading anything).
"""
import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

DATA = Path(__file__).parent / "data"

# Colours: one fixed colour per line, so a line keeps its colour on every chart and filter.
SLOTS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
LINE_COLORS = dict(zip(["LRT Kelana Jaya", "MRT Kajang", "LRT Ampang/Sri Petaling", "Rapid Bus KL",
                        "MRT Putrajaya", "KTM Komuter", "KL Monorail", "LRT Shah Alam"], SLOTS))
OTHER = "#898781"
DIVERGING = [[0, "#d03b3b"], [0.5, "#f0efec"], [1, "#2a78d6"]]  # below normal = red, above = blue
KV_LINES = list(LINE_COLORS)

st.set_page_config(page_title="Klang Valley Transit", page_icon="🚆", layout="wide")


@st.cache_data
def load(name):
    return pd.read_parquet(DATA / f"{name}.parquet")


def color_map(lines):
    return {l: LINE_COLORS.get(l, OTHER) for l in lines}


def style(fig, height=420):
    fig.update_layout(template="plotly_white", height=height, margin=dict(l=10, r=10, t=50, b=10),
                      legend_title_text="", hovermode="closest", font_family="system-ui, sans-serif")
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#e1e0d9")
    return fig


meta = json.loads((DATA / "meta.json").read_text())
ridership = load("ridership")

st.title("Klang Valley public transport")
st.caption(f"Ridership {meta['ridership_from']} to {meta['ridership_to']} (data.gov.my) · "
           f"Timetables (GTFS) from {meta['gtfs_snapshot']} · Population {meta['population_year']} (OpenDOSM)")

tabs = st.tabs(["Overview", "Trends", "Weekly & holidays", "Crowding", "Bus service gaps", "Coverage"])

# ------------------------------------------------------------------------------------------- Overview
with tabs[0]:
    kv = ridership[ridership.line.isin(KV_LINES)]
    daily = kv.groupby("date")["riders"].sum()
    last_year = daily[daily.index > daily.index.max() - pd.Timedelta(days=365)]
    four = ["LRT Kelana Jaya", "LRT Ampang/Sri Petaling", "MRT Kajang", "KL Monorail"]
    f = ridership[ridership.line.isin(four)].groupby("date")["riders"].sum()
    rec = f[f.index.year == f.index.year.max() - 1].mean() / f[f.index.year == 2019].mean()
    cov = load("coverage").sort_values("total_peak_per_1k")
    stops = load("bus_stops")

    c = st.columns(4)
    c[0].metric("Klang Valley riders per day", f"{last_year.mean() / 1e6:.2f}M", help="Rail + Rapid Bus KL + KTM Komuter, last 12 months")
    c[1].metric(f"Original 4 lines vs 2019", f"{rec:.0%}", help=f"Average daily riders in {f.index.year.max() - 1} vs 2019")
    c[2].metric("Bus stops with 2 or fewer buses/hour at peak", f"{(stops.per_hour <= 2).mean():.0%}", help="Weekday 7–9am")
    worst = cov[cov.population > 1e6].iloc[0]
    c[3].metric("Least served big area", worst.area,
                help=f"{worst.residents_per_bus_stop:,.0f} residents per Rapid KL bus stop (areas over 1 million people)")

    st.markdown("""
**What the data says**
- Rail ridership is **above pre-COVID**, but **LRT Kelana Jaya** is the one original line still below 2019.
- **MRT Kajang** is the most stretched line: as many riders as Kelana Jaya with fewer trains.
- A **weekday public holiday roughly halves** commuter ridership; Hari Raya hits hardest.
- The typical bus route runs **every 30 minutes** at peak, and about half of all stops get 2 or fewer buses an hour (one every 30 min or worse).
- **Klang** (1.2 million people) gets about 1/12 of Kuala Lumpur's peak service per resident.
""")
    st.info("Built by a daily Rapid KL commuter. Code and method: see the GitHub repo README.", icon="🚆")

# --------------------------------------------------------------------------------------------- Trends
with tabs[1]:
    lines = sorted(ridership.line.unique())
    pick = st.multiselect("Lines", lines, default=KV_LINES[:6], key="trend_lines")
    view = ridership[ridership.line.isin(pick)].copy()
    view["riders_28d"] = view.groupby("line")["riders"].transform(lambda s: s.rolling(28, min_periods=14).mean())
    st.plotly_chart(style(px.line(view, x="date", y="riders_28d", color="line", color_discrete_map=color_map(pick),
                                  labels={"riders_28d": "Daily riders (28-day average)", "date": ""},
                                  title="Daily riders, 28-day average")), width="stretch")

    rec = load("recovery")
    rec = rec[rec.line.isin(pick) & (rec.year > 2019)].dropna(subset=["recovery_pct"])
    rec["month"] = pd.to_datetime(dict(year=rec.year, month=rec.month, day=1))
    fig = px.line(rec, x="month", y="recovery_pct", color="line", color_discrete_map=color_map(pick),
                  labels={"recovery_pct": "% of same month in 2019", "month": ""},
                  title="Recovery: riders as % of the same month in 2019 (only lines open in 2019)")
    fig.add_hline(y=100, line_dash="dot", line_color="#898781")
    st.plotly_chart(style(fig), width="stretch")

# ----------------------------------------------------------------------------------- Weekly & holidays
with tabs[2]:
    order = [l for l in KV_LINES + ["KTM ETS", "KTM Intercity"]]
    dow = load("dow_profile").set_index("line").reindex(order).dropna(how="all")
    fig = px.imshow(dow, text_auto=".0f", color_continuous_scale=DIVERGING, zmin=40, zmax=160, aspect="auto",
                    labels=dict(color="% of weekday avg", x="", y=""),
                    title="Riders by day of week, % of the line's weekday average (last 12 months)")
    st.plotly_chart(style(fig, 460), width="stretch")
    st.caption("Below ~65% on weekends = office commuter line. Above 100% = leisure or long-distance line.")

    eff = load("holiday_effect").set_index("group")
    eff = eff[[c for c in order if c in eff.columns]]
    fig = px.imshow(eff, text_auto=".0f", color_continuous_scale=DIVERGING, zmin=0, zmax=200, aspect="auto",
                    labels=dict(color="% of normal", x="", y=""),
                    title="Weekday public holidays: riders as % of a normal day (2023 onwards)")
    st.plotly_chart(style(fig, 460), width="stretch")

    fc = load("festival_curves")
    fest = st.radio("Festival", fc.festival.unique(), horizontal=True)
    show = ["LRT Kelana Jaya", "MRT Kajang", "Rapid Bus KL", "KTM ETS", "KTM Intercity"]
    cm = color_map(show) | {"KTM ETS": "#6250d6", "KTM Intercity": "#e34948"}
    fig = px.line(fc[(fc.festival == fest) & fc.line.isin(show)], x="day", y="pct_of_normal", color="line",
                  markers=True, color_discrete_map=cm,
                  labels={"day": "Days from the festival (0 = the day itself)", "pct_of_normal": "% of a normal day"},
                  title=f"{fest}: the balik kampung curve")
    fig.add_hline(y=100, line_dash="dot", line_color="#898781")
    st.plotly_chart(style(fig), width="stretch")

# ------------------------------------------------------------------------------------------- Crowding
with tabs[3]:
    crowd = load("crowding").sort_values("riders_per_train_hour")
    fig = px.bar(crowd, x="riders_per_train_hour", y="line", orientation="h", color="line",
                 color_discrete_map=color_map(crowd.line), text_auto=".0f",
                 labels={"riders_per_train_hour": "Weekday riders per scheduled train-hour", "line": ""},
                 title="Which rail lines are most stretched? (higher = more riders per train running)")
    fig.update_layout(showlegend=False)
    st.plotly_chart(style(fig, 380), width="stretch")
    st.caption("A proxy, not measured crowding: planned trains from the timetable, and trains differ in size between lines. "
               "Train-hours = trains per day × end-to-end run time.")
    rp = load("rail_peak").groupby("route_long_name", as_index=False)["avg_headway_min"].min()
    st.dataframe(crowd.assign(riders=crowd.riders.round(-2)).rename(columns={
        "line": "Line", "riders": "Weekday riders", "daily_trips": "Trains/day",
        "riders_per_trip": "Riders per train", "riders_per_train_hour": "Riders per train-hour"})
        [["Line", "Weekday riders", "Trains/day", "Riders per train", "Riders per train-hour"]].round(0),
        hide_index=True, width="stretch")
    st.markdown("**Peak frequency (weekday 7–9am)**: " + " · ".join(
        f"{r.route_long_name.replace(' Line', '')} every {r.avg_headway_min:.0f} min" for r in rp.sort_values("avg_headway_min").itertuples()))

# ----------------------------------------------------------------------------------- Bus service gaps
with tabs[4]:
    routes = load("bus_routes")
    routes["Bus type"] = routes.feed.map({"rapid-bus-kl": "City bus", "rapid-bus-mrtfeeder": "MRT feeder"})
    c = st.columns(3)
    c[0].metric("Typical wait between buses at peak", f"{routes.avg_headway_min.median():.0f} min")
    c[1].metric("Routes running less often than every 20 min", f"{(routes.avg_headway_min > 20).mean():.0%}")
    c[2].metric("Routes with 1–2 buses in 7–9am", f"{(routes.peak_trips <= 2).sum()}")

    st.subheader("Find your stop")
    q = st.text_input("Type part of a stop name", "KL SENTRAL")
    stops = load("bus_stops")
    if q:
        hit = stops[stops.stop_name.str.contains(q, case=False, regex=False)].sort_values("per_hour", ascending=False)
        st.dataframe(hit[["stop_name", "area", "per_hour", "routes"]].rename(columns={
            "stop_name": "Stop", "area": "Area", "per_hour": "Buses per hour (7–9am)", "routes": "Routes"}).head(20),
            hide_index=True, width="stretch")

    bands = ["none at peak", "up to 2/h", "2–4/h", "4–8/h", "8+/h"]
    stops["band"] = pd.cut(stops.per_hour, [-0.1, 0, 2, 4, 8, 1000], labels=bands)
    fig = px.scatter_map(stops.sort_values("per_hour"), lat="stop_lat", lon="stop_lon", color="band",
                         hover_name="stop_name", hover_data={"per_hour": ":.1f", "routes": True, "stop_lat": False, "stop_lon": False, "band": False},
                         category_orders={"band": bands},
                         color_discrete_sequence=["#d03b3b", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"],
                         zoom=9.5, center={"lat": 3.1, "lon": 101.6}, height=620,
                         title="Buses per hour at each stop, weekday 7–9am")
    fig.update_traces(marker_size=6)
    st.plotly_chart(style(fig, 620), width="stretch")

    st.subheader("Routes with the longest peak waits")
    worst = routes.sort_values(["avg_headway_min", "daily_trips"], ascending=[False, True]).head(25)
    st.dataframe(worst[["route_short_name", "route_long_name", "Bus type", "peak_trips", "avg_headway_min", "daily_trips"]]
                 .rename(columns={"route_short_name": "Route", "route_long_name": "Name", "peak_trips": "Buses 7–9am",
                                  "avg_headway_min": "Avg wait (min)", "daily_trips": "Buses per day"}),
                 hide_index=True, width="stretch")

# ------------------------------------------------------------------------------------------- Coverage
with tabs[5]:
    cov = load("coverage").sort_values("total_peak_per_1k")
    fig = px.bar(cov, x="total_peak_per_1k", y="area", orientation="h", text_auto=".1f",
                 labels={"total_peak_per_1k": "Bus + rail departures 7–9am per 1,000 residents", "area": ""},
                 title="Peak service per 1,000 residents, by area", color_discrete_sequence=["#2a78d6"])
    st.plotly_chart(style(fig, 400), width="stretch")
    st.dataframe(cov.assign(population=cov.population.round(-3)).rename(columns={
        "area": "Area", "population": "Residents", "bus_stops": "Bus stops", "rail_stations": "Rail stations",
        "residents_per_bus_stop": "Residents per bus stop", "total_peak_per_1k": "Peak departures per 1,000"})
        [["Area", "Residents", "Bus stops", "Rail stations", "Residents per bus stop", "Peak departures per 1,000"]]
        .round(1), hide_index=True, width="stretch")
    st.caption("Areas come from the council code at the start of each bus stop code; Gombak and Ulu Langat are combined. "
               "Only Rapid KL and KTM Komuter are counted: Smart Selangor and private buses have no timetable data here, "
               "so gaps in Klang, Kuala Langat and Sepang may be smaller in reality.")
