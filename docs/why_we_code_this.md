# Why we code it this way — and how it pays off in a real job

This course doesn't just teach Python and SQL — it teaches the *engineering
judgment* that separates a one-off homework script from work a bank, central
bank or fund would actually run. For every design choice in the repo, here's
**why we did it** and **how that exact skill shows up in a paid role**.

> Read this once you've seen the code run. It explains the decisions *behind*
> the code — the things interviewers probe and employers pay for.

---

## 1. Why a database (SQL) at all — why not just Excel?

**What we do:** raw numbers go into a SQLite database (`db/macro.db`); we query
it with SQL (`sql/*.sql`).

**Why:** a spreadsheet mixes data, formulas and presentation in one fragile
grid — one dragged cell silently corrupts everything, and nobody can audit what
happened. A database *separates* the data from the questions you ask of it. The
questions (SQL) are written down, repeatable and reviewable.

**In the real world:** essentially every financial institution runs on
databases — a trading desk's positions, a bank's transactions, a central bank's
statistical warehouse. "Can you write SQL?" is on almost every economics/finance
data job description. The 2012 **JPMorgan "London Whale"** loss was worsened by a
risk model run in a spreadsheet with copy-paste errors — the textbook case for
*not* doing serious analysis in Excel.

## 2. Why SQLAlchemy + a single shared engine — not raw `sqlite3`?

**What we do:** `scripts/utils.py` exposes one cached `get_engine()` (a
"singleton") built with SQLAlchemy.

**Why:** (a) **Portability** — SQLAlchemy speaks SQLite, PostgreSQL, MySQL,
Snowflake, BigQuery with the *same* code. We use SQLite for a zero-install
course; a bank would point the identical code at Postgres. (b) **One connection,
reused** — opening a new database connection per query is slow and leaks
resources; a shared engine pools them.

**In the real world:** you will almost never meet SQLite in production — you'll
meet Postgres, Snowflake or BigQuery. Writing against an *abstraction* means your
analysis survives the switch. "Don't hard-code your environment" is a core data-
engineering principle.

## 3. Why SQL *views* (`v_yield_curve`, …) instead of repeating queries?

**What we do:** `scripts/setup_db.py` builds four named views — saved queries
that behave like tables.

**Why:** the yield-curve calculation is defined **once**. Every script and
dashboard reads `v_yield_curve` and gets the *same* definition. Change the logic
in one place and everything updates — no copy-pasted formulas drifting out of
sync.

**In the real world:** this is exactly how BI tools (Tableau, Power BI, Looker)
and the modern data stack (**dbt**) work — a curated "semantic layer" of trusted,
named metrics sits between raw tables and analysts. Defining "the official
recession indicator" once, centrally, is what keeps a firm's numbers consistent
across teams.

## 4. Why split the work into Extract → Transform → Load → Query → Visualise?

**What we do:** `scripts/pipeline.py` is five small functions, one per stage.

**Why:** if the download breaks you fix `extract()` without touching the chart
code; if a chart is wrong you fix `visualise()` without re-downloading anything.
Small, single-purpose steps are testable and debuggable. A 300-line "do
everything" script is not.

**In the real world:** this *is* data engineering. Tools like **Apache Airflow**,
**Dagster** and **dbt** exist to orchestrate exactly these stages. "Build me a
data pipeline" is a whole job (data engineer, £50–90k+ in London). The mental
model you practise here is the one they hire for.

## 5. Why bundled static CSVs and a `--no-api` switch?

**What we do:** real data is committed as `datasets/*_static.csv`; the build runs
offline by default.

**Why:** **reproducibility**. An analysis that depends on a live API gives a
*different* answer every day and breaks when the API is down, rate-limits you, or
changes its format. Pinning a snapshot means the result is identical for every
student today and in a year — and it works on a plane with no Wi-Fi.

**In the real world:** "it worked yesterday" is the most expensive sentence in
software. Regulators and journals demand that results **reproduce**; quant
backtests must run on frozen historical data, not a moving target. Snapshotting
your inputs is professional hygiene.

## 6. Why `.env` and never hard-code an API key?

**What we do:** secrets live in `.env` (git-ignored); the code reads `FRED_KEY`
from the environment.

**Why:** a key pasted into code and pushed to GitHub is *public forever* — bots
scrape GitHub for leaked keys within minutes. Separating secrets from code lets
you share the code safely and rotate keys without editing source.

**In the real world:** committing a credential is a genuine fireable mistake and
a common breach cause. Every firm uses secret managers (Vault, AWS Secrets
Manager, GitHub Secrets). The discipline — *config and secrets are not code* —
starts here.

## 7. Why compute in SQL window functions instead of Python loops?

**What we do:** moving averages, `LAG` growth rates and running totals are done
in SQL, next to the data.

**Why:** push the computation to where the data lives. The database is optimised
for this and processes millions of rows without shipping them anywhere. A Python
`for`-loop over rows is often 100–1000× slower and won't scale.

**In the real world:** you do **not** pull a billion-row table onto your laptop.
You send the query to the warehouse and get back the small answer. "Push compute
to the data" is a defining instinct of a strong data professional — and window
functions are a senior-level SQL interview staple.

## 8. Why vectorised pandas / method chaining instead of `for` loops?

**What we do:** `df.assign(...)`, `pct_change()`, `groupby().transform()` —
whole-column operations, not row-by-row loops.

**Why:** pandas runs these in fast, compiled C under the hood; a Python loop runs
in slow interpreted Python. On a monthly series the difference is invisible; on
tick data or millions of rows it's the difference between 0.1 seconds and ten
minutes. Chaining also reads like a recipe, top to bottom.

**In the real world:** performance is money on large datasets, and readable
transformation pipelines are what code reviewers approve. "Vectorise it" is
everyday feedback on a data team.

## 9. Why compute derived indicators once and store them?

**What we do:** `cpi_yoy`, `real_rate`, `taylor_gap`, etc. are computed in
`fetch_fred.py`/`download.py` and saved as columns.

**Why:** **DRY** (Don't Repeat Yourself). Define "real rate = nominal − inflation"
in one place; every consumer gets the identical number. If five scripts each
recomputed it slightly differently, you'd get five "truths."

**In the real world:** this is the idea behind a **feature store** — precomputed,
versioned, shared features that every model and report draws from, so the whole
firm agrees on what "12-month inflation" means.

## 10. Why train/test split, time-series CV, and a fixed random seed?

**What we do:** `ml/` always trains on the past and tests on the *future*
(`TimeSeriesSplit`), never shuffles time, and sets `random_state=42`.

**Why:** a model graded on data it trained on will look brilliant and be useless
— like marking your own exam. For time series, testing on the *past* using the
*future* is a subtler version of the same cheating (lookahead bias). A fixed seed
makes results reproducible.

**In the real world:** this is literally **model risk management** — banks are
required (e.g. the Fed's *SR 11-7* guidance) to validate models on out-of-sample
data before trusting them with money. A quant who backtests with lookahead bias
blows up real capital. Getting evaluation honest is the *whole game*.

## 11. Why prefer simple, interpretable models (and regularisation)?

**What we do:** logistic/linear regression first; the random forest only as a
comparison; Ridge/Lasso to keep models humble.

**Why:** a model you can explain — "an inverted curve raises recession risk by
this much" — is one you can trust, debug and defend. A black box that's slightly
more accurate but inexplicable is often the wrong professional choice.

**In the real world:** you must **explain models to regulators, risk committees
and clients**. "Why did the model deny this loan / flag this trade?" needs an
answer. Interpretability and **model governance** are why banks still run
logistic regressions in 2026, not just neural nets.

## 12. Why Git, branches, and Continuous Integration (CI)?

**What we do:** the repo is version-controlled; `.github/workflows/ci.yml` re-
runs every check on each push.

**Why:** Git records *who changed what, when, and why*, and lets many people work
without overwriting each other. CI is an automated safety net — it rebuilds the
whole project from scratch on every push and shouts if anything broke, *before*
a user hits it.

**In the real world:** Git is non-negotiable on every software/quant/data team on
earth. CI/CD is how modern teams ship safely. Being fluent in "branch → commit →
pull request → CI green → merge" is assumed from day one.

## 13. Why a reproducible environment (pinned `requirements.txt`, Codespaces)?

**What we do:** every package is pinned to an exact version; the `.devcontainer`
defines the whole environment.

**Why:** "works on my machine" is the oldest excuse in software. Pinning versions
and shipping the environment means the code runs *identically* for everyone —
today, in a year, on Windows, on a Mac, in the cloud.

**In the real world:** this is what **Docker** and reproducible environments solve
at scale. Reproducible builds are required for audited financial models and for
any team larger than one. Codespaces is a friendly on-ramp to that discipline.

## 14. Why label every chart and save it to a file?

**What we do:** every figure has a title, axis labels, a legend, and is written
to `outputs/*.png`.

**Why:** a chart is an *argument*. An unlabelled line is noise; a titled,
annotated one says "the curve inverted here and the model panicked there."
Saving to a file (not just showing it) makes results shareable and embeddable.

**In the real world:** the chart in the slide deck is often what actually decides
a meeting. Communicating a result clearly is as valued as producing it — many
brilliant analyses die because nobody could read the output.

## 15. Why docstrings, comments and a README?

**What we do:** every file opens with a docstring of *why it exists*; the README
onboards a stranger in minutes.

**Why:** code is read far more often than it's written, and the "next person" is
usually *you*, six months later, with no memory of it. Documentation is a gift to
future-you and to teammates.

**In the real world:** undocumented code is a liability a team has to reverse-
engineer. The ability to write clearly *about* your work — in code comments, a
README, or a paper — is a career multiplier. (It's also why this repo has a whole
[docs/](.) folder.)

---

### The meta-lesson

Notice the through-line: **separate concerns, make it reproducible, push compute
to the data, evaluate honestly, and communicate clearly.** Those five instincts —
far more than any single function — are what make you employable as an economist
*who can code*. The Fed question is the vehicle; these habits are the cargo.
