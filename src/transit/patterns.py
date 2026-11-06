"""Weekly and holiday patterns in daily ridership (Q2).

Main idea: to see what a holiday does, compare it with a *normal* day for the same line and the
same weekday nearby. `flag_outliers` in clean.py already computes that "expected" value for us.
"""
from __future__ import annotations

import holidays
import pandas as pd

# Group the official names into a few festivals people actually talk about.
HOLIDAY_GROUPS = {
    "Hari Raya Puasa": "Hari Raya Aidilfitri",
    "Hari Raya Qurban": "Hari Raya Haji",
    "Tahun Baharu Cina": "Chinese New Year",
    "Deepavali": "Deepavali",
    "Hari Kebangsaan": "Merdeka",
    "Hari Malaysia": "Malaysia Day",
    "Krismas": "Christmas",
    "Tahun Baharu": "New Year",  # checked after Tahun Baharu Cina, see _group()
}


def _group(name: str) -> str:
    for key, label in HOLIDAY_GROUPS.items():
        if key in name:
            return label
    return "Other holiday"


def holiday_calendar(years=range(2019, 2027), subdiv: str = "KUL") -> pd.DataFrame:
    """Public holidays in Kuala Lumpur (federal + KL-specific), one row per date.

    Islamic holiday dates come from the `holidays` package, which uses the officially announced
    dates for past years. Includes replacement holidays ("Cuti ...") which matter a lot for ridership.
    """
    cal = holidays.Malaysia(subdiv=subdiv, years=years)
    df = pd.DataFrame(sorted(cal.items()), columns=["date", "holiday"])
    df["date"] = pd.to_datetime(df["date"])
    df["group"] = df["holiday"].map(_group)
    return df


def add_calendar(long: pd.DataFrame, cal: pd.DataFrame) -> pd.DataFrame:
    """Add is_holiday / holiday / group columns, and pct_of_normal (riders vs same-weekday norm)."""
    out = long.merge(cal, on="date", how="left")
    out["is_holiday"] = out["holiday"].notna()
    out["pct_of_normal"] = 100 * out["riders"] / out["expected"]
    return out


def dow_profile(long: pd.DataFrame, days: int = 365) -> pd.DataFrame:
    """Average riders per weekday as % of that line's Mon–Fri average (holidays excluded)."""
    recent = long[(long.date > long.date.max() - pd.Timedelta(days=days)) & ~long.is_holiday]
    avg = recent.groupby(["line", "dow"])["riders"].mean().unstack()
    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    avg = avg[order]
    return (100 * avg.div(avg[order[:5]].mean(axis=1), axis=0)).round(0)


def holiday_effect(long: pd.DataFrame, since: str = "2023-01-01") -> pd.DataFrame:
    """Median % of normal ridership on each festival, per line (from `since`, after COVID rules).

    Only holidays that fall on a weekday count. A holiday on a Saturday is compared with a normal
    Saturday, when most people are off anyway, so it hides the effect we want to measure.
    """
    h = long[long.is_holiday & ~long.is_weekend & (long.date >= since)].dropna(subset=["pct_of_normal"])
    return h.pivot_table(index="group", columns="line", values="pct_of_normal", aggfunc="median").round(0)


def festival_curve(long: pd.DataFrame, cal: pd.DataFrame, group: str, before: int = 10,
                   after: int = 10, since: str = "2023-01-01") -> pd.DataFrame:
    """% of normal for each day around a festival's main day (day 0), median over the years.

    Day 0 is the day itself (e.g. "Hari Raya Puasa"), not its second day or replacement holiday.
    """
    # The main day is the one without "Cuti" (replacement) or "(Hari Kedua)" / "(pergantian hari)".
    is_main = lambda n: _group(n) == group and not n.startswith("Cuti") and "(" not in n
    firsts = cal[(cal.date >= since) & cal.holiday.str.split("; ").apply(lambda ns: any(map(is_main, ns)))].date
    rows = []
    for d0 in firsts:
        win = long[(long.date >= d0 - pd.Timedelta(days=before)) & (long.date <= d0 + pd.Timedelta(days=after))]
        rows.append(win.assign(day=(win.date - d0).dt.days))
    w = pd.concat(rows)
    return w.groupby(["line", "day"], as_index=False)["pct_of_normal"].median()
