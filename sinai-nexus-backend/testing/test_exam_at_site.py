# testing/test_exam_at_site.py

from src.query_handlers import exam_at_site


def test_exam_at_site_print():
    """
    Print-based exploratory test for exam_at_site.

    This test is meant to:
      - Verify that site resolution returns a LOCATION PREFIX (not departments)
      - Verify that multi-department locations work correctly
      - Verify that failures are handled cleanly

    Run with:
        pytest testing/test_exam_at_site.py -s
    """

    test_cases = [
        # Expected: True or False depending on dataset contents
        ("CT HEAD", "1176 5th ave"),
        ("CT HEAD", "union square"),
        ("MRI BRAIN", "1176 fifth avenue"),
        ("XRAY CHEST", "hess"),

        # Likely negative cases
        ("MADE UP EXAM", "1176 5th ave"),
        ("CT HEAD", "random nonsense location"),
    ]

    for exam_query, site_query in test_cases:
        found, exam, site = exam_at_site(exam_query, site_query)

        print("\n----------------------------------")
        print(f"User exam query: {exam_query}")
        print(f"User site query: {site_query}")
        print(f"Resolved exam: {exam}")
        print(f"Resolved site (prefix): {site}")
        print(f"Found at site: {found}")


def test_exam_at_site_returns_site_prefix_not_departments():
    """
    Regression test to ensure exam_at_site returns a LOCATION PREFIX,
    not a list of departments.
    """

    found, exam, site = exam_at_site("CT HEAD", "1176 5th ave")

    # We don't assert found == True because datasets can change.
    # We assert STRUCTURE, not content.
    assert site is None or isinstance(site, str)
    assert not isinstance(site, list)


def test_exam_at_site_handles_unknown_site():
    """
    Ensure unknown locations fail gracefully.
    """

    found, exam, site = exam_at_site("CT HEAD", "definitely not a real location")

    assert found is False
    assert site is None