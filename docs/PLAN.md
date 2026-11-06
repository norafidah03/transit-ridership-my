# Transit Insight: Klang Valley Mobility Analytics

A portfolio data analytics project using open Malaysian government data (data.gov.my and OpenDOSM).

## 1. Why this project

You ride Rapid KL every day, so you already know the story the data should tell: some lines are packed at 8am, some feeder buses come every 30+ minutes, and some neighbourhoods have barely any service at all. The project turns that lived experience into evidence, which is exactly what a hiring manager wants to see: a real question, messy real data, a clear method, and a result someone could act on.

## 2. The questions

We answer these in order. Each one builds on the previous and each one becomes a page in the dashboard.

| # | Question | Why it matters | Main data |
|---|----------|----------------|-----------|
| Q1 | How has ridership on each rail line and bus network changed since 2019, and which lines have fully recovered from COVID? | Sets the baseline and shows trend-analysis skills | Daily ridership (headline) |
| Q2 | What are the weekly and seasonal patterns? How big is the weekday vs weekend gap, and what happens during Raya, CNY, school holidays and big events? | Shows time-series decomposition and feature engineering | Daily ridership + holiday calendar |
| Q3 | Which lines are most crowded relative to the service they run? | "Crowding" = riders per scheduled seat/trip, a capacity-stress proxy | Daily ridership + GTFS static (trips per day) |
| Q4 | Where is service thin? Which bus routes and stops have the longest headways in the morning peak? | The "under-served routes" story | GTFS static (stop_times, trips, calendar) |
| Q5 | Which districts have many people but little transit? | Equity angle: service supply vs population demand | GTFS stops + OpenDOSM district population |
| Q6 (stretch) | Do buses actually arrive as scheduled? How often do they bunch? | Real-world reliability, impressive real-time data work | GTFS realtime vehicle positions, collected over 1 to 2 weeks |

## 3. Datasets

All are free with no API key. Every ID below is checked in Milestone 1 before we depend on it.

| Dataset | Source | Format | Use |
|---------|--------|--------|-----|
| Daily public transport ridership (`ridership_headline`) | data.gov.my catalogue, file at `storage.data.gov.my/transportation/ridership_headline.parquet` | Parquet, one row per day, one column per line/network | Q1, Q2, Q3 |
| Rail origin-destination / station-level ridership | data.gov.my transportation catalogue (to confirm what granularity is published) | Parquet/CSV | Upgrades Q3 to station level if available |
| GTFS Static, Prasarana | `api.data.gov.my/gtfs-static/prasarana?category=rapid-rail-kl`, `rapid-bus-kl`, `rapid-bus-mrtfeeder` | GTFS zip | Q3, Q4, Q5 |
| GTFS Realtime, Prasarana buses | `api.data.gov.my/gtfs-realtime/vehicle-position/prasarana?category=rapid-bus-kl` | Protobuf feed, refreshes every ~30s | Q6 |
| Population by district | OpenDOSM `population_district` | Parquet | Q5 |
| District boundaries | data.gov.my / OpenDOSM geo files (or GADM level 2 as fallback) | GeoJSON | Q5 maps |
| Public holidays | Built from the official gazette list (small hand-made CSV) | CSV | Q2 |

## 4. Methods (and what you will learn)

**Data engineering**
- A reproducible `fetch` step that downloads raw files into `data/raw/` with the download date in the filename, so results can be re-run.
- Cleaning: reshape the wide daily table to long format (`date, mode, line, riders`), tidy line names, flag missing days and outliers (e.g. system outages, data glitches).

**Q1 Trends**
- 7-day and 28-day rolling averages; recovery index = current riders as a % of the same month in 2019.
- Year-on-year growth per line.

**Q2 Patterns**
- Day-of-week profiles, weekday/weekend ratio per line.
- Holiday effect: average ridership on holidays vs comparable normal days.
- Optional: STL decomposition (trend + weekly seasonality + residual) using `statsmodels`.

**Q3 Crowding proxy**
- From GTFS: scheduled trips per line per weekday.
- Riders per scheduled trip, and riders per seat-km if we add vehicle capacity assumptions (e.g. LRT 4-car ~ 800 pax). We are honest that this is a proxy, not measured load.

**Q4 Service gaps**
- From `stop_times`: departures per stop per hour; average headway per route in the AM peak (7 to 9am).
- Rank routes by peak headway; flag routes with headway > 20 min.

**Q5 Coverage vs population**
- Stops within each district, peak departures per 1,000 residents.
- Walk catchment: 400 m around bus stops, 800 m around rail stations (GeoPandas buffers).
- Scatter of population vs service; districts below the trend line are the "under-served" list.

**Q6 Reliability (stretch)**
- A small scheduled collector saves vehicle positions every 30 to 60 s for a week.
- Reconstruct observed headways at selected stops; bunching = two buses of the same route within 2 min.

## 5. Deliverables

1. **GitHub repo** with a clear README, project structure, requirements, and a short "Findings" section with charts.
2. **Notebooks**: `01_eda`, `02_patterns`, `03_service_gaps`, `04_coverage`.
3. **Streamlit dashboard** (deployed free on Streamlit Community Cloud) with pages: Overview, Trends, Patterns, Crowding, Service gaps, Coverage map.
4. **Write-up**: a 600 to 900 word LinkedIn/Medium post: "I commute on Rapid KL every day, so I analysed 6 years of ridership data".

## 6. Milestones

| Week | Milestone | Done when |
|------|-----------|-----------|
| 1 | Setup + data access | Repo created, `fetch.py` downloads ridership + GTFS, datasets verified |
| 1 | Clean + first EDA (Q1) | Long-format table saved, trend chart and recovery table produced |
| 2 | Patterns (Q2) | Day-of-week and holiday charts, 3 written insights |
| 3 | GTFS service analysis (Q3, Q4) | Peak headway table per route, crowding proxy per line |
| 4 | Coverage (Q5) | District map + under-served ranking |
| 5 | Dashboard | Streamlit app deployed with a public link |
| 6 | Polish + write-up | README findings, blog post, (optional) start Q6 collector |

## 7. Project structure

```
transit-ridership-my/
  README.md
  requirements.txt
  docs/PLAN.md
  data/raw/            # downloaded files (not committed to git)
  data/processed/      # cleaned outputs
  src/transit/
    config.py          # all URLs and paths in one place
    fetch.py           # download step
    clean.py           # reshape + tidy ridership
    gtfs.py            # headways and trips from GTFS
  notebooks/01_eda.py  # EDA, runs as a notebook in VS Code/Jupyter
  app/streamlit_app.py # dashboard
  tests/               # small tests for cleaning logic
```

## 8. Risks and how we handle them

- **Daily data has no hours.** Peak-hour crowding comes from GTFS schedule and (if published) station-level data; we label proxies clearly.
- **Column names can change** between data releases. The cleaning code melts every non-date column instead of hard-coding line names.
- **GTFS feeds are a snapshot** of today's schedule, not history. We note the snapshot date on every chart.
- **Scope creep.** Q6 is a stretch goal and only starts once Q1 to Q5 are in the dashboard.
