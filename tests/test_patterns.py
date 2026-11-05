import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.transit.patterns import _group, holiday_calendar  # noqa: E402


def test_groups():
    assert _group("Tahun Baharu Cina (Hari Kedua)") == "Chinese New Year"  # not "New Year"
    assert _group("Tahun Baharu") == "New Year"
    assert _group("Cuti Hari Raya Puasa (Hari Kedua)") == "Hari Raya Aidilfitri"
    assert _group("Hari Wesak") == "Other holiday"


def test_calendar_has_known_dates():
    cal = holiday_calendar(years=[2025])
    days = set(cal.date)
    assert pd.Timestamp("2025-08-31") in days  # Merdeka
    assert pd.Timestamp("2025-03-31") in days  # Hari Raya Puasa 2025
    assert pd.Timestamp("2025-02-01") in days  # Hari Wilayah (KL only)
    assert cal.date.is_unique
