# Tutorial: Getting Fed (FRED) and World Economic Data

A practical guide to pulling the macro/financial data this course uses —
**FRED** (US Federal Reserve data), the **World Bank**, and **OECD** — in
Python. Everything here works with the libraries already in
`requirements.txt` (`requests`, `pandas`, `fredapi`, `wbdata`).

> **You don't need any of this to run the course.** The repo ships with
> bundled `datasets/*_static.csv` and `python datasets/download.py --no-api`
> builds the database offline. This tutorial is for when you want **live** or
> **fresh** data — for your capstone, your dissertation, or just to understand
> where the numbers come from.

---

## 0. The three sources at a glance

| Source | What | API key? | Library / endpoint |
|--------|------|----------|--------------------|
| **FRED** | US rates, inflation, money, credit, labour, Fed balance sheet | Optional (free) | `fredapi`, or key-less `fredgraph.csv` |
| **World Bank (WDI)** | GDP, inflation, unemployment, fiscal/external balances — ~200 countries | No | `wbdata`, or REST/JSON |
| **OECD** | Harmonised cross-country series (e.g. quarterly unemployment) | No | via FRED-hosted OECD series |

---

## 1. FRED — Federal Reserve Economic Data

[FRED](https://fred.stlouisfed.org) hosts 800,000+ economic time series. Every
series has a short **ID** you can find in its page URL, e.g.
`fred.stlouisfed.org/series/`**`FEDFUNDS`**.

The series this course uses:

| ID | Meaning | Frequency |
|----|---------|-----------|
| `FEDFUNDS` | Effective Federal Funds Rate | Monthly |
| `GS2` / `GS10` / `GS30` | 2y / 10y / 30y Treasury yields | Monthly |
| `CPIAUCSL` | CPI (all urban, SA, index) | Monthly |
| `PCEPILFE` | Core PCE price index | Monthly |
| `M2SL` / `M2V` | M2 money stock / velocity | Monthly / Quarterly |
| `UNRATE` / `PAYEMS` / `CIVPART` | Unemployment / payrolls / participation | Monthly |
| `BAMLH0A0HYM2` / `BAMLC0A0CM` | ICE BofA HY / IG option-adjusted spreads | Daily |
| `MORTGAGE30US` | 30-year fixed mortgage rate | Weekly |
| `WALCL` | Fed total assets | Weekly |
| `BAA10Y` | Moody's Baa corporate spread over 10y | Daily |

### Option A — no key needed (`fredgraph.csv`)

FRED serves any series as CSV with no authentication:

```python
import io, requests, pandas as pd

def fred_csv(series_id: str) -> pd.Series:
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    raw = requests.get(url, timeout=30).text
    df  = pd.read_csv(io.StringIO(raw))
    df.columns = ["date", series_id]
    df["date"] = pd.to_datetime(df["date"])
    df[series_id] = pd.to_numeric(df[series_id], errors="coerce")  # "." -> NaN
    return df.dropna().set_index("date")[series_id]

ffr = fred_csv("FEDFUNDS")
print(ffr.tail())
```

This is exactly what [`datasets/_build_static_csvs.py`](../datasets/_build_static_csvs.py)
does to build the bundled data.

**Two gotchas with the key-less endpoint:**
- **Frequency aggregation:** add `&fq=Monthly&fam=avg` to downsample a daily/
  weekly series to a monthly average — e.g.
  `...fredgraph.csv?id=BAA10Y&fq=Monthly&fam=avg`.
- **Licensed series are capped:** the ICE BofA OAS series (`BAMLH0A0HYM2`,
  `BAMLC0A0CM`) only return ~3 years of history on this public endpoint. For
  full history you need the keyed API (below) — this is why the repo
  reconstructs pre-2023 credit-spread history from `BAA10Y` (see the README's
  data-provenance note).

### Option B — the official API (free key, full history)

1. Get a free key: <https://fred.stlouisfed.org/docs/api/api_key.html>
2. Put it in `.env` at the repo root: `FRED_KEY=your_key_here`
3. Use `fredapi`:

```python
import os
from fredapi import Fred
from dotenv import load_dotenv

load_dotenv()
fred = Fred(api_key=os.getenv("FRED_KEY"))

ffr  = fred.get_series("FEDFUNDS", observation_start="1990-01-01")
cpi  = fred.get_series("CPIAUCSL")
print(ffr.tail())
```

With the key set, `python datasets/download.py` (no `--no-api`) pulls all 15
series live and recomputes every derived indicator. The repo's
[`scripts/fetch_fred.py`](../scripts/fetch_fred.py) wraps this with an automatic
fallback to the static CSV when no key is present.

---

## 2. World Bank — World Development Indicators (WDI)

No key. Indicators also have codes, found in the URL, e.g.
`data.worldbank.org/indicator/`**`NY.GDP.PCAP.CD`** (GDP per capita).

Codes used here: `NY.GDP.PCAP.CD` (GDP/capita), `FP.CPI.TOTL.ZG` (inflation),
`SL.UEM.TOTL.ZS` (unemployment), `NY.GDP.MKTP.KD.ZG` (GDP growth),
`GC.NLD.TOTL.GD.ZS` (fiscal balance), `BN.CAB.XOKA.GD.ZS` (current account).

### Option A — the `wbdata` library

```python
import wbdata, datetime

indicators = {"NY.GDP.PCAP.CD": "gdp_per_capita", "FP.CPI.TOTL.ZG": "inflation"}
df = wbdata.get_dataframe(
    indicators,
    country=["USA", "GBR", "DEU", "JPN"],
    date=(datetime.datetime(1990, 1, 1), datetime.datetime(2024, 1, 1)),
)
print(df.head())
```

### Option B — the REST/JSON API (what the repo uses)

You can query many countries at once (`;`-separated) and page in one shot:

```python
import requests, pandas as pd

countries = "USA;GBR;DEU;FRA;JPN"
code = "FP.CPI.TOTL.ZG"   # inflation, annual %
url = (f"https://api.worldbank.org/v2/country/{countries}/indicator/{code}"
       f"?format=json&per_page=20000&date=1990:2024")
meta, rows = requests.get(url, timeout=30).json()      # [metadata, observations]
df = pd.DataFrame([
    {"country": r["countryiso3code"], "year": int(r["date"]), "inflation": r["value"]}
    for r in rows if r["value"] is not None
])
print(df.sort_values(["country", "year"]).tail())
```

**Gotcha:** some indicators get archived/renamed. We swapped the old fiscal
series `GC.BAL.CASH.GD.ZS` (archived) for `GC.NLD.TOTL.GD.ZS` (net
lending/borrowing). If a code suddenly returns an error message instead of
data, check the indicator page on data.worldbank.org for its current code.

---

## 3. OECD — cross-country harmonised series

The OECD's own SDMX API is powerful but fiddly. The pragmatic route — and what
this repo uses — is the **FRED-hosted OECD harmonised series**, which you fetch
exactly like any other FRED series. Harmonised quarterly unemployment follows
the pattern `LRHUTTTT{ISO2}Q156S`:

```python
us_unemp = fred_csv("LRHUTTTTUSQ156S")   # United States, quarterly, %
uk_unemp = fred_csv("LRHUTTTTGBQ156S")   # United Kingdom
de_unemp = fred_csv("LRHUTTTTDEQ156S")   # Germany
```

Replace the 2-letter ISO code (`US`, `GB`, `DE`, `FR`, `JP`, `IT`, `CA`, …) to
get other countries.

---

## 3b. Kaggle — community & alternative datasets

FRED/World Bank/OECD give you clean *official* series. **Kaggle** is the other
half: thousands of community datasets — firm-level panels, scraped prices,
surveys, alternative data — ideal for a dissertation that needs something the
official sources don't publish.

One-time setup: create a free Kaggle account → Settings → API →
**"Create New Token"** (downloads `kaggle.json`). Put it at `~/.kaggle/kaggle.json`
(`chmod 600`), or set `KAGGLE_USERNAME` / `KAGGLE_KEY` (in Codespaces, add them as
Codespaces secrets). Then download *reproducibly* by slug:

```bash
# the slug for kaggle.com/datasets/<owner>/<name> is "<owner>/<name>"
python datasets/fetch_kaggle.py owner/dataset-name
python datasets/fetch_kaggle.py owner/dataset-name --to-db my_table   # load into macro.db
```

`datasets/fetch_kaggle.py` downloads the dataset, previews every CSV, and can
load one straight into `db/macro.db` so you can **JOIN Kaggle data to the
FRED/World Bank tables in SQL** — exactly the integration skill from Block 2.
With no token it just prints the setup steps (it never breaks the build).

> ⚠️ Check each dataset's **licence** on its Kaggle page before using it in a
> publication, and cite it. See
> [building_a_thesis_dataset.md](building_a_thesis_dataset.md) §9.

---

## 4. Refreshing this repo's bundled data

To rebuild all three static CSVs from live sources (e.g. next year):

```bash
python datasets/_build_static_csvs.py
```

It writes `datasets/wdi_indicators.csv`, `fred_rates_static.csv` and
`oecd_unemployment_static.csv`, prints sanity checks against the known facts of
the 2022–23 cycle, and caches raw responses under `datasets/.cache/` so repeat
runs are fast. Then rebuild the database:

```bash
python scripts/setup_db.py
```

---

## 5. Common pitfalls

- **Units.** ICE BofA OAS are in *percent* on FRED (`4.18` = 4.18% = 418 bp);
  this repo stores credit spreads in **basis points**, so it multiplies by 100.
  Always check a series' "Units" on its FRED page.
- **Seasonal adjustment.** `CPIAUCSL` is seasonally adjusted; the headline
  "9.1% June 2022" figure is the *non*-adjusted `CPIAUCNS` (≈9.06%). SA vs NSA
  explains small discrepancies.
- **Frequencies.** Mixing daily/weekly/monthly/quarterly series and merging on
  date creates ragged frames. Resample to a common cadence first
  (`series.resample("MS").mean()` for month-start).
- **Missing values.** FRED uses `.` and the World Bank uses `null` for missing
  observations — coerce with `pd.to_numeric(..., errors="coerce")` and decide
  whether to drop or forward-fill.
- **Rate limits / etiquette.** Be gentle with public endpoints: cache responses
  (as `_build_static_csvs.py` does), don't hammer in tight loops.

---

### See also
- `datasets/_build_static_csvs.py` — the full, working provenance script.
- `scripts/fetch_fred.py` — keyed FRED fetch with static-CSV fallback.
- `datasets/download.py` — the orchestrator (`--no-api` for offline).
- **Kaggle** — community/alternative datasets: download reproducibly with
  [`datasets/fetch_kaggle.py`](../datasets/fetch_kaggle.py) (see §3b above).
- **[building_a_thesis_dataset.md](building_a_thesis_dataset.md)** — turning all
  of this into a defensible dataset for your dissertation.
