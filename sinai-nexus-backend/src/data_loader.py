# -------------------------------------------------------------
# data_loader.py
# -------------------------------------------------------------
# Purpose:
#   Load the main scheduling dataset, room mappings, and update
#   records into memory for other modules to use.
#
#   This ensures all data sources are initialized in one place,
#   so that other modules (like query_handlers) can simply
#   import df, ROOM_PREFIX_TO_LOCATION, and USER_UPDATES directly.
# -------------------------------------------------------------

import pandas as pd
import json
from data.location_prefixes import LOCATION_PREFIXES

# Load the cleaned scheduling data
df = pd.read_parquet("data/new_scheduling_clean.parquet")

# Load prefix-to-department mapping
from data.room_location_map import ROOM_PREFIX_TO_LOCATION

# Load user updates (if file exists)
try:
    with open("data/updates.json") as f:
        USER_UPDATES = json.load(f)
except FileNotFoundError:
    USER_UPDATES = {"disabled_exams": []}


# Build a mapping from location prefixes to full department names
# One location prefix may correspond to multiple department names
# This creates a mapping like:
# {
#   "1176 5TH AVE": [
#       "1176 5TH AVE RAD CT",
#       "1176 5TH AVE RAD MRI"
#   ],
#   "10 UNION SQ E": [
#       "10 UNION SQ E RAD MRI"
#   ]
# }

LOCATION_TO_DEPARTMENTS = {}

for prefix in LOCATION_PREFIXES.keys():
    deps = (
        df[df["DEP Name"].str.startswith(prefix)]["DEP Name"]
        .drop_duplicates()
        .tolist()
    )

    if not deps:
        print(f"⚠️ Warning: location prefix '{prefix}' matched no departments")

    LOCATION_TO_DEPARTMENTS[prefix] = deps