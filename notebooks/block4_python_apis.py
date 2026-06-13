# 📖 New here? A plain-English (Feynman-style) explanation of every concept
# used below — Python, the economics, the ML — is in
# docs/concepts_explained.md. Read it alongside this file.
"""
notebooks/block4_python_apis.py
================================
BLOCK 4 -- Advanced Python Patterns & Live Economic APIs
"What does the labour market tell us about the tightening cycle?"

HOW TO USE THIS FILE
Run section by section. Each section has a CONCEPT header (why),
then the code (how), then a NOTICE comment (what to look for).
Exercise at the end -- try before reading the scaffold.

LEARNING OBJECTIVES
  1. Fetch FRED data with fredapi; use CSV fallback gracefully
  2. Write clean, readable pipelines with method chaining
  3. Reshape between wide and long format (melt / pivot_table)
  4. Compute the Fisher real rate and Taylor Rule from scratch
  5. Know when to use Python vs SQL for each transformation

Run: python notebooks/block4_python_apis.py
"""
import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from dotenv import load_dotenv
# --- make the `scripts` package importable when run directly --------------
# Lets you launch any file straight from the repo root, e.g.
#     python scripts/setup_db.py        python capstone/track_a/analysis.py
import sys as _sys, pathlib as _pl
for _p in _pl.Path(__file__).resolve().parents:
    if (_p / "scripts" / "utils.py").exists():
        if str(_p) not in _sys.path:
            _sys.path.insert(0, str(_p))
        break
# --------------------------------------------------------------------------

from scripts.utils import DATASETS, OUTPUTS, log

load_dotenv()

plt.rcParams.update({
    "font.family": "serif",
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.25,
})
NAVY, GOLD, RED, GRN = "#002855", "#C49400", "#9B1C1C", "#0A6640"


# ================================================================
# SECTION 1: Project hygiene -- .env, venv, imports
# ================================================================
print("\n" + "="*60 + "\nSECTION 1: Project hygiene\n" + "="*60)

# CONCEPT: The .env file
# API keys are secrets. They must NEVER be committed to Git.
# Pattern:  secrets in .env  (listed in .gitignore)
#           load with load_dotenv(), read with os.getenv()
FRED_KEY = os.getenv("FRED_KEY", "")
USE_API  = bool(FRED_KEY and FRED_KEY != "your_fred_api_key_here")
print(f"  FRED_KEY available: {USE_API}")
print(f"  Python executable:  {sys.executable}")
print(f"  pandas version:     {pd.__version__}")


# ================================================================
# SECTION 2: Fetching data -- API + fallback pattern
# ================================================================
print("\n" + "="*60 + "\nSECTION 2: Fetching FRED data\n" + "="*60)

# CONCEPT: Always have a fallback
# Production code never assumes a network call succeeds.
# Pattern: try the API -> if it fails, use a pre-downloaded CSV.
# This means students without a FRED key can still follow along.

SERIES = {
    "fed_funds":    "FEDFUNDS",
    "rate_2y":      "GS2",
    "rate_10y":     "GS10",
    "cpi_index":    "CPIAUCSL",
    "unemployment": "UNRATE",
    "hy_spread":    "BAMLH0A0HYM2",
    "mortgage_30y": "MORTGAGE30US",
    "m2":           "M2SL",
}


def fetch_fred(series: dict, start: str = "2000-01-01") -> pd.DataFrame:
    """
    Fetch FRED series and merge into a wide DataFrame.

    CONCEPT: reduce(merge, frames)
    Each series is a separate DataFrame. We merge them pairwise
    using functools.reduce -- a cleaner pattern than a for-loop
    that builds up a growing merged DataFrame.

    We use how='outer' so we keep ALL dates even if one series
    starts earlier or has gaps (some series are daily, others monthly).
    """
    from functools import reduce
    from fredapi import Fred
    fred   = Fred(api_key=FRED_KEY)
    frames = []
    for name, sid in series.items():
        raw = fred.get_series(sid, observation_start=start)
        df  = raw.rename(name).reset_index().rename(columns={"index": "date"})
        frames.append(df)
        print(f"  {sid:20s}: {len(df):,} observations")
    merged = reduce(
        lambda left, right: pd.merge(left, right, on="date", how="outer"),
        frames
    )
    return merged.sort_values("date").reset_index(drop=True)


if USE_API:
    print("Fetching from FRED API...")
    raw = fetch_fred(SERIES)
    raw.to_csv(DATASETS / "fred_block4.csv", index=False)
else:
    csv = DATASETS / "fred_rates.csv"
    raw = pd.read_csv(csv, parse_dates=["date"]) if csv.exists() else None
    if raw is None:
        print("ERROR: No data. Run: python datasets/download.py"); sys.exit(1)
    print(f"  Using fallback: {csv.name} ({len(raw):,} rows)")

print(f"\nShape: {raw.shape}\nColumns: {list(raw.columns)[:8]}")


# ================================================================
# SECTION 3: Method chaining -- readable transformation pipelines
# ================================================================
print("\n" + "="*60 + "\nSECTION 3: Method chaining\n" + "="*60)

# CONCEPT: Method chaining
# Instead of:  df1 = df.rename(...)
#              df2 = df1.dropna(...)    <- lots of throwaway variables
#              df3 = df2.assign(...)
#
# We write:    df = (df
#                    .rename(...)
#                    .dropna(...)
#                    .assign(...))      <- one statement, easy to read
#
# Each method returns a NEW DataFrame; the next method acts on it.
# The lambda x: inside assign() refers to the DataFrame AT THAT POINT
# in the chain, AFTER all earlier transformations have run.
#
# This is the difference between a script and a pipeline.

def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transform raw FRED data into analysis-ready indicators.

    Each assign() step is a new derived column with a clear name
    and a comment explaining the economic meaning.
    """
    return (
        df
        .assign(date=lambda x: pd.to_datetime(x["date"]))
        .query("date >= '2000-01-01'")
        .sort_values("date")

        # ---- INFLATION ----
        # pct_change(12) on a monthly index = year-on-year % change.
        # This is the PANDAS equivalent of LAG(cpi_index, 12) in SQL.
        .assign(
            cpi_yoy = lambda x: x["cpi_index"].pct_change(12, fill_method=None).mul(100).round(3)
        )

        # ---- FISHER EQUATION: r = i - pi ----
        # The REAL interest rate is what matters for economic decisions.
        # When real_rate < 0, borrowing is cheap in real terms.
        # June 2022: fed_funds=1.6%, cpi_yoy=9.1% -> real_rate=-7.5%
        # This was the most accommodative policy since 1975.
        .assign(
            real_rate = lambda x: (x["fed_funds"] - x["cpi_yoy"]).round(3)
        )

        # ---- YIELD CURVE ----
        # spread_10_2 < 0 means the curve is INVERTED.
        # Bond markets are pricing in FUTURE RATE CUTS (because they
        # expect the economy to slow and force the Fed to ease).
        # Historical record: every US recession since 1955 was preceded
        # by an inversion. The 2022-24 inversion has not (yet) been
        # followed by a recession -- the main puzzle of the cycle.
        .assign(
            spread_10_2 = lambda x: (x["rate_10y"] - x["rate_2y"]).round(3),
            inverted    = lambda x: (x["rate_10y"] < x["rate_2y"]).astype(int)
        )

        # ---- MORTGAGE SPREAD ----
        # 30-year mortgage rate = 10-year Treasury + risk premium.
        # Historical norm: 150-200 bp. In 2022-23 it hit ~290 bp
        # (MBS market stress + lock-in effect).
        .assign(
            mortgage_spread = lambda x: (x["mortgage_30y"] - x["rate_10y"]).round(3)
        )

        # ---- M2 GROWTH ----
        # M2 grew 26% in 2020-21 (largest peacetime expansion ever).
        # Then FELL year-on-year in 2023 (first time since the 1930s).
        .assign(
            m2_yoy = lambda x: x["m2"].pct_change(12, fill_method=None).mul(100).round(2)
        )

        # ---- TAYLOR RULE ----
        # i* = pi + r* + 0.5*(pi - pi*) + 0.5*y_gap
        # r* (neutral) = 0.5%, pi* (target) = 2.0%
        # y_gap proxy: Okun's law: y_gap = -2*(UNRATE - NAIRU), NAIRU=4.0%
        # Applied to June 2022: pi=9.1%, UNRATE=3.6%:
        #   i* = 9.1 + 0.5 + 0.5*(9.1-2) + 0.5*(-2*(3.6-4.0))
        #      = 9.1 + 0.5 + 3.55 + 0.4 = ~13.5%
        # Actual rate: 1.6% => taylor_gap = 13.5 - 1.6 = ~12pp BEHIND
        .assign(
            taylor_rule = lambda x: (
                x["cpi_yoy"]
                + 0.5
                + 0.5 * (x["cpi_yoy"] - 2.0)
                + 0.5 * (-2.0 * (x["unemployment"] - 4.0))
            ).round(3),
            taylor_gap  = lambda x: None  # computed below after taylor_rule exists
        )
        .assign(
            taylor_gap = lambda x: (x["taylor_rule"] - x["fed_funds"]).round(3)
        )

        .dropna(subset=["fed_funds", "cpi_yoy"])
        .reset_index(drop=True)
    )


df = compute_indicators(raw)
print(f"Shape after transformation: {df.shape}")
key_cols = ["date", "fed_funds", "cpi_yoy", "real_rate",
            "spread_10_2", "inverted", "taylor_gap"]
avail = [c for c in key_cols if c in df.columns]
print(f"\nLast 6 rows:")
print(df[avail].tail(6).to_string(index=False))

# >>> NOTICE:
# >>> (1) real_rate should be negative through most of 2021-22.
# >>>     Confirm: find the month it finally turned positive.
# >>> (2) inverted should be 1 from mid-2022. Confirm the start date.
# >>> (3) taylor_gap: find the month it was largest (most behind curve).
# >>>     The answer is around June 2022 -- check your output.


# ================================================================
# SECTION 4: Wide vs Long (tidy) format
# ================================================================
print("\n" + "="*60 + "\nSECTION 4: melt() and pivot_table()\n" + "="*60)

# CONCEPT: Why long format?
# WIDE: one row per date, one column per indicator. Good for computation.
# LONG: one row per (date, indicator) pair. Good for:
#   - Storing in SQL (one table handles all indicators)
#   - Plotting multiple series with seaborn (it expects long format)
#   - Filtering to one indicator without knowing column names
#
# melt()        converts WIDE -> LONG
# pivot_table() converts LONG -> WIDE

indicator_cols = [c for c in
                  ["fed_funds", "real_rate", "spread_10_2", "taylor_gap"]
                  if c in df.columns]

df_long = (
    df[["date"] + indicator_cols]
    .melt(
        id_vars    = "date",
        var_name   = "indicator",
        value_name = "value"
    )
    .dropna(subset=["value"])
)
print(f"  Wide -> Long:  {df.shape} -> {df_long.shape}")
print(f"\n  Long format (first 8 rows):")
print(df_long.head(8).to_string(index=False))

# Convert back: pivot_table goes Long -> Wide
df_wide_again = (
    df_long
    .pivot_table(index="date", columns="indicator", values="value")
    .reset_index()
)
df_wide_again.columns.name = None
print(f"\n  Long -> Wide:  {df_long.shape} -> {df_wide_again.shape}")


# ================================================================
# SECTION 5: groupby().transform() -- group-relative statistics
# ================================================================
print("\n" + "="*60 + "\nSECTION 5: groupby().transform()\n" + "="*60)

# CONCEPT: transform() vs agg()
# groupby().agg()       collapses rows (like SQL GROUP BY)
#                       -> fewer rows than input
# groupby().transform() preserves all rows (like SQL window functions)
#                       -> same shape as input, values replaced by group stat
#
# Use case here: "Is the current real rate high or low relative to
#                 the decade average?" -- requires knowing BOTH
#                 the individual value (all rows) AND the group average.

if "real_rate" in df.columns:
    df_dec = df[["date", "real_rate"]].dropna().copy()
    df_dec["decade"] = (df_dec["date"].dt.year // 10 * 10).astype(str) + "s"

    # transform() gives EACH ROW the mean of its decade's group
    df_dec["decade_mean"] = (
        df_dec.groupby("decade")["real_rate"].transform("mean").round(2)
    )
    df_dec["above_decade_mean"] = (
        (df_dec["real_rate"] > df_dec["decade_mean"]).astype(int)
    )
    summary = (df_dec.groupby("decade")
               .agg(avg_real_rate=("real_rate", "mean"),
                    months_negative=("real_rate", lambda x: (x<0).sum()),
                    months_total=("real_rate", "count"))
               .round(2))
    print("\n  Real rate by decade:")
    print(summary.to_string())
    print("\n  Last 6 rows with decade comparison:")
    print(df_dec.tail(6).to_string(index=False))


# ================================================================
# SECTION 6: Visualisation -- the Taylor Rule and Fisher equation
# ================================================================
print("\n" + "="*60 + "\nSECTION 6: Visualisation\n" + "="*60)

if "taylor_rule" in df.columns:
    plot_df = df[df["date"] >= "2015-01-01"].dropna(
        subset=["fed_funds", "taylor_rule", "real_rate"]
    )
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    fig.suptitle(
        "Block 4 Output: Fisher Equation & Taylor Rule\n"
        "Did the Fed start hiking too late?",
        fontsize=11, fontweight="bold"
    )

    # Panel 1: Actual vs Taylor Rule implied rate
    ax1.plot(plot_df["date"], plot_df["fed_funds"],
             NAVY, lw=1.5, label="Actual Fed Funds Rate")
    ax1.plot(plot_df["date"], plot_df["taylor_rule"],
             GOLD, lw=1.5, ls="--", label="Taylor Rule implied rate")
    ax1.fill_between(plot_df["date"],
                     plot_df["fed_funds"], plot_df["taylor_rule"],
                     where=(plot_df["taylor_gap"] > 0),
                     color=RED, alpha=0.15, label="Behind the curve")
    ax1.fill_between(plot_df["date"],
                     plot_df["fed_funds"], plot_df["taylor_rule"],
                     where=(plot_df["taylor_gap"] <= 0),
                     color=GRN, alpha=0.12, label="Ahead of the curve")
    ax1.set_ylabel("Rate (%)")
    ax1.set_title("Nominal rate vs Taylor Rule -- policy stance", loc="left", fontsize=9)
    ax1.legend(fontsize=7, ncol=2, loc="upper left")

    # Panel 2: Fisher real rate
    ax2.plot(plot_df["date"], plot_df["real_rate"],
             GRN, lw=1.2, label="Real FFR (nominal - CPI YoY)")
    ax2.axhline(0,   color="gray", lw=0.5, ls=":")
    ax2.axhline(0.5, color=GOLD,  lw=0.5, ls=":", label="Estimated neutral rate (~0.5%)")
    ax2.fill_between(plot_df["date"], plot_df["real_rate"], 0,
                     where=(plot_df["real_rate"] < 0),
                     color=RED, alpha=0.15, label="Negative real rate (accommodative)")
    ax2.set_ylabel("Real Rate (%)")
    ax2.set_title("Ex-post real interest rate (Fisher: r = i - pi)", loc="left", fontsize=9)
    ax2.legend(fontsize=7, ncol=2, loc="upper left")

    for ax in [ax1, ax2]:
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        ax.xaxis.set_major_locator(mdates.YearLocator(1))
    plt.tight_layout()
    out = OUTPUTS / "block4_taylor_rule.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    print(f"  Saved: {out}")
    plt.show()
    plt.close()


# ================================================================
# EXERCISE (15 minutes)
# ================================================================
print("\n" + "="*60 + "\nEXERCISE\n" + "="*60)
print("""
TASK: Add the Mortgage Spread and M2 story to your pipeline.

Step 1: Confirm that mortgage_spread and m2_yoy are already in df.
        Print: df[['date','mortgage_spread','m2_yoy']].dropna().tail(12)

Step 2: Add a third panel to the visualisation showing:
        - mortgage_spread (left axis, pp)
        - m2_yoy (right axis, %)
        Shade when mortgage_spread > 2.0 (above historical norm).

Step 3: Find the month where M2 annual growth was most negative
        (the 2023 decline).
        Answer: df.loc[df['m2_yoy'].idxmin(), ['date','m2_yoy']]

Step 4 (discussion):
        The quantity theory: MV = PY, so delta_M + delta_V = delta_P + delta_Y
        If M2 grew 26% in 2020-21, what would you have predicted for inflation?
        What does the fact that inflation peaked at "only" 9% tell you about V?

Scaffold for Step 2:
    fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
    # ... (panels 1 and 2 as above) ...
    ax3   = axes[2]
    ax3r  = ax3.twinx()
    ms_ok = df['mortgage_spread'].notna()
    m2_ok = df['m2_yoy'].notna()
    ax3.plot(df.loc[ms_ok,'date'], df.loc[ms_ok,'mortgage_spread'],
             color=NAVY, lw=1.2, label='Mortgage spread (left)')
    ax3.axhline(1.75, color=GOLD, lw=0.6, ls=':', label='Historical norm ~1.75pp')
    ax3r.plot(df.loc[m2_ok,'date'], df.loc[m2_ok,'m2_yoy'],
              color=GRN, lw=1.0, label='M2 YoY growth (right)')
    ax3r.axhline(0, color='gray', lw=0.4, ls=':')
""")

print("Block 4 complete.\n")
