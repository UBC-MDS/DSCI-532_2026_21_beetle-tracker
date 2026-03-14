"""
prep_data.py  –  One-time ETL: convert raw CSV to Parquet.

Run once from the project root:
    python src/prep_data.py

Output: data/processed/gbif-beetle.parquet
"""

import os
import duckdb

RAW_CSV = os.path.join(
    os.path.dirname(__file__), "..", "data", "raw", "gbif-beetle.csv"
)
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
OUT_FILE = os.path.join(OUT_DIR, "gbif-beetle.parquet")

os.makedirs(OUT_DIR, exist_ok=True)

# read_csv_auto infers headers and column types; delim='\t' matches the raw file's
# tab separator.  The COPY … TO … statement writes a single compressed Parquet file.
duckdb.execute(
    f"""
    COPY (
        SELECT *
        FROM read_csv_auto('{RAW_CSV}', delim='\t', header=true)
    )
    TO '{OUT_FILE}' (FORMAT PARQUET)
"""
)

print(f"Done. Parquet written to: {OUT_FILE}")
