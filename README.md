# Klang Valley Public Transport: Ridership, Crowding and Service Gaps

Analysing Malaysia's open public transport data (data.gov.my, OpenDOSM, Prasarana GTFS) to answer:
how has ridership recovered, when are lines busiest relative to service, and which areas are under-served?

**Live dashboard: https://transit-ridership-my-4jhdrpw8kh8u6rx4nb9vc8.streamlit.app/**

See [docs/PLAN.md](docs/PLAN.md) for the full plan.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m src.transit.fetch          # downloads ridership, GTFS and population into data/raw/
pytest                               # checks the cleaning and GTFS logic
# open notebooks/01_eda.py ... 04_coverage.py in VS Code and run the cells
python -m src.transit.build          # saves the small tables the dashboard reads into app/data/
streamlit run app/streamlit_app.py
```

## Data sources
- Daily ridership: data.gov.my, `ridership_headline`
- GTFS static and realtime: Prasarana via api.data.gov.my
- GTFS static, KTM (Komuter): api.data.gov.my/gtfs-static/ktmb
- Population by district: OpenDOSM

## Dashboard
`app/streamlit_app.py` reads only `app/data/` (about 1 MB, committed), so it runs on Streamlit Community Cloud
without downloading anything. To refresh it with new data: `fetch`, then `build`, then commit `app/data/`.

## Findings
- Rail ridership on the 4 lines open since 2019 averaged 116% of the 2019 level in 2025; LRT Kelana Jaya is the only one still below.
- A weekday public holiday roughly halves commuter ridership; Hari Raya hits hardest.
- MRT Kajang is the most stretched rail line: 776 weekday riders per scheduled train-hour.
- The typical Rapid KL bus route runs every 30 minutes at peak; about half of stops get 2 or fewer buses an hour.
- Klang (1.2M residents) has one Rapid KL bus stop per 7,200 people, versus about one per 1,250 in KL.

Details: [docs/FINDINGS_01.md](docs/FINDINGS_01.md) to [docs/FINDINGS_04.md](docs/FINDINGS_04.md).
