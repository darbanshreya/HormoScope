# 🔭 HormoScope
### *Not the stars. Your hormones.*

> A personal data project built on real PMOS data — tracking hormones, cycles, sleep, and metabolic markers to surface patterns that most people (and doctors) miss.

Built by a PMOS patient. Powered by data engineering, analytics, machine learning, and AI.

---

## 📌 Context

On **May 12, 2026**, PCOS (Polycystic Ovary Syndrome) was officially renamed to **PMOS — Polyendocrine Metabolic Ovarian Syndrome** following a landmark global consensus study published in *The Lancet*. The rename recognises what patients have long known: this is not just a reproductive condition. It is a complex, multisystem condition spanning endocrine, metabolic, dermatological, and psychological health.

HormoScope is built around this expanded understanding.

---

## 🎯 Project Goals

| Goal | Description |
|------|-------------|
| **Personal** | Make sense of my own PMOS data across 3 years of cycle tracking, bloodwork, and symptoms |
| **Technical** | Demonstrate end-to-end data skills: engineering → analysis → ML → AI |
| **Clinical** | Surface patterns that are actionable in a doctor's appointment |
| **Timely** | Build with the PMOS framing, not the outdated PCOS lens |

---

## 🗂️ Project Structure

```
HormoScope/
│
├── data/
│   ├── raw/                        # Original uploads: CSVs, PDFs, images
│   │   ├── cycle_tracking/         # Cycle logs (June 2023 – May 2026)
│   │   ├── bloodwork/              # CBC, lipids, HbA1c, insulin, thyroid
│   │   ├── ultrasounds/            # Pelvic ultrasound reports (May + Dec 2025)
│   │   └── skin_photos/            # Labeled skin photos for breakout tracking
│   ├── processed/                  # Cleaned, transformed data
│   └── synthetic/                  # CTGAN-generated augmented data
│
├── pipeline/
│   ├── ingestion/                  # Scripts to load raw data into warehouse
│   ├── dbt/                        # dbt models: staging → intermediate → mart
│   │   ├── staging/
│   │   ├── intermediate/
│   │   └── mart/
│   └── airflow/                    # DAGs for scheduled pipeline runs
│       └── dags/
│
├── database/
│   ├── schema.sql                  # Full warehouse schema
│   └── migrations/                 # Version-controlled schema changes
│
├── notebooks/
│   ├── 01_eda_cycle.ipynb          # Exploratory analysis: cycle patterns
│   ├── 02_eda_bloodwork.ipynb      # Bloodwork deep dive + PMOS markers
│   ├── 03_eda_crossref.ipynb       # Cross-referencing cycle + labs + sleep
│   └── 04_pmos_nlp.ipynb           # NLP: PCOS → PMOS literature shift
│
├── ml/
│   ├── feature_engineering.py      # HOMA-IR, LH:FSH ratio, androgenic index
│   ├── risk_model.py               # XGBoost PMOS risk classifier
│   ├── clustering.py               # Phenotype clustering (K-Means / DBSCAN)
│   ├── cycle_forecast.py           # Time-series: menstrual irregularity
│   └── shap_explainability.py      # SHAP values for clinical interpretability
│
├── ai/
│   ├── system_prompt.md            # HormoScope AI analyst prompt
│   ├── rag_pipeline.py             # RAG: PMOS literature + FAISS index
│   ├── chatbot.py                  # LangChain-powered PMOS Q&A chatbot
│   └── recommendations.py          # Personalised lifestyle suggestion engine
│
├── app/
│   ├── main.py                     # Streamlit app entry point
│   ├── pages/
│   │   ├── 01_dashboard.py         # Main cycle + hormone dashboard
│   │   ├── 02_checkin.py           # Daily check-in (energy, mood, skin)
│   │   ├── 03_patterns.py          # Pattern report (data + research + action)
│   │   ├── 04_risk_score.py        # Upload labs → get PMOS risk score
│   │   └── 05_doctor_prep.py       # Doctor appointment summary generator
│   └── utils/
│
├── tests/
│   ├── test_pipeline.py
│   ├── test_models.py
│   └── test_data_quality.py
│
├── docs/
│   ├── data_dictionary.md          # Every field, every table, explained
│   ├── schema_diagram.png
│   └── research_references.md      # All studies cited in pattern outputs
│
├── .github/
│   └── workflows/
│       └── ci.yml                  # GitHub Actions: lint + test on push
│
├── docker-compose.yml              # Spin up PostgreSQL + Airflow locally
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🗄️ Database Schema

### Core Tables

```sql
-- Cycle events
CREATE TABLE fact_cycle_day (
    id              SERIAL PRIMARY KEY,
    date            DATE NOT NULL,
    cycle_day       INT,
    phase           VARCHAR(20),    -- follicular / ovulation / luteal / menstrual
    period_active   BOOLEAN,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- Daily check-in log
CREATE TABLE fact_daily_checkin (
    id              SERIAL PRIMARY KEY,
    date            DATE NOT NULL,
    cycle_day       INT,
    energy_score    INT CHECK (energy_score BETWEEN 1 AND 10),
    mood            VARCHAR(50),
    skin_status     VARCHAR(20),    -- clear / okay / breaking_out
    notes           TEXT,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- Bloodwork results
CREATE TABLE fact_bloodwork (
    id              SERIAL PRIMARY KEY,
    test_date       DATE NOT NULL,
    marker          VARCHAR(100),   -- e.g. HbA1c, LH, FSH, AMH, ferritin
    value           DECIMAL(10,3),
    unit            VARCHAR(20),
    reference_low   DECIMAL(10,3),
    reference_high  DECIMAL(10,3),
    flag            VARCHAR(10),    -- normal / low / high / critical
    notes           TEXT
);

-- Derived PMOS markers (feature engineering output)
CREATE TABLE mart_pmos_markers (
    id              SERIAL PRIMARY KEY,
    date            DATE NOT NULL,
    lh_fsh_ratio    DECIMAL(6,3),   -- LH divided by FSH
    homa_ir         DECIMAL(6,3),   -- insulin resistance proxy
    free_androgen_index DECIMAL(6,3),
    amh_level       DECIMAL(6,3),
    metabolic_risk  VARCHAR(10)     -- low / moderate / high
);

-- Skin log
CREATE TABLE fact_skin_log (
    id              SERIAL PRIMARY KEY,
    date            DATE NOT NULL,
    cycle_day       INT,
    location        VARCHAR(50),    -- chin / forehead / cheeks / jawline
    severity        VARCHAR(10),    -- clear / mild / moderate / severe
    photo_path      TEXT,
    notes           TEXT
);

-- Sleep & recovery
CREATE TABLE fact_sleep_log (
    id              SERIAL PRIMARY KEY,
    date            DATE NOT NULL,
    sleep_duration  DECIMAL(4,2),   -- hours
    hrv             INT,            -- ms
    recovery_score  INT,
    deep_sleep_pct  DECIMAL(4,2),
    source          VARCHAR(20)     -- oura / apple_watch / manual
);
```

---

## 🧰 Tech Stack

| Layer | Tools |
|-------|-------|
| **Language** | Python 3.11, SQL |
| **Data Engineering** | Apache Airflow, dbt, Great Expectations |
| **Database** | PostgreSQL (local), BigQuery (cloud) |
| **Containerisation** | Docker, docker-compose |
| **Analysis** | pandas, numpy, matplotlib, seaborn, plotly |
| **NLP** | spaCy, NLTK, BERTopic |
| **ML** | scikit-learn, XGBoost, LightGBM, Prophet |
| **Explainability** | SHAP, LIME |
| **Experiment Tracking** | MLflow |
| **Synthetic Data** | CTGAN, SDV |
| **AI / LLM** | Anthropic API, LangChain, FAISS, sentence-transformers |
| **App** | Streamlit |
| **CI/CD** | GitHub Actions |
| **Version Control** | Git + GitHub |

---

## 📊 Data Sources

| Source | Type | Coverage | Notes |
|--------|------|----------|-------|
| Personal cycle tracker | CSV | 3 years | Exported from tracking app |
| Bloodwork (Year 1) | PDF | CBC, lipids, HbA1c, fasting insulin, liver | |
| Thyroid panel (Year 2) | PDF | TSH, T3, T4 | |
| Pelvic ultrasounds | PDF | Two time points | |
| Skin photos | Images | Labeled by date | |
| PubMed / Lancet | Text | 2015–2026 | For NLP + RAG pipeline |
| NHANES | CSV | Public | Metabolic benchmarking |
| Synthetic (CTGAN) | CSV | Generated | Class balancing for ML |

---

## 🚀 Development Phases

### Phase 1 — Data Engineering *(Week 1–2)*
- [ ] Set up PostgreSQL + dbt + Airflow via Docker
- [ ] Ingest and clean all personal data sources
- [ ] Build dbt models: staging → mart
- [ ] Add Great Expectations data quality checks
- [ ] Generate synthetic data with CTGAN

### Phase 2 — Data Analysis *(Week 3–4)*
- [ ] EDA notebooks: cycle, bloodwork, cross-reference
- [ ] Correlation analysis: hormones × symptoms × sleep
- [ ] NLP on PCOS → PMOS literature
- [ ] Build Streamlit dashboard (Phase 2 version)

### Phase 3 — ML & Data Science *(Week 5–6)*
- [ ] Feature engineering: HOMA-IR, LH:FSH, free androgen index
- [ ] PMOS risk classification model (XGBoost)
- [ ] Phenotype clustering
- [ ] Cycle irregularity forecasting (Prophet)
- [ ] SHAP explainability layer
- [ ] MLflow experiment tracking

### Phase 4 — AI Layer *(Week 7–8)*
- [ ] RAG pipeline over PMOS literature (LangChain + FAISS)
- [ ] Daily check-in chatbot
- [ ] Doctor prep summary generator (Anthropic API)
- [ ] Final Streamlit app: all pages integrated
- [ ] Deploy to Streamlit Cloud

---

## 🔑 Key PMOS Markers Tracked

| Marker | Why It Matters |
|--------|----------------|
| LH / FSH ratio | Hormonal imbalance indicator |
| AMH | Ovarian reserve, elevated in PMOS |
| Fasting insulin + HOMA-IR | Insulin resistance — core to PMOS metabolic axis |
| HbA1c | Long-term blood sugar — pre-diabetic range flagged |
| Testosterone / DHEAS | Androgen excess — drives skin + hair symptoms |
| SHBG | Low = more free androgens circulating |
| Ferritin | Often missed; explains fatigue + anemia patterns |
| ESR | Inflammatory marker — elevated (76) in current labs |
| TSH / T3 / T4 | Thyroid — commonly co-occurring with PMOS |
| Vitamin D | Deficiency common; affects insulin sensitivity |

---

## 📎 Disclaimer

HormoScope is a personal data project for educational and portfolio purposes.
It is **not** a medical device, diagnostic tool, or clinical product.
All patterns are observational. Nothing here replaces a doctor's advice.
Always consult a qualified healthcare provider for medical decisions.

---

## 👩‍💻 About

Built by a data professional and PMOS patient.
*Because the data in my body deserved the same rigour I bring to work.*
