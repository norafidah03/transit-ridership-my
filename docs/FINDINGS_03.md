# Service gaps and crowding (Q3, Q4) · 5 Nov 2026

Notebook: `notebooks/03_service_gaps.py`. Timetables: Prasarana GTFS downloaded 5 Nov 2026 (rail,
Rapid Bus KL, MRT feeder buses). All numbers are for a normal weekday. Morning peak = 7 to 9am.

## Rail: scheduled peak frequency
| Line | Train every |
|---|---|
| LRT Ampang, LRT Sri Petaling | 3 min |
| LRT Kelana Jaya, BRT Sunway | 4 min |
| MRT Putrajaya | 5 min |
| MRT Kajang | 6 min |
| KL Monorail | 7 min |
| LRT Shah Alam | 8 min |

## Q3: crowding proxy (weekday riders per scheduled train-hour)
| Line | Weekday riders | Trains/day | Riders per train-hour |
|---|---|---|---|
| MRT Kajang | 293k | 256 | **776** |
| KL Monorail | 60k | 238 | 583 |
| MRT Putrajaya | 186k | 311 | 530 |
| LRT Kelana Jaya | 291k | 350 | 508 |
| LRT Ampang/Sri Petaling | 225k | 1,010 | 302 |
| LRT Shah Alam | 49k | 230 | 193 |

- MRT Kajang carries as many riders as Kelana Jaya with far fewer trains: the most stretched line on this measure.
- Ampang/Sri Petaling has the most trains (two lines sharing track through the city) and a lot of spare room.
- LRT Shah Alam, opened in 2026, still has plenty of capacity.
- Caveats: this is planned service, not measured crowding; trains differ in size between lines; train-hours
  = trains x end-to-end run time.

## Q4: bus waits in the morning peak
- 265 bus route-directions (173 city, 92 MRT feeder). The typical (median) route runs every **30 minutes** at peak.
- 80% of city routes and 65% of feeder routes run less often than every 20 minutes.
- 34 city routes have 1 or 2 buses in the whole 7 to 9am window (a 60 to 120 min wait), mostly in outer areas:
  Banting, Puncak Alam, Batu Arang, Selayang, Kajang (450), Shah Alam (752, 753) and Subang (770).
- Stops: of ~6,200 bus stops, about half (3,133) get **fewer than 2 buses an hour** at peak, and 54 get none.
  Only 427 stops get 8 or more per hour, mostly in the city centre (KL Sentral gets ~31/h).

## Caveats
- The timetable is today's snapshot, while ridership runs to Aug 2026.
- City and feeder feeds use different stop IDs, so a physical stop served by both counts twice.
