import json
import os
import pytest

from src.update_helpers import add_location_note
from src.query_router import answer_scheduling_query
from src.data_loader import USER_UPDATES

# run via pytest testing/test_location_notes.py


def test_add_location_note_and_display_in_response(tmp_path, monkeypatch):
    """
    Integration-style test that verifies:
      1) A free-text note is correctly resolved to a location
      2) The note is stored in USER_UPDATES
      3) The note is displayed when answering a question about that location
    """

    # ---------------------------------------------------------
    # Step 0: Ensure we start with a clean notes state
    # ---------------------------------------------------------
    USER_UPDATES["location_notes"] = []

    # ---------------------------------------------------------
    # Step 1: Add a realistic free-text operational note
    # ---------------------------------------------------------
    note_text = (
        "MRI machine down for maintenance in HESS site; "
        "book MRIs in room 2 instead"
    )

    add_location_note(note_text)

    # ---------------------------------------------------------
    # Step 2: Verify the note was stored and location was resolved
    # ---------------------------------------------------------
    assert "location_notes" in USER_UPDATES
    assert len(USER_UPDATES["location_notes"]) == 1

    stored_note = USER_UPDATES["location_notes"][0]

    # This is the critical assertion:
    # the system must resolve "HESS" → "1470 MADISON AVE"
    assert stored_note["location"] == "1470 MADISON AVE"
    assert note_text in stored_note["note"]

    # ---------------------------------------------------------
    # Step 3: Ask a question about that location
    # ---------------------------------------------------------
    response = answer_scheduling_query(
        "Is MRI Brain done at 1470 Madison Ave?"
    )

    # ---------------------------------------------------------
    # Step 4: Verify the note appears in the chatbot output
    # ---------------------------------------------------------
    assert "LOCATION NOTES" in response
    assert "MRI machine down for maintenance" in response
    assert "1470 MADISON AVE" in response