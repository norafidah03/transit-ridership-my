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

# GTFS static for KTM (Komuter, ETS, Intercity). Klang Valley Komuter = these two route_ids.
GTFS_KTMB_URL = "https://api.data.gov.my/gtfs-static/ktmb"
KTM_KOMUTER_KV_ROUTES = ["KA15_KD19", "KC05_KB18"]  # Port Klang Line, Seremban Line

# GTFS realtime vehicle positions (protobuf), used for the stretch goal
GTFS_REALTIME_URL = "https://api.data.gov.my/gtfs-realtime/vehicle-position/prasarana?category=rapid-bus-kl"

# OpenDOSM population by district
POPULATION_DISTRICT_URL = "https://storage.dosm.gov.my/population/population_district.parquet"

# Which GTFS rail route feeds which ridership series. Ampang and Sri Petaling lines are reported
# together in the ridership data, so both routes map to one series. BRT Sunway has no series.
RAIL_ROUTE_TO_SERIES = {
    "AG": "rail_lrt_ampang", "PH": "rail_lrt_ampang", "KJ": "rail_lrt_kj",
    "KGL": "rail_mrt_kajang", "PYL": "rail_mrt_pjy", "MR": "rail_monorail", "SA": "rail_lrt_shah_alam",
}
