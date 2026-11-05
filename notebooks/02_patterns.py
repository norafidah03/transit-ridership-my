# %% [markdown]
# # 02 · Weekly and holiday patterns (Q2)
# Question: what does a normal week look like on each line, and what do holidays do to ridership?
#
# Key idea used all through this notebook: **compare like with like**. A Monday is compared with
# nearby Mondays, never with a Sunday. `expected` = the median of the same weekday over the
# surrounding ~8 weeks, and `pct_of_normal` = riders / expected × 100.

# %%
import sys
from pathlib import Path

ROOT = Path.cwd() if (Path.cwd() / "src").exists() else Path.cwd().parent
sys.path.insert(0, str(ROOT))

import pandas as pd
import plotly.express as px
from statsmodels.tsa.seasonal import STL
from src.transit import config
from src.transit.clean import flag_outliers, to_long
from src.transit.patterns import add_calendar, dow_profile, festival_curve, holiday_calendar, holiday_effect

KV = ["LRT Kelana Jaya", "LRT Ampang/Sri Petaling", "MRT Kajang", "MRT Putrajaya", "KL Monorail",
      "LRT Shah Alam", "Rapid Bus KL", "KTM Komuter", "KTM ETS", "KTM Intercity"]

# %% [markdown]
# ## 1. Holiday calendar
# Kuala Lumpur public holidays from the `holidays` package, including replacement days ("Cuti ...").
# Saved to data/processed so you can open it in Excel and check it.

# %%
cal = holiday_calendar()
config.PROCESSED.mkdir(parents=True, exist_ok=True)
cal.to_csv(config.PROCESSED / "holidays_kl.csv", index=False)
cal[cal.date.dt.year == 2026]

# %%
wide = pd.read_parquet(config.RAW / "ridership_headline.parquet")
long = add_calendar(flag_outliers(to_long(wide)), cal)

# %% [markdown]
# ## 2. The shape of a normal week
# Each weekday as % of that line's Mon–Fri average, last 12 months, holidays removed.
# Below ~65% at weekends = a commuter line. Above 100% = a leisure / long-distance line.

# %%
dow = dow_profile(long).loc[KV]
px.imshow(dow, text_auto=True, color_continuous_scale="RdBu", color_continuous_midpoint=100,
          aspect="auto", title="Riders by weekday, % of the line's weekday average")

# %%
dow

# %% [markdown]
# ## 3. What a public holiday does (weekday holidays only)
# A holiday on a Saturday is compared with a normal Saturday, when most people are off anyway,
# so it hides the effect. We only keep holidays that fall Mon–Fri, from 2023 (after COVID rules).

# %%
eff = holiday_effect(long)[KV]
eff

# %% [markdown]
# ## 4. The Hari Raya and CNY "balik kampung" curves
# Day 0 = the festival day. Median % of normal over 2023–2026, per line.
# Watch commuter lines empty out while ETS / Intercity fill up before and after.
# Caveat: in some years day 0 was a weekend, which pulls the day-0 value toward 100.

# %%
lines = ["LRT Kelana Jaya", "MRT Kajang", "Rapid Bus KL", "KTM ETS", "KTM Intercity"]
for fest in ["Hari Raya Aidilfitri", "Chinese New Year"]:
    c = festival_curve(long, cal, fest, before=7, after=10)
    fig = px.line(c[c.line.isin(lines)], x="day", y="pct_of_normal", color="line", markers=True,
                  title=f"{fest}: riders as % of a normal day")
    fig.add_hline(y=100, line_dash="dot")
    fig.show()

# %% [markdown]
# ## 5. Split a line into trend + weekly rhythm + surprises (STL)
# STL ("Seasonal-Trend decomposition using LOESS") pulls a series apart into:
# - **trend**: the slow underlying level (is the line growing?)
# - **seasonal**: the repeating weekly pattern
# - **residual**: everything else (holidays, outages, events)
# We use log(riders) so the weekly pattern is a % effect, not a fixed number of people.

# %%
import numpy as np

line = "LRT Kelana Jaya"
s = long[(long.line == line) & (long.date >= "2023-01-01")].set_index("date")["riders"].asfreq("D")
s = s.interpolate()
res = STL(np.log(s), period=7, robust=True).fit()
parts = pd.DataFrame({"riders": s, "trend": np.exp(res.trend),
                      "weekly_effect_pct": 100 * (np.exp(res.seasonal) - 1),
                      "residual_pct": 100 * (np.exp(res.resid) - 1)})
px.line(parts.reset_index().melt(id_vars="date"), x="date", y="value", facet_row="variable",
        height=800, title=f"{line}: STL decomposition").update_yaxes(matches=None)

# %%
# Average trend level per year: is the line still growing?
parts["trend"].resample("YE").mean().round(-3)

# %% [markdown]
# ## 6. Write down 3 insights
# Put them in docs/FINDINGS_02.md in plain words, as if telling a friend.
