# Advanced Python and SQL for Applied Economic & Financial Analysis

**Durham University Business School — MSc Economics**
Sitraka Forler · 15–16 June 2026

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/Sitraka17/durham-python-sql-2026)

*(↑ Students: click this green button to start — no installation. See
[Start here](#-start-here--no-installation-no-experience-needed) below.)*

> ### The big question we answer this week
> **"Did the Fed's tightening cycle work?"**
> In March 2022 the US Federal Reserve began the most aggressive interest-rate
> hikes since 1979 — 525 basis points in 16 months. Over two days you'll use
> real economic data to investigate whether it worked, and learn Python and SQL
> by doing it.

---

## 🚀 Start here — no installation, no experience needed

**You do not need to be technical. You do not need to install anything.** The
whole course runs on a free cloud computer that opens **inside your web browser**
(Chrome, Edge, Firefox or Safari). Just follow these steps in order.

> ⏱️ Total time to get going: about **5 minutes**, most of it waiting.

### Step 1 — Get a free GitHub account *(skip if you already have one)*

1. Go to **https://github.com/signup**
2. Enter an email, password and username. Use your Durham email if you like.
3. Confirm the email GitHub sends you. That's it — GitHub is free.

*(GitHub is just the website that stores the course files. Think of it like a
Google Drive for code.)*

### Step 2 — Open the course (one click)

👉 **Click this link:**
**https://codespaces.new/Sitraka17/durham-python-sql-2026**

A page appears saying **“Set up your codespace”**. Click the green
**“Create codespace”** button.

*(A “codespace” is a private computer in the cloud, created just for you, with
Python, the data, and everything already set up. Nothing touches your own
laptop.)*

### Step 3 — Wait for it to build *(first time only: ~2–3 minutes)*

The screen turns into a code editor. **Leave the tab open and wait.** Behind the
scenes it is installing the tools and building the database for you.

> ⚠️ The **first** open takes a couple of minutes. After that, reopening takes
> only a few seconds.

### Step 4 — Know when it's ready

Look at the **bottom of the screen**: there's a black panel called the
**TERMINAL**. When it stops scrolling and shows a line ending in a `$` with a
blinking cursor, the setup is finished.

### Step 5 — Check everything is ready (copy → paste → Enter)

Click anywhere inside that bottom **TERMINAL** panel, type (or paste) this line,
and press **Enter**:

```bash
python scripts/utils.py
```

✅ **You should see four lines with numbers**, like this:

```
  countries                               40 rows
  fred_rates                             438 rows
  indicators                           1,400 rows
  oecd_unemployment                    1,258 rows
```

If you see those four lines, **you are fully set up.** 🎉
*(If not, see [Troubleshooting](#-troubleshooting--faq) below.)*

### Step 6 — Make your very first chart

1. On the **left** is a list of folders. Click the **`scripts`** folder to open it.
2. Click the file **`financial_indicators.py`**.
3. At the **top-right** of the editor, click the **▶ (play) button** — its label
   is *“Run Python File”*. *(If a menu asks you to choose a Python version, pick
   the one that says **3.11**.)*
4. Wait a few seconds — you'll see progress messages in the terminal.
5. On the left, open the **`outputs`** folder and click
   **`financial_dashboard.png`**. 🎉 **That's your first chart** — a five-panel
   dashboard of the Fed's tightening cycle.

> 💡 **Where do charts appear?** In the browser, charts do **not** pop up in a
> window — they are **saved as `.png` images in the `outputs/` folder**. Open
> that folder and click any image to view it. (You may see a harmless message
> *“FigureCanvasAgg is non-interactive…”* — ignore it; the chart still saved.)

---

## 💡 What am I actually looking at? (plain-English glossary)

| Thing you see | What it really is |
|---------------|-------------------|
| **Codespace** | Your free cloud computer, running in the browser. |
| **Terminal** (black panel, bottom) | Where you type commands and read messages. |
| A **`.py`** file | A **Python** program. Run it with the ▶ button (top-right). |
| A **`.sql`** file | A **SQL** query — a question you ask the database. |
| **`outputs/`** folder | Where your charts (`.png`) and result tables (`.csv`) are saved. |
| **`db/macro.db`** | The **database** of economic data. Click it to browse the tables. |
| **▶ play button** | “Run this file”. The output appears in the terminal / `outputs/`. |

---

## ▶ How to run things (everyday cheat-sheet)

**To run a program:** open any `.py` file and click the **▶** button (top-right).
Or type its name in the terminal. The three you'll use most:

```bash
python scripts/concepts.py             # runnable demos of every key idea (Fisher, Taylor, yield curve)
python scripts/financial_indicators.py # the big five-panel dashboard
python scripts/pipeline.py             # the full data pipeline, start to finish
```

**To look at the data like a spreadsheet:** click **`db/macro.db`** in the left
panel — it opens a table viewer (the *SQLite Viewer*, already installed).

**To see your charts:** open the **`outputs/`** folder and click any `.png`.

---

## 🆘 Troubleshooting / FAQ

**“It's been ‘Setting up your codespace’ for a while.”**
The first build takes 2–3 minutes (allow up to 5). Don't close the tab. If it
seems stuck after 5 minutes, reload the page.

**“I closed the tab / I'm back the next day. Did I lose my work?”**
No — your work is saved. Go to **https://github.com/codespaces**, and click your
course codespace to reopen it.

**“The terminal says `python: command not found`.”**
Make sure you're typing in the codespace's bottom **TERMINAL** panel (not on your
own computer), and that Step 3 finished. Reopen the codespace if needed.

**“Do I need a password, credit card, or API key?”**
**No.** The course ships with all the data it needs and runs completely offline.

**“I ran a file but nothing popped up.”**
That's expected in the browser. Charts are **saved to the `outputs/` folder** —
open it and click the `.png`.

**“I see a warning about `FigureCanvasAgg is non-interactive`.”**
Harmless. It just means “no pop-up window here” — the chart was still saved to
`outputs/`.

**“The ▶ button asks me to select an interpreter.”**
Choose the option that mentions **Python 3.11**.

**“How do I not waste my free GitHub hours?”**
When you finish for the day, go to **https://github.com/codespaces**, click the
**…** next to your codespace, and choose **Stop codespace**. Your files stay
saved; you just pause the meter.

---

## 🗓️ Day-by-day guide

> 📖 **New to SQL, Python, or the macroeconomics?** Read
> **[docs/concepts_explained.md](docs/concepts_explained.md)** first — or keep it
> open alongside. It explains *every* concept in plain English (Feynman-style:
> an analogy first, then the precise version), and points to exactly where each
> one appears. Every `.sql` file and every teaching `.py` file links to it too.
>
> 💡 **Want the human story behind the numbers?**
> **[docs/finance_anecdotes.md](docs/finance_anecdotes.md)** gives each block a
> real market anecdote — Volcker breaking inflation on purpose, "Team
> Transitory", SVB killed by *safe* bonds, the 2022 UK gilt/pension crisis, and
> the economist who publicly doubted his own famous recession indicator.
>
> 🛠️ **Why is it built this way — and how does it help me get hired?**
> **[docs/why_we_code_this.md](docs/why_we_code_this.md)** explains the *engineering
> judgment* behind every design choice (databases, views, ETL, reproducibility,
> honest model evaluation) and maps each to a real job skill. The
> **[docs/](docs/)** folder has an index of all guides.

| Day | Block | Time | Open this file | The question |
|-----|-------|------|----------------|--------------|
| 1 | B1 | 09:00–10:00 | `sql/02_core_sql.sql` | What kind of inflation was the 2022 surge? |
| 1 | B2 | 10:15–11:45 | `sql/03_joins_ctes.sql` | How did tightening spread globally? |
| 1 | B3 | 13:00–14:30 | `sql/04_window_functions.sql` + `sql/05_financial_analysis.sql` | What did the yield curve signal? |
| 2 | B4 | 09:00–10:30 | `notebooks/block4_python_apis.py` + `scripts/fetch_fred.py` | What does the labour market tell us? |
| 2 | B5 | 10:45–12:15 | `notebooks/block5_etl_pipeline.py` + `scripts/pipeline.py` | Can we automate this monitoring? |
| 2 | B6 | 13:00–14:30 | `capstone/track_[a\|b\|c]/analysis.py` | What would you advise the central bank? |

**Practise as you go:** `exercises/day1_sql.sql` (Day 1) and
`exercises/day2_python.py` (Day 2). Run `python scripts/concepts.py` any time
for live demos of every key concept.

---

## 🤖 Block 7 (extension) — Machine Learning, on your laptop

An optional final block applies machine learning to the same data — **entirely
locally: scikit-learn, CPU only, no GPU, no cloud, no internet.** Each model
trains in under a second. Full guide: **[ml/README.md](ml/README.md)**.

```bash
python ml/recession_prediction.py    # can the yield curve predict recessions?
python ml/inflation_forecast.py       # forecast inflation (Ridge & Lasso)
python ml/taylor_rule_regression.py   # learn the Fed's reaction function
python ml/country_clustering.py       # group countries into macro "regimes"
```

The recession model would have *screamed* recession in 2022–24 — yet none came.
That gap between a confident prediction and what actually happened is the perfect
springboard for the course's central question.

---

## 🎓 Beyond the course — research, data & careers

Three guides to take what you've built further and turn it into a career asset:

- **📊 [Data sources directory](docs/data_sources.md)** — a mapped catalogue of
  where to get real economic & financial data, with direct links: FRED, World
  Bank, IMF, OECD, BIS, Eurostat, the ONS, market data, long-run history, and
  aggregators like DBnomics. Plus **Kaggle**: grab community datasets
  reproducibly with [`datasets/fetch_kaggle.py`](datasets/fetch_kaggle.py).
- **🎓 [Building a thesis dataset](docs/building_a_thesis_dataset.md)** — turn
  these skills into your dissertation: choosing the unit of observation, mapping
  Y/X/controls, merging sources safely, data-quality checks, the bias traps
  (lookahead, survivorship, selection), a codebook, and a 12-point checklist.
- **📝 [Writing scientific papers](docs/writing_scientific_papers.md)** — how to
  structure an empirical economics paper, write it in LaTeX, and use
  **[latexci.com](https://latexci.com/)** to auto-build citations from a
  DOI/arXiv ID and turn your `outputs/*.csv` straight into LaTeX tables.
- **🚀 [Careers & building your portfolio](docs/careers_and_portfolio.md)** — the
  public & private institutions that hire Durham economics/finance graduates
  (central banks, IMF/World Bank/OECD/BIS, investment banks, asset managers,
  hedge funds, economic consultancies, think tanks, data firms) **with links**,
  plus a step-by-step to **host your own portfolio on GitHub Pages** and turn
  this very course into your first portfolio piece. Copy-paste starter site:
  **[templates/portfolio/](templates/portfolio/)**.

---

<details>
<summary><h2>📚 Reference (click to expand) — for the curious and for instructors</h2></summary>

### Run on your own computer instead *(advanced, optional — Codespaces is easier)*

You only need this if you cannot use Codespaces. Requires **Python 3.11+**.

```bash
git clone https://github.com/Sitraka17/durham-python-sql-2026.git
cd durham-python-sql-2026
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python datasets/download.py --no-api   # uses bundled data — no API key needed
python scripts/setup_db.py
python scripts/utils.py                # verify
```

One-shot alternative (Mac/Linux): `bash setup.sh`, or `make all`.

> **A FRED API key is optional.** Everything works offline from the bundled
> `datasets/*_static.csv`. For *live* data, get a free key at
> <https://fred.stlouisfed.org/docs/api/api_key.html>, put `FRED_KEY=...` in
> `.env`, and run `python datasets/download.py` (without `--no-api`).

### Repository structure

```
durham-python-sql-2026/
├── .devcontainer/devcontainer.json   One-click Codespaces environment
├── .github/workflows/ci.yml          Automated checks on every push
├── datasets/                         Data + the download/build scripts
│   ├── download.py                   Fetch data (--no-api uses the bundles)
│   ├── wdi_indicators.csv            World Bank — 40 countries, 1990–2024
│   ├── fred_rates_static.csv         FRED monthly series + derived indicators
│   └── oecd_unemployment_static.csv  OECD/FRED quarterly unemployment
├── sql/                              01 schema → 06 ETL queries (heavily commented)
├── scripts/                          utils, setup_db, fetch_fred, pipeline,
│                                     financial_indicators, concepts
├── notebooks/                        block4_python_apis.py, block5_etl_pipeline.py
├── exercises/                        day1_sql.sql, day2_python.py (with a checker)
├── capstone/track_{a,b,c}/           Group-project starting points
├── ml/                               Block 7 — machine learning (local, CPU)
├── docs/                             Guides: data sources, paper-writing, careers
├── templates/portfolio/              Copy-paste GitHub Pages starter site
├── db/        outputs/               Generated database / charts (auto-created)
├── requirements.txt  Makefile  setup.sh  durham.code-workspace
```

### Data sources (all open-access)

| Source | Series | Used in |
|--------|--------|---------|
| [FRED](https://fred.stlouisfed.org) | FEDFUNDS, GS2/10/30, CPIAUCSL, PCEPILFE, M2SL, MORTGAGE30US, UNRATE, WALCL, BAML OAS, USREC | Blocks 3–7 |
| [World Bank WDI](https://data.worldbank.org) | GDP per capita, inflation, unemployment, fiscal balance, current account | Blocks 1–2 |
| [OECD](https://stats.oecd.org) (via FRED) | Harmonised quarterly unemployment, 12 economies | Block 3 |

**Offline by default.** The repo ships with real, bundled data (built by
`datasets/_build_static_csvs.py` from public, key-less endpoints) so everything
works with zero API keys, reproducing the verified facts of the cycle (Fed funds
peak 5.33%, CPI YoY peak ~9%, the 2022–24 yield-curve inversion).

> **Note on credit spreads.** FRED only exposes ~3 years of the *licensed* ICE
> BofA HY/IG OAS series publicly, so pre-2023 history is reconstructed by
> rescaling the full-history Moody's Baa–10y spread (`BAA10Y`) over the overlap.
> Both inputs are real FRED series; the historical tail is a real-spread
> reconstruction, reproducing the GFC, COVID and 2022 stress episodes.

**Want live data?** See **[docs/getting_economic_data.md](docs/getting_economic_data.md)**
(the how-to) and the **[full data-sources directory](docs/data_sources.md)**
(where to find everything else, with links).

### Key financial indicators derived in code

| Indicator | Formula | FRED input |
|-----------|---------|------------|
| Real FFR (Fisher) | `fed_funds − cpi_yoy` | FEDFUNDS, CPIAUCSL |
| Taylor Rule rate | `π + 0.5 + 0.5(π−2) + 0.5·ỹ` | FEDFUNDS, CPIAUCSL, UNRATE |
| Taylor gap | `taylor_rule − fed_funds` | — |
| Yield spread | `GS10 − GS2` | GS10, GS2 |
| Mortgage spread | `MORTGAGE30US − GS10` | MORTGAGE30US, GS10 |
| M2 YoY growth | `M2SL.pct_change(12)×100` | M2SL |

Exposed through four SQL views built by `scripts/setup_db.py`:
`v_gdp_ranked`, `v_yield_curve`, `v_real_rates`, `v_credit_dashboard`.

### Makefile commands (own-computer setup)

```bash
make all        # full setup: venv + data + database
make pipeline   # run the Block 5 pipeline end-to-end
make dashboard  # build the five-panel chart
make test       # verify database row counts
make clean      # remove generated DB and charts
```

### VS Code extensions (pre-installed in Codespaces)

**SQLite Viewer** (browse `.db` files) · **Python** · **Jupyter**.
Open the workspace: *File → Open Workspace from File → `durham.code-workspace`*.

</details>

---

## License

Released under the [MIT License](LICENSE) — free to reuse, adapt and teach
from, with attribution. © 2026 Sitraka Forler.

---

## Instructor

**Sitraka Forler**
Systems Architect & Senior Data Scientist, POST Luxembourg ·
Lecturer, IAE Metz & Centrale Méditerranée (AMU) ·
[sitraka.forler@post.lu](mailto:sitraka.forler@post.lu) ·
[LinkedIn](https://www.linkedin.com/in/sitraka-matthieu-forler/) ·
[github.com/Sitraka17](https://github.com/Sitraka17)
