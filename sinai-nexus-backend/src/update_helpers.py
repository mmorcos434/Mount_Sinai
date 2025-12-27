# -------------------------------------------------------------
# update_helpers.py
# -------------------------------------------------------------
# Purpose:
#   Manage temporary user updates (e.g., marking an exam as
#   unavailable at a site) without touching the main dataset.
# -------------------------------------------------------------

import json
import pandas as pd
from src.data_loader import USER_UPDATES

# update_helpers.py

from src.data_loader import USER_UPDATES
from src.fuzzy_matchers import best_site_match
import json
import pandas as pd

def add_location_note(note_text: str):
    """
    Store a free-text operational note and automatically associate it
    with a resolved location prefix.

    Example note:
        "MRI machine down for maintenance in HESS site; book MRIs in room 2 instead"
    """

    if not isinstance(note_text, str) or not note_text.strip():
        raise ValueError("Note text must be a non-empty string")

    # Reuse the SAME site-resolution logic used for user queries
    site_match = best_site_match(note_text)

    if not site_match:
        raise ValueError("Could not confidently determine location from note")

    location_prefix, _ = site_match

    USER_UPDATES.setdefault("location_notes", []).append({
        "location": location_prefix,
        "note": note_text.strip(),
        "timestamp": pd.Timestamp.now().isoformat()
    })

    with open("data/updates.json", "w") as f:
        json.dump(USER_UPDATES, f, indent=2)

    print(f"📝 Added note for location {location_prefix}")

"""
def disable_exam(exam, site, reason="unspecified"):
    #Temporarily mark an exam unavailable at a site.
    USER_UPDATES["disabled_exams"].append({
        "exam": exam,
        "site": site,
        "reason": reason,
        "timestamp": pd.Timestamp.now().isoformat()
    })
    with open("data/updates.json", "w") as f:
        json.dump(USER_UPDATES, f, indent=2)
    print(f"✅ Marked {exam} at {site} as unavailable ({reason}).")

def enable_exam(exam, site):
    #Re-enable a previously disabled exam at a site.
    USER_UPDATES["disabled_exams"] = [
        e for e in USER_UPDATES["disabled_exams"]
        if not (
            e["exam"].lower() == exam.lower()
            and e["site"].lower() == site.lower()
        )
    ]
    with open("data/updates.json", "w") as f:
        json.dump(USER_UPDATES, f, indent=2)
    print(f"✅ Re-enabled {exam} at {site}.")
"""