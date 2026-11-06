"""Transit Insight: Klang Valley Mobility Analytics (Streamlit dashboard).

Run locally:   streamlit run app/streamlit_app.py
Data:          app/data/*.parquet, built by `python -m src.transit.build` (committed to git, so the
               deployed app on Streamlit Community Cloud works without downloading anything).
Styling:       .streamlit/config.toml (theme, fonts) + app/style.css (layout details).

This file only presents results. All calculations live in src/transit/ and in the build step.
"""
import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

APP = Path(__file__).parent
DATA = APP / "data"

# Paste your repo link here to show a "Code on GitHub" link in the header.
GITHUB_URL = ""

# One colour per line, everywhere. Taken from each line's colour in the GTFS timetable feeds, adjusted so
# all eight stay distinguishable for colour-blind readers (checked with a palette validator).
LINE_COLORS = {
    "LRT Kelana Jaya": "#D50032",
    "MRT Kajang": "#047940",
    "LRT Ampang/Sri Petaling": "#E57200",
    "Rapid Bus KL": "#008C9E",
    "MRT Putrajaya": "#C99700",
    "KTM Komuter": "#3C5A9F",
    "KL Monorail": "#7A9E00",
    "LRT Shah Alam": "#B5179E",
}
KV_LINES = list(LINE_COLORS)
NAVY, SLATE, RAIL, PLATFORM, ALERT = "#13233F", "#52627A", "#D7DDE5", "#F2F4F7", "#C8102E"
OTHER = "#8A96A8"
DIVERGING = [[0, ALERT], [0.5, PLATFORM], [1, "#1F5FAF"]]  # below normal = red, above = blue

st.set_page_config(page_title="Transit Insight: Klang Valley Mobility Analytics", page_icon="🚆", layout="wide")
st.html(f"<style>{(APP / 'style.css').read_text()}</style>")


@st.cache_data
def load(name):
    return pd.read_parquet(DATA / f"{name}.parquet")


def color_map(lines):
    return {l: LINE_COLORS.get(l, OTHER) for l in lines}


def style(fig, height=420):
    fig.update_layout(template="plotly_white", height=height, margin=dict(l=10, r=10, t=64, b=10),
                      legend_title_text="", hovermode="closest", paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
                      font=dict(family="Overpass, system-ui, sans-serif", color=NAVY, size=13),
                      title=dict(font=dict(size=17, color=NAVY), x=0, xanchor="left"),
                      hoverlabel=dict(font_family="Overpass, system-ui, sans-serif"))
    fig.update_xaxes(showgrid=False, linecolor=RAIL, tickfont_color=SLATE, title_font_color=SLATE)
    fig.update_yaxes(gridcolor="#E9EDF2", linecolor=RAIL, tickfont_color=SLATE, title_font_color=SLATE)
    return fig


def chart(fig, height=420):
    # The chart title is set as page text so it wraps on phones and matches the page typography.
    title = fig.layout.title.text
    if title:
        html(f'<h3 class="ti-chart-title">{title}</h3>')
    style(fig, height)
    fig.update_layout(title=None, margin=dict(l=10, r=10, t=10, b=10),
                      legend=dict(orientation="h", yanchor="top", y=-0.22, x=0, xanchor="left"))
    st.plotly_chart(fig, width="stretch", config={"displaylogo": False})


def html(s):
    st.html(s)


def here(active):
    stops_ = ["Recovery", "Peak demand vs service", "Underserved areas"]
    parts = []
    for i, s in enumerate(stops_):
        parts.append(f'<span class="{"on" if s == active else ""}"><i></i>{s}</span>')
        if i < len(stops_) - 1:
            parts.append("<b></b>")
    html(f'<div class="ti-here" aria-label="Question {stops_.index(active) + 1} of 3: {active}">{"".join(parts)}</div>')


def intro(question, answer):
    html(f'<p class="ti-question">{question}</p><p class="ti-answer">{answer}</p>')


def means(text):
    html(f'<div class="ti-means"><h4>What this means</h4><p>{text}</p></div>')


def kpis(items):
    tiles = "".join(f'<div class="ti-kpi{" alert" if a else ""}"><div class="v">{v}</div><div class="l">{l}</div>'
                    f'<div class="c">{c}</div></div>' for v, l, c, a in items)
    html(f'<div class="ti-kpis">{tiles}</div>')


def month(d):
    return pd.Timestamp(d).strftime("%b %Y")


# ----------------------------------------------------------------------------------------- data + KPIs
# The calculations below are the same as in the previous version of the dashboard.
meta = json.loads((DATA / "meta.json").read_text())
ridership = load("ridership")
kv = ridership[ridership.line.isin(KV_LINES)]
daily = kv.groupby("date")["riders"].sum()
last_year = daily[daily.index > daily.index.max() - pd.Timedelta(days=365)]
four = ["LRT Kelana Jaya", "LRT Ampang/Sri Petaling", "MRT Kajang", "KL Monorail"]
f4 = ridership[ridership.line.isin(four)].groupby("date")["riders"].sum()
rec_year = f4.index.year.max() - 1
rec_ratio = f4[f4.index.year == rec_year].mean() / f4[f4.index.year == 2019].mean()
crowd = load("crowding").sort_values("riders_per_train_hour")
top_crowd = crowd.iloc[-1]
kj_crowd = crowd[crowd.line == "LRT Kelana Jaya"].iloc[0]
cov = load("coverage").sort_values("total_peak_per_1k")
worst_big = cov[cov.population > 1e6].iloc[0]
kl = cov[cov.area == "Kuala Lumpur"].iloc[0]
service_ratio = kl.total_peak_per_1k / worst_big.total_peak_per_1k
stops = load("bus_stops")
routes = load("bus_routes")
routes["Bus type"] = routes.feed.map({"rapid-bus-kl": "City bus", "rapid-bus-mrtfeeder": "MRT feeder"})
median_wait = routes.avg_headway_min.median()
share_over_20 = (routes.avg_headway_min > 20).mean()
n_thin_routes = (routes.peak_trips <= 2).sum()
share_thin_stops = (stops.per_hour <= 2).mean()

# ------------------------------------------------------------------------------------------------ header
gh = f' · <a href="{GITHUB_URL}">Code on GitHub</a>' if GITHUB_URL else ""
html(f"""
<header class="ti-header">
  <h1 class="ti-title">Transit Insight<span>Klang Valley Mobility Analytics</span></h1>
  <p class="ti-tagline">Understanding ridership recovery, service demand and public transport accessibility.</p>
  <p class="ti-meta">Ridership to {month(meta['ridership_to'])} from data.gov.my, timetables from {month(meta['gtfs_snapshot'])},
  population {meta['population_year']} from OpenDOSM{gh}</p>
</header>""")

tabs = st.tabs(["Overview", "Recovery", "Peak demand vs service", "Underserved areas",
                "Findings & recommendations", "Methodology & data"])

# ---------------------------------------------------------------------------------------------- Overview
with tabs[0]:
    html(f"""
<div class="ti-prose">
  <p>About {last_year.mean() / 1e6:.2f} million trips are made on Klang Valley rail, Rapid KL buses and KTM Komuter every day.
  This project uses open government data to answer three questions a transport planner would ask:
  has ridership come back since COVID, is service matched to when people travel, and which areas are left with too little?</p>
</div>
<nav class="ti-route" aria-label="The three questions">
  <ol>
    <li><span class="ti-dot"></span>
      <div class="ti-stop">Recovery</div>
      <div class="ti-num">{rec_ratio:.0%}</div>
      <div class="ti-num-label">of 2019 ridership on the 4 original lines ({rec_year})</div>
      <div class="ti-take">Rail is back above pre-COVID levels, but LRT Kelana Jaya still lags.</div>
      <div class="ti-go">Details in the Recovery tab</div></li>
    <li><span class="ti-dot"></span>
      <div class="ti-stop">Peak demand vs service</div>
      <div class="ti-num">{top_crowd.riders_per_train_hour:,.0f}</div>
      <div class="ti-num-label">weekday riders per train-hour on {top_crowd.line}, the highest</div>
      <div class="ti-take">{top_crowd.line} is the most stretched line, and the typical bus comes every {median_wait:.0f} minutes at peak.</div>
      <div class="ti-go">Details in the Peak demand vs service tab</div></li>
    <li><span class="ti-dot"></span>
      <div class="ti-stop">Underserved areas</div>
      <div class="ti-num">1 per {worst_big.residents_per_bus_stop:,.0f}</div>
      <div class="ti-num-label">residents per Rapid KL bus stop in {worst_big.area}, vs 1 per {kl.residents_per_bus_stop:,.0f} in Kuala Lumpur</div>
      <div class="ti-take">{worst_big.area} gets about 1/{service_ratio:.0f} of Kuala Lumpur's peak service per resident.</div>
      <div class="ti-go">Details in the Underserved areas tab</div></li>
  </ol>
</nav>""")

    trend = kv.copy()
    trend["riders_28d"] = trend.groupby("line")["riders"].transform(lambda s: s.rolling(28, min_periods=14).mean())
    chart(px.line(trend, x="date", y="riders_28d", color="line", color_discrete_map=color_map(KV_LINES),
                  category_orders={"line": KV_LINES},
                  labels={"riders_28d": "Daily riders (28-day average)", "date": ""},
                  title="Ridership collapsed in 2020-21 and has climbed back on every line"), 460)

    html(f"""<div class="ti-means"><h4>Three things to take away</h4><p>
    Demand has returned, so the question now is capacity, not recovery. The pressure points are {top_crowd.line} at peak
    and bus frequency everywhere. The biggest coverage gap is {worst_big.area}, an area of {worst_big.population / 1e6:.1f} million people.
    The Findings &amp; recommendations tab turns each of these into an action.</p></div>""")

# ---------------------------------------------------------------------------------------------- Recovery
with tabs[1]:
    here("Recovery")
    intro("Has Klang Valley public transport ridership recovered from COVID?",
          f"Yes, on rail. The four lines open since 2019 averaged {rec_ratio:.0%} of their 2019 ridership in {rec_year}. "
          "LRT Kelana Jaya is the exception: it is the only original line still below 2019.")

    lines = sorted(ridership.line.unique())
    pick = st.multiselect("Choose lines to compare", lines, key="trend_lines",
                          default=["LRT Kelana Jaya", "MRT Kajang", "LRT Ampang/Sri Petaling", "KL Monorail",
                                   "Rapid Bus KL", "MRT Putrajaya"])
    view = ridership[ridership.line.isin(pick)].copy()
    view["riders_28d"] = view.groupby("line")["riders"].transform(lambda s: s.rolling(28, min_periods=14).mean())
    chart(px.line(view, x="date", y="riders_28d", color="line", color_discrete_map=color_map(pick),
                  category_orders={"line": KV_LINES + sorted(set(lines) - set(KV_LINES))}, labels={"riders_28d": "Daily riders (28-day average)", "date": ""},
                  title="Daily riders by line, 28-day average"))

    rec = load("recovery")
    rec = rec[rec.line.isin(pick) & (rec.year > 2019)].dropna(subset=["recovery_pct"])
    rec["month"] = pd.to_datetime(dict(year=rec.year, month=rec.month, day=1))
    fig = px.line(rec, x="month", y="recovery_pct", color="line", color_discrete_map=color_map(pick),
                  category_orders={"line": KV_LINES},
                  labels={"recovery_pct": "% of the same month in 2019", "month": ""},
                  title="MRT Kajang and the Monorail are well above 2019; Kelana Jaya hovers just below")
    fig.add_hline(y=100, line_dash="dot", line_color=SLATE, annotation_text="2019 level",
                  annotation_position="bottom right", annotation_font_color=SLATE)
    chart(fig)
    html('<p class="ti-note">Only lines open in 2019 have a recovery figure. Rapid Bus KL data starts in 2022, '
         'MRT Putrajaya opened in 2022, KTM Komuter data starts in 2023 and LRT Shah Alam opened in 2026.</p>')
    means("Ridership is no longer the problem to solve: the network carries more people than before COVID. "
          "Kelana Jaya's flat trend is worth investigating, since it may point to service reliability or to riders "
          "shifting to the MRT Putrajaya line, which serves some of the same areas.")

# -------------------------------------------------------------------------------- Peak demand vs service
with tabs[2]:
    here("Peak demand vs service")
    intro("When are lines busiest, and is the service sized to match?",
          f"Demand follows the working week and the festival calendar very predictably. Measured against the trains it runs, "
          f"{top_crowd.line} carries the most riders, while buses run too rarely for a commuter network.")

    html('<p class="ti-part">When people travel</p>')
    order = KV_LINES + ["KTM ETS", "KTM Intercity"]
    dow = load("dow_profile").set_index("line").reindex(order).dropna(how="all")
    chart(px.imshow(dow, text_auto=".0f", color_continuous_scale=DIVERGING, zmin=40, zmax=160, aspect="auto",
                    labels=dict(color="% of weekday avg", x="", y=""),
                    title="Commuter lines halve at weekends; Shah Alam, ETS and Intercity get busier"), 470)
    html('<p class="ti-note">Each cell is that day\'s riders as a % of the line\'s Monday to Friday average, last 12 months, '
         'holidays removed. Below about 65% at weekends marks an office commuter line.</p>')

    eff = load("holiday_effect").set_index("group")
    eff = eff[[c for c in order if c in eff.columns]]
    chart(px.imshow(eff, text_auto=".0f", color_continuous_scale=DIVERGING, zmin=0, zmax=200, aspect="auto",
                    labels=dict(color="% of normal", x="", y=""),
                    title="A weekday public holiday roughly halves commuter ridership and doubles Intercity"), 470)
    html('<p class="ti-note">Riders on public holidays that fall Monday to Friday, as a % of a normal day for the same line '
         'and weekday, 2023 onwards. Blank cells: LRT Shah Alam has not yet had these holidays on a weekday.</p>')

    fc = load("festival_curves")
    fest = st.radio("Festival", fc.festival.unique(), horizontal=True)
    show = ["LRT Kelana Jaya", "MRT Kajang", "Rapid Bus KL", "KTM ETS", "KTM Intercity"]
    cm = color_map(show) | {"KTM ETS": "#6250D6", "KTM Intercity": "#5C3D2E"}
    fig = px.line(fc[(fc.festival == fest) & fc.line.isin(show)], x="day", y="pct_of_normal", color="line",
                  markers=True, color_discrete_map=cm,
                  labels={"day": "Days from the festival (0 = the day itself)", "pct_of_normal": "% of a normal day"},
                  title=f"{fest}: city lines empty out while long-distance trains fill up")
    fig.add_hline(y=100, line_dash="dot", line_color=SLATE)
    chart(fig)

    html('<p class="ti-part">The service provided</p>')
    fig = px.bar(crowd, x="riders_per_train_hour", y="line", orientation="h", color="line",
                 color_discrete_map=color_map(crowd.line), text_auto=",.0f",
                 labels={"riders_per_train_hour": "Weekday riders per scheduled train-hour", "line": ""},
                 title=f"{top_crowd.line} carries the most riders for the trains it runs")
    fig.update_layout(showlegend=False)
    fig.update_traces(textfont_color=NAVY, textposition="outside", cliponaxis=False)
    chart(fig, 380)
    rp = load("rail_peak").groupby("route_long_name", as_index=False)["avg_headway_min"].min()
    kpis([(f"{r.avg_headway_min:.0f} min", r.route_long_name, "Time between trains, weekday 7 to 9am", False)
          for r in rp.sort_values("avg_headway_min").itertuples()])
    st.dataframe(crowd.assign(riders=crowd.riders.round(-2)).rename(columns={
        "line": "Line", "riders": "Weekday riders", "daily_trips": "Trains/day",
        "riders_per_trip": "Riders per train", "riders_per_train_hour": "Riders per train-hour"})
        [["Line", "Weekday riders", "Trains/day", "Riders per train", "Riders per train-hour"]].round(0)
        .sort_values("Riders per train-hour", ascending=False),
        hide_index=True, width="stretch",
        column_config={c: st.column_config.NumberColumn(format="localized") for c in
                       ["Weekday riders", "Trains/day", "Riders per train", "Riders per train-hour"]})
    html('<p class="ti-note">A proxy, not measured crowding: planned trains from the timetable, and train sizes differ '
         'between lines. Train-hours = trains per day × end-to-end run time.</p>')
    means(f"Peak capacity, not total ridership, is where service falls short. {top_crowd.line} runs a train every "
          "6 minutes at peak against 3 to 4 minutes on the LRT lines, yet carries as many people as Kelana Jaya. Because "
          "holiday and festival swings repeat every year, timetables can be planned from these curves in advance.")

# ------------------------------------------------------------------------------------- Underserved areas
with tabs[3]:
    here("Underserved areas")
    intro("Which areas have many people but little public transport?",
          f"{worst_big.area}. It is home to {worst_big.population / 1e6:.1f} million people but has one Rapid KL bus stop per "
          f"{worst_big.residents_per_bus_stop:,.0f} residents, against one per {kl.residents_per_bus_stop:,.0f} in Kuala Lumpur. "
          "Across the whole network, low bus frequency is the main weakness.")

    kpis([
        (f"{median_wait:.0f} min", "Typical wait between buses at peak", "Median across all bus routes, weekday 7 to 9am", True),
        (f"{share_over_20:.0%}", "Routes running less often than every 20 min", "City and MRT feeder buses", True),
        (f"{n_thin_routes}", "Routes with only 1 or 2 buses from 7 to 9am", "A wait of an hour or more", True),
        (f"{share_thin_stops:.0%}", "Bus stops with 2 or fewer buses an hour", "One bus every 30 minutes or worse", True),
    ])

    cov_plot = cov.copy()
    cov_plot["Level"] = (cov_plot.total_peak_per_1k < 1).map({True: "Under 1 per 1,000", False: "1 or more per 1,000"})
    fig = px.bar(cov_plot, x="total_peak_per_1k", y="area", orientation="h", text_auto=".1f", color="Level",
                 color_discrete_map={"Under 1 per 1,000": ALERT, "1 or more per 1,000": "#5E7491"},
                 labels={"total_peak_per_1k": "Bus + rail departures 7 to 9am per 1,000 residents", "area": ""},
                 title=f"{worst_big.area} gets far less peak service per resident than the rest of the urban core")
    fig.update_traces(textfont_color=NAVY, textposition="outside", cliponaxis=False)
    fig.update_yaxes(categoryorder="total ascending")
    chart(fig, 400)
    st.dataframe(cov.assign(population=cov.population.round(-3)).rename(columns={
        "area": "Area", "population": "Residents", "bus_stops": "Bus stops", "rail_stations": "Rail stations",
        "residents_per_bus_stop": "Residents per bus stop", "total_peak_per_1k": "Peak departures per 1,000"})
        .assign(**{"Residents per bus stop": lambda d: d["Residents per bus stop"].round(0)})
        [["Area", "Residents", "Bus stops", "Rail stations", "Residents per bus stop", "Peak departures per 1,000"]]
        .round(1), hide_index=True, width="stretch",
        column_config={c: st.column_config.NumberColumn(format="localized") for c in
                       ["Residents", "Bus stops", "Rail stations", "Residents per bus stop"]})
    html('<p class="ti-note">Red marks areas below 1 peak departure per 1,000 residents. Kuala Langat and Kuala Selangor are '
         'partly rural; Klang is the only one with over a million people.</p>')

    html('<p class="ti-part">Bus service stop by stop</p>')
    left, right = st.columns([3, 2], gap="large")
    bands = ["none at peak", "up to 2/h", "2–4/h", "4–8/h", "8+/h"]
    stops["band"] = pd.cut(stops.per_hour, [-0.1, 0, 2, 4, 8, 1000], labels=bands)
    with left:
        fig = px.scatter_map(stops.sort_values("per_hour"), lat="stop_lat", lon="stop_lon", color="band",
                             hover_name="stop_name",
                             hover_data={"per_hour": ":.1f", "routes": True, "stop_lat": False, "stop_lon": False, "band": False},
                             category_orders={"band": bands},
                             color_discrete_sequence=[ALERT, "#9DB7D9", "#5B8BC4", "#2C5F9E", NAVY],
                             zoom=9.3, center={"lat": 3.1, "lon": 101.6}, map_style="carto-positron",
                             labels={"band": "Buses per hour", "per_hour": "Buses per hour", "routes": "Routes"},
                             title="Frequent buses cluster in central KL")
        fig.update_traces(marker_size=6)
        chart(fig, 560)
    with right:
        st.markdown("**Find your stop**")
        q = st.text_input("Type part of a stop name", "KL SENTRAL")
        if q:
            hit = stops[stops.stop_name.str.contains(q, case=False, regex=False)].sort_values("per_hour", ascending=False)
            if hit.empty:
                st.caption("No stop matches that name. Try a shorter part of it, such as a road or station name.")
            else:
                st.dataframe(hit[["stop_name", "area", "per_hour", "routes"]].rename(columns={
                    "stop_name": "Stop", "area": "Area", "per_hour": "Buses/hour (7–9am)", "routes": "Routes"}).head(20),
                    hide_index=True, width="stretch")

    st.markdown("**Routes with the longest peak waits**")
    worst = routes.sort_values(["avg_headway_min", "daily_trips"], ascending=[False, True]).head(25)
    st.dataframe(worst[["route_short_name", "route_long_name", "Bus type", "peak_trips", "avg_headway_min", "daily_trips"]]
                 .rename(columns={"route_short_name": "Route", "route_long_name": "Name", "peak_trips": "Buses 7–9am",
                                  "avg_headway_min": "Avg wait (min)", "daily_trips": "Buses per day"}),
                 hide_index=True, width="stretch")
    html('<p class="ti-note">Areas come from the council code at the start of each bus stop code; Gombak and Ulu Langat '
         'are combined. Only Rapid KL and KTM Komuter are counted: Smart Selangor and private buses have no timetable '
         'data here, so gaps in Klang, Kuala Langat and Sepang may be smaller in reality.</p>')
    means(f"Rail coverage is reasonable in the urban core, but most people reach it by bus, and buses rarely come. "
          f"{worst_big.area} stands out as a large population with little Rapid KL service, which makes it the first place "
          "to check whether other operators fill the gap, and to expand if they do not.")

# ---------------------------------------------------------------------------- Findings & recommendations
FINDINGS = [
    ("Recovery", "Rail has passed pre-COVID ridership, but LRT Kelana Jaya has not",
     f"The original 4 lines were at {rec_ratio:.0%} of 2019 in {rec_year}. Kelana Jaya was at 96% in Jan to Aug 2026, with a flat trend since 2025.",
     "Investigate why Kelana Jaya lags (service disruptions, riders moving to MRT Putrajaya, changing work patterns in its corridor) before adding capacity elsewhere.",
     "Data that would confirm it: station-level ridership and disruption logs."),
    ("Peak demand vs service", f"{top_crowd.line} is the most stretched rail line",
     f"{top_crowd.riders_per_train_hour:,.0f} weekday riders per scheduled train-hour, against {kj_crowd.riders_per_train_hour:,.0f} on Kelana Jaya. Trains run every 6 minutes at peak against every 4.",
     f"Prioritise {top_crowd.line} for additional peak trains.",
     "Data that would confirm it: passenger load counts per train."),
    ("Peak demand vs service", "Demand swings predictably with the calendar",
     "Weekday holidays cut commuter ridership to about half while Intercity more than doubles. The Raya and CNY curves repeat each year.",
     "Plan holiday timetables from these curves: fewer commuter trains on holidays, and more ETS and Intercity capacity 3 to 4 days before and after major festivals.",
     "Data that would confirm it: ticket sales by day for ETS and Intercity."),
    ("Underserved areas", "Bus frequency, not rail, is the network's main weakness",
     f"The typical bus route runs every {median_wait:.0f} minutes at peak, {share_over_20:.0%} of routes run less often than every 20 minutes, and {share_thin_stops:.0%} of stops get 2 or fewer buses an hour.",
     f"Set a minimum peak frequency standard, for example every 15 to 20 minutes on trunk and feeder routes, starting with the {n_thin_routes} routes that run only 1 or 2 buses at peak.",
     "Data that would confirm it: bus boardings by route and stop."),
    ("Underserved areas", f"{worst_big.area} has far less Rapid KL service than its population suggests",
     f"{worst_big.population / 1e6:.2f} million residents and one bus stop per {worst_big.residents_per_bus_stop:,.0f} people, against one per {kl.residents_per_bus_stop:,.0f} in Kuala Lumpur. Peak service per resident is about 1/{service_ratio:.0f} of Kuala Lumpur's.",
     f"Treat {worst_big.area} as the first candidate for network expansion, after confirming how much Smart Selangor and private buses already cover.",
     "Data that would confirm it: timetables for Smart Selangor and private stage buses."),
]

with tabs[4]:
    intro("What should a transport planner do with these results?",
          "Five findings, each with the evidence behind it and a recommendation. They come from planned timetables and "
          "daily totals rather than passenger counts, so each one names the data that would confirm it.")
    cards = "".join(f"""
<article class="ti-finding">
  <div class="tag"><i></i>{obj}</div>
  <div>
    <h3>{title}</h3>
    <p class="ev">{ev}</p>
    <p class="rec"><strong>Recommendation.</strong> {rec_text}</p>
    <p class="check">{check}</p>
  </div>
</article>""" for obj, title, ev, rec_text, check in FINDINGS)
    html(f"<section>{cards}</section>")

# ------------------------------------------------------------------------------------ Methodology & data
with tabs[5]:
    html(f"""
<div class="ti-method">
  <p>Everything here is reproducible from open data with the code in the GitHub repository.</p>

  <h3>Data sources</h3>
  <ul>
    <li><a href="https://data.gov.my/data-catalogue/ridership_headline">Daily public transport ridership</a>, data.gov.my,
        {meta['ridership_from']} to {meta['ridership_to']}.</li>
    <li>GTFS timetables for Rapid Rail, Rapid Bus KL and MRT feeder buses (Prasarana) and KTM, via
        <a href="https://developer.data.gov.my/realtime-api/gtfs-static">api.data.gov.my</a>, snapshot of {meta['gtfs_snapshot']}.</li>
    <li>Population by district, <a href="https://open.dosm.gov.my/data-catalogue/population_district">OpenDOSM</a>,
        {meta['population_year']} estimates.</li>
    <li>Malaysian public holidays for Kuala Lumpur from the open-source <code>holidays</code> Python package.</li>
  </ul>

  <h3>Definitions</h3>
  <dl>
    <dt>Recovery</dt><dd>Average daily riders in a month as a % of the same calendar month in 2019.</dd>
    <dt>% of normal</dt><dd>A day's riders divided by the median of the same weekday for that line over the surrounding
        8 weeks. Mondays are compared with Mondays, never with Sundays.</dd>
    <dt>Peak</dt><dd>Weekday departures from 7:00 to 9:00 am.</dd>
    <dt>Wait between buses</dt><dd>120 minutes divided by the number of buses starting a route in the peak, per direction.</dd>
    <dt>Train-hour</dt><dd>One train running for one hour: trains per day × end-to-end run time. Riders per train-hour is a
        crowding proxy that is fair to long and short lines.</dd>
    <dt>Peak departures per 1,000 residents</dt><dd>Bus and train departures from stops in an area during the peak, divided by
        the area's population. A bus passing 30 stops counts 30 times, because it serves people at each one.</dd>
  </dl>

  <h3>Limitations</h3>
  <ul>
    <li>Ridership is a daily total per line: there is no hourly or station-level data, so peak crowding comes from timetables.</li>
    <li>Timetables show planned service, not what actually ran, and are a current snapshot compared with historical ridership.</li>
    <li>Only Rapid KL and KTM Komuter are counted. Smart Selangor, private buses, KLIA Ekspres and KLIA Transit are not.</li>
    <li>Areas are built from local council codes in bus stop IDs because district boundary maps were not available. Councils and
        districts do not match exactly, so Gombak and Ulu Langat are combined, and the Petaling and Klang split is approximate.</li>
    <li>City and feeder bus feeds use different stop IDs, so a stop served by both is counted twice.</li>
  </ul>

  <h3>How to reproduce</h3>
  <p><code>python -m src.transit.fetch</code> downloads the data, the notebooks in <code>notebooks/</code> walk through each
  analysis, <code>python -m src.transit.build</code> saves the tables this dashboard reads, and
  <code>streamlit run app/streamlit_app.py</code> starts it.</p>
</div>""")
