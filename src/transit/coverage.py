"""Q5: how much public transport does each area get, relative to how many people live there?

We could not download district boundary maps (polygons) from an allowed source, so instead we use
a neat trick: every Rapid KL bus stop code starts with the local council that owns the stop
(KL1079 = Kuala Lumpur City Hall, PJ785 = Petaling Jaya, BD530 = Klang ...). We map councils to the
districts that OpenDOSM publishes population for. Stops without a code (and rail stations) take the
area of their nearest coded bus stop.

Limits, stated honestly:
- Councils and districts don't match exactly (e.g. Ampang Jaya council spans Gombak and Ulu Langat,
  so those two districts are combined; Shah Alam council reaches into Klang district).
- An area is large (KL is one unit of 2 million people), so this shows big gaps, not street-level ones.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

# Council code (start of stop code) -> area used for population.
COUNCIL_TO_AREA = {
    "KL": "Kuala Lumpur",
    "PPJ": "Putrajaya",
    "PJ": "Petaling", "SJ": "Petaling", "SA": "Petaling",
    "AJ": "Gombak & Ulu Langat", "SL": "Gombak & Ulu Langat", "KJ": "Gombak & Ulu Langat",
    "BD": "Klang",
    "SP": "Sepang",
    "LG": "Kuala Langat",
    "KS": "Kuala Selangor",
}

# OpenDOSM district -> same areas.
DISTRICT_TO_AREA = {
    "W.P. Kuala Lumpur": "Kuala Lumpur", "W.P. Putrajaya": "Putrajaya", "Petaling": "Petaling",
    "Gombak": "Gombak & Ulu Langat", "Ulu Langat": "Gombak & Ulu Langat", "Klang": "Klang",
    "Sepang": "Sepang", "Kuala Langat": "Kuala Langat", "Kuala Selangor": "Kuala Selangor",
}


def area_population(pop: pd.DataFrame, year: int | None = None) -> pd.DataFrame:
    """Total population per area (people, not thousands) for one year (default: latest)."""
    p = pop[(pop.sex == "both") & (pop.age == "overall") & (pop.ethnicity == "overall")].copy()
    p["date"] = pd.to_datetime(p["date"])
    year = year or p.date.dt.year.max()
    p = p[p.date.dt.year == year]
    p["area"] = p["district"].map(DISTRICT_TO_AREA)
    out = p.dropna(subset=["area"]).groupby("area", as_index=False)["population"].sum()
    out["population"] = (out["population"] * 1000).round()  # OpenDOSM publishes thousands
    return out.assign(year=year)


def council_code(stops: pd.DataFrame) -> pd.Series:
    """The letters at the start of stop_code (or of stop_name, where the code is embedded)."""
    src = stops["stop_code"] if "stop_code" in stops else stops["stop_name"]
    return src.fillna("").str.extract(r"^([A-Z]+)\d")[0]


def assign_area(points: pd.DataFrame, coded: pd.DataFrame, max_km: float | None = None) -> pd.Series:
    """Area of the nearest coded stop, for each point.

    Longitude is scaled by cos(latitude) so distances are fair near the equator; 1 degree ~ 111 km.
    With max_km, points further than that from any coded stop get NaN (outside our areas).
    """
    k = np.cos(np.radians(3.1))
    tree = cKDTree(np.c_[coded.stop_lat, coded.stop_lon * k])
    dist, idx = tree.query(np.c_[points.stop_lat, points.stop_lon * k])
    area = pd.Series(coded["area"].to_numpy()[idx], index=points.index)
    if max_km is not None:
        area[dist * 111 > max_km] = np.nan
    return area


def label_bus_stops(stops: pd.DataFrame) -> pd.DataFrame:
    s = stops.copy()
    s[["stop_lat", "stop_lon"]] = s[["stop_lat", "stop_lon"]].astype(float)
    s["area"] = council_code(s).map(COUNCIL_TO_AREA)
    s["area_from"] = np.where(s["area"].notna(), "stop code", "nearest stop")
    known = s.dropna(subset=["area"])
    s.loc[s.area.isna(), "area"] = assign_area(s[s.area.isna()], known)
    return s
