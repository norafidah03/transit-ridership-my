import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.transit.coverage import area_population, label_bus_stops  # noqa: E402


def test_label_bus_stops_uses_code_then_nearest():
    stops = pd.DataFrame({
        "stop_id": ["1", "2", "3"],
        "stop_name": ["KL1079 KL SENTRAL", "BD530 SURAU", "STESEN BRT X"],
        "stop_lat": ["3.13", "3.03", "3.031"], "stop_lon": ["101.68", "101.44", "101.441"],
    })
    s = label_bus_stops(stops).set_index("stop_id")
    assert s.loc["1", "area"] == "Kuala Lumpur"
    assert s.loc["3", "area"] == "Klang" and s.loc["3", "area_from"] == "nearest stop"


def test_area_population_combines_and_scales():
    pop = pd.DataFrame({
        "district": ["Gombak", "Ulu Langat", "Kinta"], "sex": "both", "age": "overall",
        "ethnicity": "overall", "date": "2026-01-01", "population": [1.0, 2.0, 5.0],
    })
    out = area_population(pop).set_index("area")
    assert out.loc["Gombak & Ulu Langat", "population"] == 3000
    assert "Kinta" not in out.index
