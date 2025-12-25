# testing/test_exams_at_site.py

# test the functionality of exams_at_site
# run via 'pytest testing/test_exams_at_site.py -s'

from src.query_handlers import exams_at_site


def test_exams_at_site_print():
    """
    Print-based exploratory test for exams_at_site.

    This test helps visually confirm:
      - Site resolution works with fuzzy input
      - The returned site is a LOCATION PREFIX
      - Exams are aggregated across all departments at the location
    """

    test_queries = [
        "1176 5th ave",
        "1176 fifth avenue",
        "union square",
        "hess",
        "msm",
        "random nonsense location"
    ]

    for site_query in test_queries:
        exams, site = exams_at_site(site_query)

        print("\n----------------------------------")
        print(f"User site query: {site_query}")
        print(f"Resolved site (prefix): {site}")
        print(f"Number of exams found: {len(exams)}")

        if exams:
            print("Sample exams:")
            for e in exams[:5]:  # only print a few to keep output readable
                print(f"  - {e}")
        else:
            print("No exams found.")


def test_exams_at_site_returns_prefix_not_departments():
    """
    Regression test:
    Ensure the returned site is a STRING prefix, not a list of departments.
    """

    exams, site = exams_at_site("1176 5th ave")

    assert site is None or isinstance(site, str)
    assert not isinstance(site, list)
    assert isinstance(exams, list)


def test_exams_at_site_unknown_site():
    """
    Ensure unknown locations fail gracefully.
    """

    exams, site = exams_at_site("definitely not a real location")

    assert exams == []
    assert site is None


def test_exams_at_site_multi_department_location():
    """
    Ensure a multi-department location returns more than zero exams.
    This guards against accidentally collapsing to a single department.
    """

    exams, site = exams_at_site("1176 5th ave")

    assert site is not None
    assert isinstance(exams, list)
    assert len(exams) > 0
