from src.data_loader import LOCATION_TO_DEPARTMENTS

for prefix, deps in LOCATION_TO_DEPARTMENTS.items():
    print(f"\nLocation prefix: {prefix}")
    for d in deps:
        print(f"  - {d}")