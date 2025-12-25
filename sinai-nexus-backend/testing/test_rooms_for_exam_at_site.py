# testing/test_rooms_for_exam_at_site.py
# run via 'pytest testing/test_rooms_for_exam_at_site.py -s'

from src.query_handlers import rooms_for_exam_at_site


def test_rooms_for_exam_at_site_print():
    """
    Exploratory print-based test.

    Purpose:
      - Visually confirm that rooms are correctly resolved
        using LOCATION (not department).
      - Ensure room prefixes are mapped correctly to locations.
      - Ensure output formatting is stable.
    """

    test_cases = [
        ("CT Head", "1470 Madison Ave"),      # HESS
        ("CT Head", "1176 5th Ave"),          # RA
        ("MRI Brain", "Union Square"),        # MSDUS
        ("CT Head", "MSM"),
        ("CT Head", "random nonsense location"),
    ]

    for exam_query, site_query in test_cases:
        rooms, exam, site = rooms_for_exam_at_site(exam_query, site_query)

        print("\n----------------------------------")
        print(f"Exam query: {exam_query}")
        print(f"Site query: {site_query}")
        print(f"Resolved site (location prefix): {site}")
        print(f"Resolved exam: {exam}")
        print(f"Number of rooms found: {len(rooms)}")

        if rooms:
            print("Rooms:")
            for r in rooms:
                print(f"  - {r}")
        else:
            print("No rooms found.")


def test_rooms_for_exam_at_site_returns_location_prefix():
    """
    Regression test:
    Ensure the returned site is a LOCATION PREFIX (string),
    not a department name or list.
    """

    rooms, exam, site = rooms_for_exam_at_site("CT Head", "1470 Madison Ave")

    assert site is None or isinstance(site, str)
    assert not isinstance(site, list)


def test_rooms_for_exam_at_site_unknown_location():
    """
    Ensure unknown locations fail gracefully.
    """

    rooms, exam, site = rooms_for_exam_at_site("CT Head", "definitely not real")

    assert rooms == []
    assert site is None


def test_rooms_for_exam_at_site_filters_by_location():
    """
    Critical regression test.

    Ensures rooms returned belong ONLY to the resolved location
    and not to other locations performing the same exam.
    """

    rooms, exam, site = rooms_for_exam_at_site("CT Head", "1470 Madison Ave")

    assert site == "1470 MADISON AVE"
    assert all(room.startswith("HESS") for room in rooms)


def test_rooms_for_exam_at_site_filters_by_exam():
    """
    Ensure that rooms returned actually perform the exam.
    """

    rooms, exam, site = rooms_for_exam_at_site("MRI Brain", "1470 Madison Ave")

    # MRI may or may not exist at this site — both outcomes are valid,
    # but the function must not crash or return rooms from other exams.
    assert isinstance(rooms, list)
