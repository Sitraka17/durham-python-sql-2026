# Advanced Python and SQL for Applied Economic & Financial Analysis

**Durham University Business School — MSc Economics**
Sitraka Forler · 15–16 June 2026

---

## The central question

> *"Did the Fed's tightening cycle work?"*
>
> In March 2022 the Fed began the most aggressive rate hike cycle since 1979.
> 11 hikes, 525 basis points, 16 months.
> By the end of Day 2 you will have built the data infrastructure to answer this
> empirically — and defend your answer.

---

## Get started in 30 seconds — GitHub Codespaces (recommended)

No install, runs in your browser. Click:

**→ https://codespaces.new/Sitraka17/durham-python-sql-2026**

The container automatically installs dependencies, downloads the bundled data
(`--no-api`, no key needed) and builds `db/macro.db`. When the terminal is
ready, verify with:

```bash
python scripts/utils.py     # should print non-zero row counts for 4 tables
```

Then open any `sql/*.sql` or `scripts/*.py` and run it. The **SQLite Viewer**,
**Python** and **Jupyter** extensions are pre-installed.

---

## Local setup (fallback — VS Code on your own machine)

```bash
# 1. Clone
git clone https://github.com/Sitraka17/durham-python-sql-2026.git
cd durham-python-sql-2026

# 2. Virtual environment  (Python 3.11+)
python -m venv .venv
source .venv/bin/activate      # Mac/Linux
# .venv\Scripts\activate       # Windows PowerShell

# 3. Install
pip install -r requirements.txt

# 4. Build data + database  (uses the bundled CSVs — NO API key required)
cp .env.example .env
python datasets/download.py --no-api
python scripts/setup_db.py

# 5. Verify
python scripts/utils.py
```

One-shot alternative (Mac/Linux): `bash setup.sh`, or `make all`.

> **FRED API key is optional.** Everything works offline from the bundled
> `datasets/*_static.csv`. To pull *live* data instead, get a free key at
> <https://fred.stlouisfed.org/docs/api/api_key.html>, put it in `.env`
> (`FRED_KEY=...`), and run `python datasets/download.py` (without `--no-api`).

---

## Repository structure

```
durham-python-sql-2026/
│
├── .devcontainer/devcontainer.json   One-click GitHub Codespaces environment
├── .github/workflows/ci.yml          CI: builds the DB + runs all checks on push
│
├── datasets/
│   ├── download.py                   Fetch WDI/FRED/OECD (--no-api uses bundles)
│   ├── _build_static_csvs.py         (instructor) how the bundled CSVs were built
│   ├── wdi_indicators.csv            World Bank WDI — 40 countries, 1990–2024
│   ├── fred_rates_static.csv         FRED monthly series + derived indicators
│   └── oecd_unemployment_static.csv  OECD/FRED harmonised quarterly unemployment
│
├── sql/
│   ├── 01_schema.sql                 CREATE TABLE statements
│   ├── 02_core_sql.sql               Block 1 — SELECT, GROUP BY, HAVING, CASE WHEN
│   ├── 03_joins_ctes.sql             Block 2 — JOINs, subqueries, CTEs
│   ├── 04_window_functions.sql       Block 3 — LAG, RANK, moving averages, yield curve
│   ├── 05_financial_analysis.sql     Finance — Fisher, Taylor Rule, credit spreads
│   └── 06_etl_queries.sql            Block 5 — SQL run inside the Python pipeline
│
├── scripts/
│   ├── utils.py                      Shared: singleton engine, paths, logging
│   ├── setup_db.py                   Build macro.db + 4 analytical views
│   ├── fetch_fred.py                 FRED download + derived indicators (Block 4)
│   ├── financial_indicators.py       Five-panel macro dashboard
│   ├── pipeline.py                   Block 5 ETL (extract→transform→load→query→chart)
│   └── concepts.py                   Runnable Fisher / Taylor / yield-curve / credit demos
│
├── notebooks/                        Concept-first, step-by-step Python scripts
│   ├── block4_python_apis.py
│   └── block5_etl_pipeline.py
│
├── exercises/
│   ├── day1_sql.sql                  Scaffolded SQL with ??? blanks (answers inline)
│   └── day2_python.py                Python exercises with a check() verifier
│
├── capstone/
│   ├── track_a/analysis.py           UK labour market + sacrifice ratio
│   ├── track_b/analysis.py           International spillovers + dollar-dominance index
│   └── track_c/analysis.py           Yield-curve episodes + recession prediction
│
├── solutions/                        Model answers (added after the course)
├── db/                               Generated SQLite database (git-ignored)
├── outputs/                          Generated charts and CSVs (git-ignored)
│
├── requirements.txt
├── .env.example
├── Makefile
├── setup.sh
└── durham.code-workspace             VS Code workspace with recommended extensions
```

---

## Day-by-day guide

| Day | Block | Time | File to open | Central question |
|-----|-------|------|--------------|------------------|
| 1 | B1 | 09:00–10:00 | `sql/02_core_sql.sql` | What kind of inflation was the 2022 surge? |
| 1 | B2 | 10:15–11:45 | `sql/03_joins_ctes.sql` | How did tightening propagate globally? |
| 1 | B3 | 13:00–14:30 | `sql/04_window_functions.sql` + `sql/05_financial_analysis.sql` | What did the yield curve signal? |
| 2 | B4 | 09:00–10:30 | `notebooks/block4_python_apis.py` + `scripts/fetch_fred.py` | What does the labour market tell us? |
| 2 | B5 | 10:45–12:15 | `notebooks/block5_etl_pipeline.py` + `scripts/pipeline.py` | Can we automate this monitoring? |
| 2 | B6 | 13:00–14:30 | `capstone/track_[a\|b\|c]/analysis.py` | What would you recommend to the MPC? |

Practice as you go: `exercises/day1_sql.sql` (Day 1) and `exercises/day2_python.py`
(Day 2). Run `python scripts/concepts.py` for runnable demos of every key concept.

---

## Data sources (all open-access)

| Source | Series | Used in |
|--------|--------|---------|
| [FRED](https://fred.stlouisfed.org) | FEDFUNDS, GS2/10/30, CPIAUCSL, PCEPILFE, M2SL, MORTGAGE30US, UNRATE, WALCL, BAML OAS | Blocks 3–6 |
| [World Bank WDI](https://data.worldbank.org) | GDP per capita, inflation, unemployment, fiscal balance, current account | Blocks 1–2 |
| [OECD](https://stats.oecd.org) (via FRED) | Harmonised quarterly unemployment, 12 economies | Block 3 |

### Offline by default — data provenance

The repo **ships with real, bundled data** so everything works with **zero API
keys**. The bundles were produced by `datasets/_build_static_csvs.py` from public,
key-less endpoints (FRED `fredgraph.csv` + the World Bank REST API) and reproduce
the verified facts of the cycle (Fed funds peak 5.33%, CPI YoY peak ~9%, the
10y–2y inversion of 2022–24, etc.).

> **Note on credit spreads.** FRED only exposes ~3 years of the *licensed* ICE
> BofA HY/IG OAS series on its public endpoint. The recent window therefore uses
> the real ICE OAS; pre-2023 history is reconstructed by rescaling the
> full-history Moody's Baa–10y credit spread (`BAA10Y`) to OAS levels over the
> overlap period. Both inputs are real FRED series — the historical tail is a
> real-spread reconstruction, not synthetic noise, and reproduces the GFC, COVID
> and 2022 stress episodes.

---

## Key financial indicators derived in code

| Indicator | Formula | FRED input |
|-----------|---------|------------|
| Real FFR (Fisher) | `fed_funds − cpi_yoy` | FEDFUNDS, CPIAUCSL |
| Taylor Rule rate | `π + 0.5 + 0.5(π−2) + 0.5·ỹ` | FEDFUNDS, CPIAUCSL, UNRATE |
| Taylor gap | `taylor_rule − fed_funds` | — |
| Yield spread | `GS10 − GS2` | GS10, GS2 |
| Mortgage spread | `MORTGAGE30US − GS10` | MORTGAGE30US, GS10 |
| M2 YoY growth | `M2SL.pct_change(12)×100` | M2SL |

These are computed in `datasets/download.py` / `scripts/fetch_fred.py` and exposed
through four SQL views built by `scripts/setup_db.py`:
`v_gdp_ranked`, `v_yield_curve`, `v_real_rates`, `v_credit_dashboard`.

---

## Makefile commands

```bash
make all        # venv + download + database (full setup)
make data       # download datasets only
make db         # build macro.db from CSVs
make pipeline   # run Block 5 end-to-end
make dashboard  # run financial_indicators.py (full 5-panel chart)
make clean      # remove generated DB and outputs
make test       # verify database row counts
```

---

## VS Code setup

Install these extensions (Ctrl+Shift+X) — pre-installed in Codespaces:

- **SQLite Viewer** (qwtel) — browse `.db` files directly
- **Python** (Microsoft) — linting, IntelliSense
- **Jupyter** (Microsoft) — run notebooks in VS Code

Open the workspace: **File → Open Workspace from File → `durham.code-workspace`**

---

## Instructor

**Sitraka Forler**
Systems Architect & Senior Data Scientist, POST Luxembourg ·
Lecturer, IAE Metz & Centrale Méditerranée (AMU) ·
[sitraka.forler@post.lu](mailto:sitraka.forler@post.lu) ·
[github.com/Sitraka17](https://github.com/Sitraka17)
