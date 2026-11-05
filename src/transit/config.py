"""All data sources and paths in one place, so nothing is hard-coded elsewhere."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"

# Daily ridership by rail line / bus network (data.gov.my catalogue id: ridership_headline)
RIDERSHIP_HEADLINE_URL = "https://storage.data.gov.my/transportation/ridership_headline.parquet"

# GTFS static feeds from Prasarana (zip files)
GTFS_STATIC_BASE = "https://api.data.gov.my/gtfs-static/prasarana"
GTFS_CATEGORIES = ["rapid-rail-kl", "rapid-bus-kl", "rapid-bus-mrtfeeder"]

# GTFS realtime vehicle positions (protobuf), used for the stretch goal
GTFS_REALTIME_URL = "https://api.data.gov.my/gtfs-realtime/vehicle-position/prasarana?category=rapid-bus-kl"

# OpenDOSM population by district
POPULATION_DISTRICT_URL = "https://storage.dosm.gov.my/population/population_district.parquet"
