# Klang Valley Public Transport: Ridership, Crowding and Service Gaps

Analysing Malaysia's open public transport data (data.gov.my, OpenDOSM, Prasarana GTFS) to answer:
how has ridership recovered, when are lines busiest relative to service, and which areas are under-served?

See [docs/PLAN.md](docs/PLAN.md) for the full plan.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m src.transit.fetch          # downloads ridership, GTFS and population into data/raw/
pytest                               # checks the cleaning logic
# open notebooks/01_eda.py in VS Code and run the cells
streamlit run app/streamlit_app.py
```

## Data sources
- Daily ridership: data.gov.my, `ridership_headline`
- GTFS static and realtime: Prasarana via api.data.gov.my
- Population by district: OpenDOSM

## Findings
_Coming after Milestone 2._
