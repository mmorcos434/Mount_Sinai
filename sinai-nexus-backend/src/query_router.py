# -------------------------------------------------------------
# query_router.py
# -------------------------------------------------------------
# Purpose:
#   Connects Gemini intent recognition with the correct
#   query handler function.
# -------------------------------------------------------------

from src.query_interpreter import interpret_scheduling_query
from src.query_handlers import (
    exam_at_site,
    locations_for_exam,
    exams_at_site,
    exam_duration,
    rooms_for_exam_at_site,
    rooms_for_exam
)
from src.data_loader import USER_UPDATES

CONFIRMATION_FOOTER = (
    "\n\n NOTE: Please confirm that the chosen EXAM/LOCATION is correct. "
    "If not, feel free to be more specific in your query."
)

def get_location_notes(location: str):
    """
    Return a list of note strings associated with a given location prefix.
    If no notes exist, returns an empty list.
    """
    if not location:
        return []

    notes = []
    for entry in USER_UPDATES.get("location_notes", []):
        if entry.get("location", "").lower() == location.lower():
            notes.append(entry.get("note"))

    return notes

def format_location_notes(location: str):
    """
    Format location-specific notes for display, if any exist.
    """
    notes = get_location_notes(location)

    if not notes:
        return ""

    formatted = "\n⚠️ LOCATION NOTES:\n"
    for note in notes:
        formatted += f"- {note}\n"

    return formatted + "\n"

# Helper functions to return official site and exam names
# Only exam name
def format_exam_header(exam, content):
    """
    Prepend the official exam name to the answer content.
    """
    return (
        f"Official exam name: {exam}\n\n"
        f"{content.strip()}\n\n"
        f"{CONFIRMATION_FOOTER}"
    )

# Exam and site name
def format_site_exam_header(site, exam, content):
    """
    Prepend the official site and exam names to the answer.
    """

    notes_block = format_location_notes(site)

    return (
        f"Location name: {site}\n"
        f"Official exam name: {exam}\n\n"
        f"{notes_block}"
        f"{content.strip()}\n\n"
        f"{CONFIRMATION_FOOTER}"
    )

# Only site name
def format_site_header(site, content):
    """
    Prepend the official site name to the answer content.
    """

    notes_block = format_location_notes(site)

    return (
        f"Location name: {site}\n\n"
        f"{notes_block}"
        f"{content.strip()}\n\n"
        f"{CONFIRMATION_FOOTER}"
    )

def answer_scheduling_query(user_input: str):
    """
    Purpose:
        Handle any scheduling-related user question by:
          1. Sending it to Gemini for interpretation
          2. Routing it to the correct lookup function
          3. Returning a clear, human-readable answer
    """
    parsed = interpret_scheduling_query(user_input)
    intent = parsed.get("intent")
    exam = parsed.get("exam")
    site = parsed.get("site")

    print("\n--- Gemini interpretation ---")
    print(parsed)
    print("------------------------------\n")

    # Intent 1: "Is [exam] done at [site]?"
    if intent == "exam_at_site" and exam and site:
        found, official_exam, official_site = exam_at_site(exam, site)

        # Case 1: fuzzy match failed (exam or site name not recognized)
        if not official_exam:
            return "Exam name not recognized."
        if not official_site:
            return "Site name not recognized."

        # Case 2: return formatted answer
        content = (
            "Yes, this exam is performed at this site."
            if found else
            "No, this exam is not performed at this site."
        )

        return format_site_exam_header(official_site, official_exam, content)

        # return f"✅ Yes, {exam} is performed at {site}." if found \
               # else f"❌ No, {exam} is not listed at {site}."

    # Intent 2: "Which locations perform [exam]?"
    elif intent == "locations_for_exam" and exam:
        locs, official_exam = locations_for_exam(exam)

        # If fuzzy matching failed (i.e., no official exam name found)
        if not official_exam:
            return f"Exam name not recognized. Please check the spelling or try a more complete name."

        # If exam name is found but there are no sites
        if not locs:
            return f"Sorry, no locations were found for {official_exam}."

        content = "Performed at:\n" + "\n".join(locs)
        return format_exam_header(official_exam, content)

    # Intent 3: "What exams are offered at [site]?"
    elif intent == "exams_at_site" and site:
        exams, official_site = exams_at_site(site)

        if not official_site:
            return "Site name not recognized."
        if not exams:
            return f"No exams found for the site: {official_site}."
        
        content = "Exams offered:\n" + "\n".join(exams)
        return format_site_header(official_site, content)
    
    # Intent 4: "How long does [exam] take?"
    elif intent == "exam_duration" and exam:
        duration, official_exam = exam_duration(exam)

        if not official_exam:
            return "Exam name not recognized."

        if not duration:
            return f"No visit duration found for the exam: {official_exam}."

        content = f"Duration: {duration} minutes"
        return format_exam_header(official_exam, content)
    
    # Intent 5: "Which rooms at [site] perform [exam]?"
    elif intent == "rooms_for_exam_at_site" and exam and site:
        rooms, official_exam, official_site = rooms_for_exam_at_site(exam, site)

        if not official_exam:
            return "Exam name not recognized."
        if not official_site:
            return "Site name not recognized."

        if not rooms:
            return f"No rooms found performing {official_exam} at {official_site}."

        content = "Rooms:\n" + "\n".join(rooms)
        return format_site_exam_header(official_site, official_exam, content)
    
    # Intent 6: "Which rooms perform [exam]?"
    elif intent == "rooms_for_exam" and exam:
        rooms, official_exam = rooms_for_exam(exam)

        if not official_exam:
            return "Exam name not recognized."

        if not rooms:
            return f"No rooms found performing the exam: {official_exam}."

        content = "Rooms performing this exam:\n" + "\n".join(rooms)
        return format_exam_header(official_exam, content)

    # Fallback if Gemini can't classify the question
    else:
        return "Sorry, I couldn’t understand that scheduling question."