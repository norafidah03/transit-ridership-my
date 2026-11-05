"""Turn the wide daily ridership table into a tidy long table.

Input  (wide): date | bus_rkl | rail_lrt_kj | rail_mrt_kajang | ...
Output (long): date | mode | line | riders | dow | is_weekend
"""
from __future__ import annotations

import pandas as pd

# Friendly names for the dashboard. Unknown columns still work, they just keep their raw name.
LINE_NAMES = {
    "bus_rkl": "Rapid Bus KL",
    "bus_rkn": "Rapid Bus Kuantan",
    "bus_rpn": "Rapid Bus Penang",
    "rail_lrt_ampang": "LRT Ampang/Sri Petaling",
    "rail_lrt_kj": "LRT Kelana Jaya",
    "rail_mrt_kajang": "MRT Kajang",
    "rail_mrt_pjy": "MRT Putrajaya",
    "rail_lrt_shah_alam": "LRT Shah Alam",
    "rail_monorail": "KL Monorail",
    "rail_komuter": "KTM Komuter",
    "rail_komuter_utara": "KTM Komuter Utara",
    "rail_ets": "KTM ETS",
    "rail_intercity": "KTM Intercity",
    "rail_tebrau": "KTM Shuttle Tebrau",
}


def to_long(wide: pd.DataFrame) -> pd.DataFrame:
    df = wide.copy()
    df["date"] = pd.to_datetime(df["date"])
    long = df.melt(id_vars="date", var_name="series", value_name="riders")
    long["mode"] = long["series"].str.split("_", n=1).str[0]  # "bus" or "rail"
    long["line"] = long["series"].map(LINE_NAMES).fillna(long["series"])
    long["dow"] = long["date"].dt.day_name()
    long["is_weekend"] = long["date"].dt.dayofweek >= 5
    # A line that had not opened yet shows as missing; keep NaN rather than 0 so averages stay honest.
    long["riders"] = pd.to_numeric(long["riders"], errors="coerce").astype("float64")
    # A whole network carrying exactly 0 people means "not reported" (e.g. Rapid Kuantan from
    # Dec 2025), not a real zero, so treat it as missing too.
    long.loc[long["riders"] == 0, "riders"] = float("nan")
    return long.sort_values(["series", "date"]).reset_index(drop=True)


def flag_outliers(long: pd.DataFrame, weeks: int = 8, z: float = 4.0, min_pct: float = 15.0) -> pd.DataFrame:
    """Mark days far from what is normal for that line on that weekday.

    Compare each Monday with the surrounding Mondays, each Saturday with the surrounding Saturdays,
    and so on. (Comparing against all days would flag every weekend, because weekends are always
    quieter.) What remains are holidays, outages, big events and data glitches.
    """
    out = long.copy()
    grp = out.groupby(["series", out["date"].dt.dayofweek])["riders"]
    roll = lambda s: s.rolling(weeks + 1, min_periods=4, center=True).median()
    med = grp.transform(roll)
    out["dev"] = out["riders"] - med
    mad = out.groupby(["series", out["date"].dt.dayofweek])["dev"].transform(lambda s: roll(s.abs()))
    # Must be statistically unusual AND a big enough change (min_pct %) to matter in real life.
    out["is_outlier"] = ((out["dev"].abs() > z * 1.4826 * mad) & mad.gt(0)
                         & (out["dev"].abs() > min_pct / 100 * med))
    out["expected"] = med
    return out.drop(columns="dev")


def recovery_index(long: pd.DataFrame, base_year: int = 2019) -> pd.DataFrame:
    """Monthly average riders as % of the same calendar month in the base year."""
    m = (long.assign(year=long.date.dt.year, month=long.date.dt.month)
             .groupby(["series", "line", "year", "month"], as_index=False)["riders"].mean())
    base = m[m.year == base_year][["series", "month", "riders"]].rename(columns={"riders": "base"})
    m = m.merge(base, on=["series", "month"], how="left")
    m["recovery_pct"] = 100 * m["riders"] / m["base"]
    return m
