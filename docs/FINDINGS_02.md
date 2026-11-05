# Weekly and holiday patterns (Q2) · 5 Nov 2026

Notebook: `notebooks/02_patterns.py`. Holidays: Kuala Lumpur public holidays from the `holidays`
package (`data/processed/holidays_kl.csv`). "% of normal" = riders vs the median of the same weekday
in the surrounding ~8 weeks.

## 1. Three kinds of line, by their weekly shape (last 12 months, holidays removed)
- **Office commuter lines**: LRT Kelana Jaya and MRT Putrajaya drop to about half on Sundays (50%, 52%).
  Rapid Bus KL, KTM Komuter, LRT Ampang and MRT Kajang sit at 60 to 65% on Sundays.
- **City / leisure line**: KL Monorail keeps 81% on Sundays and peaks on Friday (Bukit Bintang nightlife and shopping).
- **Weekend lines**: LRT Shah Alam carries 28% *more* on Sunday than on a weekday. KTM ETS and Intercity
  peak Friday to Sunday (going home or travelling), and are quietest Tuesday and Wednesday.
- Wednesday is the busiest weekday on every urban line (101 to 104%); Monday and Friday are slightly lower.

## 2. Weekday public holidays roughly halve commuter ridership
- LRT Kelana Jaya carries 49 to 60% of a normal day on a weekday holiday; Hari Raya Aidilfitri is the deepest (49%).
- MRT Kajang holds up better (63 to 72%, 88% at Christmas), likely because it serves malls and Bukit Bintang.
- KTM Intercity more than doubles on CNY, Deepavali, Christmas and Malaysia Day (255 to 282%).
- Merdeka is unusual: Rapid Bus KL carries 97% of a normal day, likely parade and celebration crowds.

## 3. The Hari Raya "balik kampung" curve
- Commuter lines start emptying 2 days before Raya (Kelana Jaya 80% at day -2, 59% at day -1).
- ETS and Intercity fill up 3 to 4 days before (Intercity ~178%), and again 2 to 4 days after Raya
  for the trip back (Intercity 210 to 240%).
- Commuter lines take about a week to return to normal (Kelana Jaya 97% by day 8).
- Caveat: when Raya falls on a weekend it looks closer to normal, because it is compared with a normal weekend.

## 4. Underlying trend (STL), average level per year
| Line | 2023 | 2024 | 2025 | 2026 (Jan to Aug) |
|---|---|---|---|---|
| LRT Kelana Jaya | 198k | 228k | 242k | 243k |
| MRT Kajang | 182k | 231k | 254k | 263k |
| MRT Putrajaya | 79k | 130k | 152k | 161k |
| Rapid Bus KL | 177k | 205k | 214k | 212k |

Growth has flattened on LRT Kelana Jaya and Rapid Bus KL, while both MRT lines are still growing.

## Not done yet
- School holidays: no official machine-readable calendar found yet; it needs a small hand-made CSV from the MOE calendar.
