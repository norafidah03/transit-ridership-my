"""Download raw data into data/raw/.

Run from the project root:
    python -m src.transit.fetch            # everything
    python -m src.transit.fetch ridership  # just one source
"""
from __future__ import annotations

import sys
from datetime import date

import requests

from . import config


def _download(url: str, filename: str) -> None:
    config.RAW.mkdir(parents=True, exist_ok=True)
    out = config.RAW / filename
    print(f"Downloading {url}")
    resp = requests.get(url, timeout=120)
    resp.raise_for_status()
    out.write_bytes(resp.content)
    print(f"  saved {out.relative_to(config.ROOT)} ({len(resp.content) / 1e6:.1f} MB)")


def fetch_ridership() -> None:
    _download(config.RIDERSHIP_HEADLINE_URL, "ridership_headline.parquet")


def fetch_gtfs() -> None:
    # GTFS is a snapshot of the current timetable, so keep the download date in the name.
    stamp = date.today().isoformat()
    for cat in config.GTFS_CATEGORIES:
        _download(f"{config.GTFS_STATIC_BASE}?category={cat}", f"gtfs_{cat}_{stamp}.zip")


def fetch_population() -> None:
    _download(config.POPULATION_DISTRICT_URL, "population_district.parquet")


SOURCES = {"ridership": fetch_ridership, "gtfs": fetch_gtfs, "population": fetch_population}

if __name__ == "__main__":
    wanted = sys.argv[1:] or list(SOURCES)
    for name in wanted:
        SOURCES[name]()
