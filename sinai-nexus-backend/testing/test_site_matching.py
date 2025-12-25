# testing/test_site_matching.py

from src.fuzzy_matchers import best_site_match

def test_best_site_match_print():
    """
    This test is intentionally simple and print-based.
    It helps us visually inspect what best_site_match()
    returns after the refactor.
    """

    test_queries = [
        "1176 5th ave",
        "1176 fifth avenue",
        "1176 5th ave mri",
        "union square",
        "10 union sq e",
        "1470 madison ave",
        "hess",
        "chelsea",
        "msm",
        "random nonsense text"
    ]

    for query in test_queries:
        result = best_site_match(query)

        print("\n----------------------------------")
        print(f"User query: {query}")
        print("Result:")

        if result is None:
            print("  None (no confident match)")
        else:
            for dep in result:
                print(f"  - {dep}")

test_best_site_match_print()