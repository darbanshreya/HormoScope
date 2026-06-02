CREATE TABLE fact_cycle_day (
    id              SERIAL PRIMARY KEY,
    date            DATE NOT NULL,
    cycle_day       INT,
    phase           VARCHAR(20),
    period_active   BOOLEAN,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE fact_daily_checkin (
    id              SERIAL PRIMARY KEY,
    date            DATE NOT NULL,
    cycle_day       INT,
    energy_score    INT CHECK (energy_score BETWEEN 1 AND 10),
    mood            VARCHAR(50),
    skin_status     VARCHAR(20),
    notes           TEXT,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE fact_bloodwork (
    id              SERIAL PRIMARY KEY,
    test_date       DATE NOT NULL,
    marker          VARCHAR(100),
    value           DECIMAL(10,3),
    unit            VARCHAR(20),
    reference_low   DECIMAL(10,3),
    reference_high  DECIMAL(10,3),
    flag            VARCHAR(10),
    notes           TEXT
);

CREATE TABLE fact_skin_log (
    id              SERIAL PRIMARY KEY,
    date            DATE NOT NULL,
    cycle_day       INT,
    location        VARCHAR(50),
    severity        VARCHAR(10),
    photo_path      TEXT,
    notes           TEXT
);

CREATE TABLE fact_sleep_log (
    id              SERIAL PRIMARY KEY,
    date            DATE NOT NULL,
    sleep_duration  DECIMAL(4,2),
    hrv             INT,
    recovery_score  INT,
    deep_sleep_pct  DECIMAL(4,2),
    source          VARCHAR(20)
);

CREATE TABLE mart_pmos_markers (
    id                  SERIAL PRIMARY KEY,
    date                DATE NOT NULL,
    lh_fsh_ratio        DECIMAL(6,3),
    homa_ir             DECIMAL(6,3),
    free_androgen_index DECIMAL(6,3),
    amh_level           DECIMAL(6,3),
    metabolic_risk      VARCHAR(10)
);