# %% [markdown]
# # 01 · First look at daily ridership (Q1)
# Open this file in VS Code or Jupyter (with jupytext) and run cell by cell.
# Before running: `python -m src.transit.fetch ridership` from the project root.

# %%
import sys
from pathlib import Path

ROOT = Path.cwd() if (Path.cwd() / "src").exists() else Path.cwd().parent
sys.path.insert(0, str(ROOT))

import pandas as pd
import plotly.express as px
from src.transit import config
from src.transit.clean import flag_outliers, recovery_index, to_long

# %% [markdown]
# ## 1. Load and inspect the raw table
# Always look at the shape, columns, date range and missing values before analysing anything.

# %%
wide = pd.read_parquet(config.RAW / "ridership_headline.parquet")
print(wide.shape)
print(wide["date"].min(), "→", wide["date"].max())
wide.tail()

# %%
wide.isna().sum().sort_values(ascending=False)  # NaN usually means "line not open yet"

# %% [markdown]
# ## 2. Reshape to long format and save

# %%
long = flag_outliers(to_long(wide))
config.PROCESSED.mkdir(parents=True, exist_ok=True)
long.to_parquet(config.PROCESSED / "ridership_long.parquet", index=False)
long.head()

# %% [markdown]
# ## 3. Trends: 28-day rolling average per line (Klang Valley rail + bus)

# %%
kv = long[long.series.isin(["rail_lrt_kj", "rail_lrt_ampang", "rail_mrt_kajang",
                            "rail_mrt_pjy", "rail_monorail", "rail_lrt_shah_alam", "rail_komuter", "bus_rkl"])].copy()
kv["riders_28d"] = kv.groupby("series")["riders"].transform(lambda s: s.rolling(28, min_periods=14).mean())
px.line(kv, x="date", y="riders_28d", color="line", title="Daily riders, 28-day average")

# %% [markdown]
# ## 4. Recovery vs 2019
# Only 4 lines have 2019 data (LRT Kelana Jaya, LRT Ampang/Sri Petaling, MRT Kajang, Monorail).
# Bus data starts 2022, MRT Putrajaya opened mid-2022 and LRT Shah Alam in 2026, so they show no index.

# %%
rec = recovery_index(long)
latest_year = rec.year.max()
(rec[rec.year == latest_year].groupby("line")["recovery_pct"].mean()
    .dropna().sort_values(ascending=False).round(1))

# %% [markdown]
# ## 5. Weekday vs weekend

# %%
recent = long[long.date >= long.date.max() - pd.Timedelta(days=365)]
ratio = (recent.groupby(["line", "is_weekend"])["riders"].mean().unstack()
         .rename(columns={False: "weekday", True: "weekend"}))
ratio["weekend_share_of_weekday"] = (ratio.weekend / ratio.weekday).round(2)
ratio.sort_values("weekend_share_of_weekday")

# %% [markdown]
# ## 6. Outlier days worth investigating
# Write down what happened on these dates (holidays? outages? concerts?). These become stories.

# %%
out = long[long.is_outlier].assign(pct_of_normal=lambda d: (100 * d.riders / d.expected).round())
out.sort_values("date", ascending=False).head(30)[["date", "dow", "line", "riders", "expected", "pct_of_normal"]]
