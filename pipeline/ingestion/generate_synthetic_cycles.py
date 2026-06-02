"""
HormoScope — Synthetic Cycle Data Generator
Generates realistic PMOS-pattern cycle and daily check-in data
Inserts into: fact_cycle_day, fact_daily_checkin
"""

import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from datetime import date, timedelta
import random
import os
import logging

# ── Logging ──────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)

# ── Load env ─────────────────────────────────────────────────────
load_dotenv()
DB_HOST     = os.getenv("DB_HOST", "localhost")
DB_PORT     = os.getenv("DB_PORT", "5432")
DB_NAME     = os.getenv("DB_NAME", "hormoscope")
DB_USER     = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

# ── Config ───────────────────────────────────────────────────────
START_DATE    = date(2023, 6, 1)
END_DATE      = date(2026, 5, 30)
RANDOM_SEED   = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

# PMOS cycle patterns — irregular cycles (32–45 days typical)
CYCLE_LENGTH_MEAN = 38
CYCLE_LENGTH_STD  = 6
CYCLE_LENGTH_MIN  = 26
CYCLE_LENGTH_MAX  = 60
PERIOD_LENGTH_MEAN = 6
PERIOD_LENGTH_STD  = 1.5


# ── Phase assignment ─────────────────────────────────────────────
def get_phase(cycle_day: int, cycle_length: int, period_length: int) -> str:
    if cycle_day <= period_length:
        return "menstrual"
    elif cycle_day <= int(cycle_length * 0.4):
        return "follicular"
    elif cycle_day <= int(cycle_length * 0.55):
        return "ovulation"
    else:
        return "luteal"


# ── Energy score by phase (PMOS pattern) ─────────────────────────
def get_energy(phase: str) -> int:
    profiles = {
        "menstrual":  (4, 1.5),   # low energy, cramping
        "follicular": (7, 1.2),   # rising energy
        "ovulation":  (8, 1.0),   # peak energy
        "luteal":     (5, 1.8),   # drops post-ovulation — PMOS pattern
    }
    mean, std = profiles[phase]
    return int(np.clip(np.random.normal(mean, std), 1, 10))


# ── Mood by phase ─────────────────────────────────────────────────
def get_mood(phase: str) -> str:
    moods = {
        "menstrual":  ["tired", "low", "crampy", "quiet", "heavy"],
        "follicular": ["motivated", "clear", "hopeful", "focused", "good"],
        "ovulation":  ["energetic", "confident", "social", "sharp", "great"],
        "luteal":     ["anxious", "irritable", "foggy", "bloated", "flat"],
    }
    return random.choice(moods[phase])


# ── Skin status by phase ──────────────────────────────────────────
def get_skin(phase: str, cycle_day: int, cycle_length: int) -> str:
    # PMOS: breakouts cluster 10-14 days before period (progesterone driven)
    days_before_period = cycle_length - cycle_day
    if days_before_period <= 14 and days_before_period >= 8:
        return random.choices(
            ["breaking_out", "okay"], weights=[0.65, 0.35]
        )[0]
    elif phase == "follicular" or phase == "ovulation":
        return random.choices(
            ["clear", "okay"], weights=[0.70, 0.30]
        )[0]
    else:
        return random.choices(
            ["okay", "breaking_out", "clear"], weights=[0.50, 0.30, 0.20]
        )[0]


# ── Notes generator ──────────────────────────────────────────────
def get_notes(phase: str, energy: int) -> str:
    luteal_notes = [
        "bloated today", "craving sugar", "headache in the evening",
        "really tired after lunch", "brain fog all day",
        "lower back ache", "craving carbs", "mood dip around 3pm"
    ]
    menstrual_notes = [
        "cramps today", "heavy flow", "light flow", "heating pad helping",
        "feeling drained", "skipped gym today"
    ]
    follicular_notes = [
        "feeling good", "productive day", "good workout",
        "clear skin today", "slept well"
    ]
    ovulation_notes = [
        "best energy this week", "really focused",
        "slight twinge on left side", "social and talkative"
    ]
    generic = ["", "", "", ""]  # empty notes some days

    pool = {
        "luteal": luteal_notes,
        "menstrual": menstrual_notes,
        "follicular": follicular_notes + generic,
        "ovulation": ovulation_notes + generic,
    }
    return random.choice(pool.get(phase, generic))


# ── Generate all cycle days ───────────────────────────────────────
def generate_cycles():
    cycle_days_rows    = []
    daily_checkin_rows = []

    current_date  = START_DATE
    cycle_number  = 1

    while current_date <= END_DATE:
        # Random cycle length for this cycle (PMOS = irregular)
        cycle_length  = int(np.clip(
            np.random.normal(CYCLE_LENGTH_MEAN, CYCLE_LENGTH_STD),
            CYCLE_LENGTH_MIN, CYCLE_LENGTH_MAX
        ))
        period_length = int(np.clip(
            np.random.normal(PERIOD_LENGTH_MEAN, PERIOD_LENGTH_STD),
            3, 10
        ))

        log.info(f"Cycle {cycle_number}: {current_date} — length {cycle_length} days")

        for cycle_day in range(1, cycle_length + 1):
            if current_date > END_DATE:
                break

            phase  = get_phase(cycle_day, cycle_length, period_length)
            energy = get_energy(phase)
            mood   = get_mood(phase)
            skin   = get_skin(phase, cycle_day, cycle_length)
            notes  = get_notes(phase, energy)

            cycle_days_rows.append({
                "date":          current_date,
                "cycle_day":     cycle_day,
                "phase":         phase,
                "period_active": cycle_day <= period_length,
                "cycle_number":  cycle_number,
                "cycle_length":  cycle_length,
            })

            daily_checkin_rows.append({
                "date":         current_date,
                "cycle_day":    cycle_day,
                "energy_score": energy,
                "mood":         mood,
                "skin_status":  skin,
                "notes":        notes if notes else None,
            })

            current_date += timedelta(days=1)

        cycle_number += 1

    return pd.DataFrame(cycle_days_rows), pd.DataFrame(daily_checkin_rows)


# ── Insert into PostgreSQL ────────────────────────────────────────
def insert_data(engine, df_cycles: pd.DataFrame, df_checkins: pd.DataFrame):
    log.info("Writing fact_cycle_day...")
    df_cycles.to_sql(
        "fact_cycle_day", con=engine, schema="public",
        if_exists="replace", index=False, method="multi", chunksize=500
    )
    log.info(f"  {len(df_cycles)} rows written")

    log.info("Writing fact_daily_checkin...")
    df_checkins.to_sql(
        "fact_daily_checkin", con=engine, schema="public",
        if_exists="replace", index=False, method="multi", chunksize=500
    )
    log.info(f"  {len(df_checkins)} rows written")


# ── Summary stats ─────────────────────────────────────────────────
def print_summary(df_cycles: pd.DataFrame, df_checkins: pd.DataFrame):
    log.info("\n── Summary ─────────────────────────────────────")
    log.info(f"Total days generated : {len(df_cycles)}")
    log.info(f"Total cycles         : {df_cycles['cycle_number'].max()}")
    log.info(f"Avg cycle length     : {df_cycles.groupby('cycle_number')['cycle_day'].max().mean():.1f} days")
    log.info(f"Date range           : {df_cycles['date'].min()} → {df_cycles['date'].max()}")

    phase_dist = df_cycles["phase"].value_counts()
    log.info(f"\nPhase distribution:\n{phase_dist.to_string()}")

    avg_energy = df_checkins.groupby(
        df_cycles["phase"]
    )["energy_score"].mean().round(2)
    log.info(f"\nAvg energy by phase:\n{avg_energy.to_string()}")

    skin_dist = df_checkins["skin_status"].value_counts()
    log.info(f"\nSkin status distribution:\n{skin_dist.to_string()}")


# ── Main ─────────────────────────────────────────────────────────
def main():
    log.info("=" * 50)
    log.info("HormoScope — Synthetic Cycle Data Generator")
    log.info("=" * 50)

    conn_str = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine   = create_engine(conn_str)
    log.info(f"Connected to: {DB_HOST}:{DB_PORT}/{DB_NAME}")

    df_cycles, df_checkins = generate_cycles()
    print_summary(df_cycles, df_checkins)
    insert_data(engine, df_cycles, df_checkins)

    log.info("\nSynthetic data generation complete!")
    engine.dispose()


if __name__ == "__main__":
    main()
