"""
HormoScope — Kaggle PCOS Dataset Ingestion
Pipeline: data/raw → PostgreSQL (hormoscope database)
Loads both CSV and XLSX files, cleans columns, inserts into raw tables
"""

import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
import logging

# ── Logging setup ────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)

# ── Load environment variables ───────────────────────────────────
load_dotenv()

DB_HOST     = os.getenv("DB_HOST", "localhost")
DB_PORT     = os.getenv("DB_PORT", "5432")
DB_NAME     = os.getenv("DB_NAME", "hormoscope")
DB_USER     = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

# ── File paths ───────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
RAW_DIR  = os.path.join(BASE_DIR, "data", "raw")

CSV_FILE  = os.path.join(RAW_DIR, "PCOS_infertility.csv")
XLSX_FILE = os.path.join(RAW_DIR, "PCOS_data_without_infertility.xlsx")


# ── Helper: clean column names ───────────────────────────────────
def clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Lowercase, strip spaces, replace special chars with underscores."""
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(r"[^\w]", "_", regex=True)
        .str.replace(r"_+", "_", regex=True)
        .str.strip("_")
    )
    return df


# ── Load CSV ─────────────────────────────────────────────────────
def load_csv() -> pd.DataFrame:
    log.info(f"Reading CSV: {CSV_FILE}")
    df = pd.read_csv(CSV_FILE)
    df = clean_columns(df)
    df["source"] = "kaggle_infertility"
    log.info(f"CSV loaded — {len(df)} rows, {len(df.columns)} columns")
    return df


# ── Load XLSX ────────────────────────────────────────────────────
def load_xlsx() -> pd.DataFrame:
    log.info(f"Reading XLSX: {XLSX_FILE}")
    xl = pd.ExcelFile(XLSX_FILE)
    log.info(f"Sheets found: {xl.sheet_names}")
    df = pd.read_excel(XLSX_FILE, sheet_name="Full_new")
    df = clean_columns(df)
    df["source"] = "kaggle_no_infertility"
    log.info(f"XLSX loaded — {len(df)} rows, {len(df.columns)} columns")
    return df


# ── Write to PostgreSQL ──────────────────────────────────────────
def create_raw_table(engine, df: pd.DataFrame, table_name: str):
    log.info(f"Writing to table: {table_name}")
    df.to_sql(
        name=table_name,
        con=engine,
        schema="public",
        if_exists="replace",
        index=False,
        method="multi",
        chunksize=500
    )
    log.info(f"Table '{table_name}' written successfully")


# ── Data quality checks ──────────────────────────────────────────
def run_quality_checks(engine, table_name: str, expected_min_rows: int):
    log.info(f"Running quality checks on '{table_name}'")
    with engine.connect() as conn:
        row_count = conn.execute(
            text(f"SELECT COUNT(*) FROM public.{table_name}")
        ).scalar()
        assert row_count >= expected_min_rows, \
            f"Row count {row_count} below expected {expected_min_rows}"
        log.info(f"  Row count: {row_count} — passed")
    log.info("Quality checks passed")


# ── Main ─────────────────────────────────────────────────────────
def main():
    log.info("=" * 50)
    log.info("HormoScope — PCOS Kaggle Ingestion Pipeline")
    log.info("=" * 50)

    conn_str = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(conn_str)
    log.info(f"Connected to: {DB_HOST}:{DB_PORT}/{DB_NAME}")

    # CSV
    df_csv = load_csv()
    create_raw_table(engine, df_csv, "raw_pcos_infertility")
    run_quality_checks(engine, "raw_pcos_infertility", expected_min_rows=500)

    # XLSX
    df_xlsx = load_xlsx()
    create_raw_table(engine, df_xlsx, "raw_pcos_no_infertility")
    run_quality_checks(engine, "raw_pcos_no_infertility", expected_min_rows=10)

    log.info("\nColumn preview — CSV:")
    log.info(list(df_csv.columns))
    log.info("\nColumn preview — XLSX:")
    log.info(list(df_xlsx.columns))

    log.info("\nIngestion complete — both datasets in PostgreSQL")
    engine.dispose()


if __name__ == "__main__":
    main()
