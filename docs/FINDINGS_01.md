# First findings from the real data (5 Nov 2026)

Data: `ridership_headline`, 1 Jan 2019 to 31 Aug 2026 (2,800 days). GTFS snapshot downloaded 5 Nov 2026.

## What the data contains
- 14 series: 3 bus networks (KL, Penang, Kuantan) and 11 rail lines.
- Only 4 lines go back to 2019: LRT Kelana Jaya, LRT Ampang/Sri Petaling, MRT Kajang, KL Monorail.
- Bus data starts Jan 2022, MRT Putrajaya Jun 2022, KTM Komuter Sep 2023, LRT Shah Alam Apr 2026.
- Rapid Bus Kuantan reports 0 riders every day since 15 Dec 2025: treated as "not reported".

## Q1: recovery
- The 4 original lines together averaged 647k riders/day in 2019, fell to 194k in 2021, and reached 752k in 2025 (116% of 2019).
- Jan to Aug 2026 vs the same months of 2019: Monorail 178%, MRT Kajang 154%, LRT Ampang 114%, LRT Kelana Jaya 96%.
- Kelana Jaya is the only original line still below 2019.
- Klang Valley urban rail + Rapid Bus KL + Komuter: ~1.17M riders/day in 2026.
- Busiest day in the data: 31 Dec 2025 (New Year's Eve), 1.6M riders.

## Q2 preview: weekday vs weekend (last 12 months)
- Commuter lines: LRT Kelana Jaya weekends are 56% of weekdays, MRT Putrajaya 59%.
- Leisure lines: Monorail 88%, and LRT Shah Alam, ETS and Intercity are busier on weekends.
- Holidays stand out clearly: on Merdeka (31 Aug 2026) LRT Kelana Jaya carried 56% of a normal Monday,
  while Intercity carried 251%.

## Q4 preview: peak service (GTFS, 7 to 9am)
- Rail: Ampang/Sri Petaling every 3 min on weekdays.
- Slowest Rapid Bus KL peak routes: 752 (Putra Heights to Shah Alam) ~100 min, T715 and 754 ~90 min.

## Fixes made to the code
- `clean.py`: added LRT Shah Alam name; zeros now count as missing; outliers are judged against the
  same weekday (before, 87% of "outliers" were just normal weekends).
- `gtfs.py`: skip `__MACOSX` junk files in the rail zip; expand `frequencies.txt` (Rapid KL feeds list
  "every 3 minutes" instead of each trip, so headways were badly wrong); fill empty feeder route names.
