import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.transit import gtfs  # noqa: E402


def _feed():
    # One route, one template trip of 2 stops (5 min apart), repeated every 10 min from 07:00 to 08:00.
    s = lambda d: pd.DataFrame(d).astype(str)
    return {
        "calendar": s({"service_id": ["wk", "we"], "wednesday": [1, 0]}),
        "trips": s({"trip_id": ["t1", "t2"], "route_id": ["R", "R"], "service_id": ["wk", "we"], "direction_id": [0, 0]}),
        "stop_times": s({"trip_id": ["t1", "t1", "t2"], "stop_id": ["A", "B", "A"], "stop_sequence": [1, 2, 1],
                         "departure_time": ["7:00:00", "7:05:00", "9:00:00"]}),
        "frequencies": s({"trip_id": ["t1"], "start_time": ["07:00:00"], "end_time": ["08:00:00"], "headway_secs": [600]}),
        "routes": s({"route_id": ["R"], "route_short_name": ["R1"], "route_long_name": ["Test"]}),
        "stops": s({"stop_id": ["A", "B"], "stop_name": ["Alpha", "Beta"], "stop_lat": [3.1, 3.2], "stop_lon": [101.6, 101.7]}),
    }


def test_weekday_service_ids():
    assert gtfs.weekday_service_ids(_feed()) == {"wk"}


def test_frequencies_are_expanded():
    g = _feed()
    deps = gtfs.all_departures(g, gtfs.weekday_service_ids(g))
    assert deps.trip_id.nunique() == 6            # 07:00, 07:10, ... 07:50
    assert len(deps) == 12                         # 2 stops each
    assert sorted(deps[deps.stop_id == "B"].dep_s)[:2] == [7 * 3600 + 300, 7 * 3600 + 900]


def test_peak_service():
    g = _feed()
    deps = gtfs.all_departures(g, {"wk"})
    r = gtfs.route_peak_service(deps, g["routes"]).iloc[0]
    assert (r.peak_trips, r.avg_headway_min) == (6, 20)   # 120 min window / 6 trips
    s = gtfs.stop_peak_service(deps, g["stops"]).set_index("stop_id")
    assert s.loc["A", "per_hour"] == 3
