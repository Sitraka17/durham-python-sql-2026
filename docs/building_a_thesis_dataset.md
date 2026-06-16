# Building a good dataset for your master's thesis

The dataset *is* your thesis. A brilliant question with a sloppy dataset becomes
an un-defendable result; a clear, well-built dataset makes the analysis almost
write itself. This guide turns the engineering habits from the course into a
repeatable recipe for your own research data.

> Use it with: [data_sources.md](data_sources.md) (where to get data),
> [getting_economic_data.md](getting_economic_data.md) (FRED/WB/OECD how-to),
> [datasets/fetch_kaggle.py](../datasets/fetch_kaggle.py) (Kaggle), and
> [why_we_code_this.md](why_we_code_this.md) (the engineering reasons).

---

## 1. The golden rule: the dataset serves the question

Write your research question in **one sentence** *before* you download anything,
then ask: "what is the smallest dataset that could answer this?" Everything
follows from the question.

> *Bad:* "I'll grab some finance data and see what's interesting." → endless
> fishing, p-hacking, no thesis.
> *Good:* "Does a 1pp rise in the policy rate reduce house-price growth more in
> high-household-debt countries?" → this *tells you* the unit (country-month),
> the outcome (house-price growth), the key variable (policy rate × debt), and
> the controls you need.

## 2. Decide the unit of observation and the shape

Every dataset has a **unit of observation** — what one row represents. Get this
right first; everything else is a column.

| Structure | One row is… | Example | Key(s) |
|-----------|-------------|---------|--------|
| Cross-section | one entity at one time | 40 countries in 2022 | `country` |
| Time series | one entity over time | US, monthly | `date` |
| **Panel** (most theses) | one entity × one period | country × month | `country` + `date` |

This course's `fred_rates` is a time series (one row per month); `indicators`
is a panel (country × year). **Tidy data** rule: one row = one observation, one
column = one variable, one value per cell. Resist "wide" spreadsheets with a
column per year — they fight every tool.

## 3. Map your variables before you build

Sketch the table on paper first:

- **Outcome (Y)** — the thing you're explaining (e.g. `house_price_growth`).
- **Key regressor(s) (X)** — the cause you care about (e.g. `policy_rate`).
- **Controls** — things that also move Y and could confound (GDP growth,
  population, inflation).
- **Identifiers / keys** — `entity_id`, `date` — how rows are uniquely labelled
  and how tables join.
- **(Maybe) instrument** — for causal identification (a variable that moves X
  but not Y directly).

If you can't name your Y and X, you're not ready to collect data yet.

## 4. Where to get each variable

- **Official macro/finance:** FRED, World Bank, OECD, IMF, BIS, ONS, Eurostat —
  see [data_sources.md](data_sources.md). Reliable, citable, free.
- **Community / alternative / firm-level:** **Kaggle** — use
  `python datasets/fetch_kaggle.py owner/dataset-slug` to download
  *reproducibly* (and `--to-db` to load it straight into SQL).
- **Academic gold standard (via Durham):** WRDS / CRSP / Compustat for
  firm-level finance.

> **Combining sources is where theses are won.** The interesting question
> usually needs *two* datasets joined — e.g. FRED rates + a Kaggle housing panel.
> That's exactly the JOIN skill from `sql/03_joins_ctes.sql`.

## 5. Build it like an engineer (so it's reproducible)

Mirror this repo's flow — it's a proven template:

```
your-thesis/
├── data/raw/         # untouched downloads — NEVER edit by hand
├── data/processed/   # cleaned, merged output of your code
├── build_dataset.py  # the script that turns raw -> processed
└── analysis.py       # uses processed/ only
```

Rules that save your thesis:
- **Never hand-edit raw data.** Every change happens in code, so it's repeatable
  and auditable. (Why: [why_we_code_this.md](why_we_code_this.md) §5.)
- **Snapshot + date your downloads.** Record the source, series ID and access
  date (data revise!).
- **Merge carefully.** Joining on the wrong key, or on mismatched frequencies
  (monthly vs quarterly), silently corrupts everything. Check row counts before
  and after every merge: a merge that *grows* your rows usually means duplicate
  keys.
- **Align frequencies explicitly** (resample monthly→quarterly with a stated
  rule), don't let pandas guess.
- **Derive in code, store once** (e.g. `real_rate = nominal − inflation`) so one
  definition feeds the whole analysis.

## 6. Data-quality checklist (run this on every dataset)

```python
df.shape                      # how many rows/cols? expected?
df.info()                     # dtypes — are numbers actually numeric?
df.isna().mean().sort_values()# missingness per column
df.describe()                 # ranges — any impossible values (negative prices)?
df.duplicated(subset=keys).sum()   # duplicate keys = a merge bomb waiting
```

- **Missing data:** is it random, or systematic (e.g. poorer countries missing)?
  Systematic missingness biases results. Decide: drop, or impute, and *justify*.
- **Outliers:** a real crisis or a data error? Plot before you trust.
- **Units & scale:** %, bp, $, $m? Mixing them is the classic silent bug (this
  course converts credit spreads to basis points for exactly this reason).
- **Revisions / vintages:** macro data gets revised. If timing matters, use
  *as-released* ("vintage") data (e.g. ALFRED) — using revised data you couldn't
  have known at the time is **lookahead bias**.

## 7. Pitfalls that sink economics/finance theses

- **Lookahead bias:** using information you couldn't have had at decision time.
  The cardinal sin of any backtest. (Why time-series CV matters: §10 of
  why_we_code_this.md.)
- **Survivorship bias:** analysing only firms/funds that *survived* — the failed
  ones dropped out of your data, flattering your results.
- **Selection bias:** your sample isn't representative of the population you
  claim to speak about.
- **p-hacking / data dredging:** testing 50 variables and reporting the 3 that
  were "significant" by chance. Pre-register your hypothesis; report what you
  tested.
- **Spurious correlation:** two trending series correlate by accident. Think
  about mechanism, and watch for non-stationarity.
- **Tiny N:** 15 countries × 1 year is not enough to support strong claims. Know
  your effective sample size.

## 8. Document it — the data dictionary (codebook)

A thesis dataset without a codebook is unfinished. Include a table like:

| Variable | Description | Unit | Source | Coverage | Notes |
|----------|-------------|------|--------|----------|-------|
| `policy_rate` | Central-bank policy rate | % p.a. | FRED `FEDFUNDS` | 1990–2024, monthly | — |
| `hp_growth` | House-price index YoY | % | Kaggle `owner/ds` | 2005–2023 | SA |

Plus a **"Data & code availability"** statement in the thesis itself — there's a
ready template at
[templates/data_and_code_availability.md](../templates/data_and_code_availability.md).

## 9. Ethics & licensing — *can you actually use this?*

- **Licence:** check the dataset's licence (Kaggle shows it on each dataset
  page; World Bank/FRED are open). "Found on the internet" ≠ "free to use in a
  publication." Cite it regardless.
- **Personal data / GDPR:** if rows are *people*, you likely need anonymisation
  and possibly ethics approval — talk to your supervisor early.
- **Terms of use / scraping:** respect robots.txt and site terms; don't scrape
  what an API offers.

## 10. A worked template — this very course

This repo is a miniature, well-built research dataset you can copy the *shape*
of:

- **Question:** "Did the Fed's tightening cycle work?"
- **Units:** US monthly (`fred_rates`), country-year panel (`indicators`).
- **Sources:** FRED + World Bank + OECD, snapshotted to `datasets/*_static.csv`,
  built reproducibly by `datasets/_build_static_csvs.py`.
- **Provenance:** every series documented in `sql/01_schema.sql`; the build is
  re-runnable; results reproduce on a clean clone.

Fork it, swap in your own question and data, and you have a thesis-grade pipeline.

---

## The 12-point checklist

- [ ] One-sentence research question written down first
- [ ] Unit of observation chosen (cross-section / time series / panel)
- [ ] Y, X, controls and keys mapped before collecting
- [ ] Sources identified and *citable*; licences checked
- [ ] Raw data saved untouched; all changes in code
- [ ] Downloads dated; revised vs vintage decided
- [ ] Merges checked (keys unique, row counts sane, frequencies aligned)
- [ ] Units consistent and documented
- [ ] Missingness, outliers, duplicates inspected and handled with justification
- [ ] Lookahead / survivorship / selection bias considered
- [ ] Data dictionary (codebook) written
- [ ] "Data & code availability" statement + repo link included
