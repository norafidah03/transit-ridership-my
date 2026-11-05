import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.transit.clean import flag_outliers, recovery_index, to_long  # noqa: E402


def _wide():
    # Tiny hand-made table to test the reshaping logic only (not real data).
    return pd.DataFrame({
        "date": ["2019-01-07", "2019-01-12", "2024-01-08", "2024-01-13"],
        "rail_lrt_kj": [100, 50, 90, None],
        "bus_new_route": [10, 5, 20, 8],
    })


def test_to_long_shape_and_labels():
    long = to_long(_wide())
    assert len(long) == 8
    assert set(long["mode"]) == {"rail", "bus"}
    assert "LRT Kelana Jaya" in set(long["line"])
    assert "bus_new_route" in set(long["line"])  # unknown columns keep raw name
    assert long.loc[long.date == "2019-01-12", "is_weekend"].all()


def test_missing_stays_missing():
    long = to_long(_wide())
    assert long["riders"].isna().sum() == 1


def test_recovery_index():
    rec = recovery_index(to_long(_wide()))
    kj = rec[(rec.series == "rail_lrt_kj") & (rec.year == 2024)].iloc[0]
    assert round(kj.recovery_pct, 1) == round(100 * 90 / 75, 1)


def test_zero_means_missing():
    wide = pd.DataFrame({"date": ["2025-01-01", "2025-01-02"], "bus_rkn": [500, 0]})
    assert to_long(wide)["riders"].isna().sum() == 1


def test_weekends_are_not_outliers():
    # Ten weeks of a regular line: busy weekdays, quiet weekends, one outage day.
    dates = pd.date_range("2024-01-01", periods=70)
    riders = [(100 if d.dayofweek < 5 else 40) + i % 3 for i, d in enumerate(dates)]  # small wobble
    riders[30] = 5  # outage
    long = flag_outliers(to_long(pd.DataFrame({"date": dates, "rail_lrt_kj": riders})))
    assert long.loc[long.is_outlier, "date"].tolist() == [dates[30]]
