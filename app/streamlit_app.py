"""Dashboard skeleton. Run: streamlit run app/streamlit_app.py"""
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.transit import config  # noqa: E402
from src.transit.clean import recovery_index  # noqa: E402

st.set_page_config(page_title="Klang Valley Transit", layout="wide")
st.title("Klang Valley public transport: ridership and service gaps")

path = config.PROCESSED / "ridership_long.parquet"
if not path.exists():
    st.warning("Run the fetch step and notebooks/01_eda.py first to create data/processed/ridership_long.parquet")
    st.stop()

long = pd.read_parquet(path)
lines = sorted(long.line.unique())
pick = st.multiselect("Lines", lines, default=[l for l in lines if l.startswith(("LRT", "MRT"))])
view = long[long.line.isin(pick)].copy()
view["riders_28d"] = view.groupby("line")["riders"].transform(lambda s: s.rolling(28, min_periods=14).mean())

tab1, tab2, tab3 = st.tabs(["Trends", "Recovery vs 2019", "Service gaps (coming)"])
with tab1:
    st.plotly_chart(px.line(view, x="date", y="riders_28d", color="line"), use_container_width=True)
with tab2:
    rec = recovery_index(view)
    rec["month_start"] = pd.to_datetime(dict(year=rec.year, month=rec.month, day=1))
    st.plotly_chart(px.line(rec[rec.year > 2019], x="month_start", y="recovery_pct", color="line"),
                    use_container_width=True)
with tab3:
    st.info("Peak headways per bus route from GTFS will appear here in Milestone 3.")
