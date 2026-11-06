# Coverage vs population (Q5) · 5 Nov 2026

Notebook: `notebooks/04_coverage.py`. Population: OpenDOSM district estimates for 2026. Service: weekday
7 to 9am departures from the Rapid KL bus, MRT feeder, Rapid Rail and KTM Komuter timetables (GTFS, 5 Nov 2026).

## How areas were built
No district boundary map could be downloaded from an allowed source, so each bus stop was placed using the
local-council code at the start of its stop code (KL..., PJ..., BD... for Klang, and so on). Stops without a code,
and rail stations, take the area of the nearest coded stop. Gombak and Ulu Langat are combined because the
Ampang Jaya council spans both.

## Result: peak departures per 1,000 residents
| Area | Residents | Bus stops | Rail stations | Residents per bus stop | Bus + rail peak departures per 1,000 |
|---|---|---|---|---|---|
| Kuala Langat | 332k | 88 | 0 | 3,768 | **0.4** |
| Kuala Selangor | 305k | 71 | 0 | 4,296 | **0.6** |
| Klang | 1.19M | 165 | 15 | **7,219** | **0.8** |
| Sepang | 354k | 113 | 2 | 3,134 | 2.3 |
| Gombak & Ulu Langat | 2.52M | 2,012 | 23 | 1,252 | 5.2 |
| Petaling | 2.38M | 1,862 | 74 | 1,279 | 5.8 |
| Kuala Lumpur | 2.08M | 1,668 | 115 | 1,248 | 10.0 |
| Putrajaya | 121k | 246 | 2 | 493 | 21.9 |

## What it says
- **Klang is the clearest gap.** It is the 4th biggest area (1.2 million people) but has 165 Rapid KL bus stops,
  one per 7,200 residents, compared with about one per 1,250 in KL, Petaling and Gombak/Ulu Langat. Its peak
  service per resident is about 1/12 of KL's.
- Kuala Langat and Kuala Selangor are even lower per resident, but they are partly rural, so some gap is expected.
- Putrajaya is the best served per resident: a small, planned city with many feeder routes.
- KL gets about twice the peak service per resident of the surrounding Selangor suburbs, mostly because of rail.

## Caveats
- **Only Rapid KL and KTM Komuter are counted.** Klang, Kuala Langat and Sepang also have other buses
  (e.g. Selangor's free Smart Selangor buses and private operators) and the KLIA Ekspres/Transit, which have no
  GTFS feed here. The gap is real for Rapid KL but may be smaller in total.
- Areas are large; a well-served centre can hide poorly served neighbourhoods inside the same area.
- Council areas don't match district borders exactly (e.g. part of Shah Alam council lies in Klang district),
  so the split between Petaling and Klang is approximate.
