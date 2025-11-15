import pandas as pd
from sqlalchemy import create_engine
import os


excel_path = "data/locations/All Exams & locations.xlsx"
DB_PATH = "db/locations.db"

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

df = pd.read_excel(excel_path)

engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={'timeout': 30})


df.to_sql("locations", engine, if_exists="replace", index=False)

procedures_df = df.copy()

def summarize_row(row):
    return (
        f"Procedure: {row['EAP Name']}\n\n"
        f"Visit Type Name: {row['Visit Type Name']}\n\n"
        f"Length of Time for Procedure: {row['Visit Type Length']}\n\n"
        f"DEP Name: {row['DEP Name']}\n\n"
        f"Room Name: {row['Room Name']}."
    )

procedures_df["summary"] = procedures_df.apply(summarize_row, axis=1)

with engine.begin() as conn:
    procedures_df.to_sql("procedures", conn, if_exists="replace", index=False)
    print(f"Saved {len(procedures_df)} rows to 'procedures' table.")

engine.dispose()

