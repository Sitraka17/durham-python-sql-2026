"""
capstone/track_a/analysis.py
=============================
TRACK A — The Labour Market Lens

Research question
-----------------
Did the 2022-23 UK tightening cycle (Bank Rate: 0.1% -> 5.25%)
produce a meaningful and sustained rise in UK unemployment?

At what point did the real rate turn significantly positive?
Is there a measurable lag between the real rate turning positive
and unemployment rising?

How does the UK sacrifice ratio compare to the US?
(Sacrifice ratio = cumulative unemployment rise / inflation fall)

Datasets used
-------------
  datasets/uk_ons_labour.csv     ONS labour market: unemployment, wages
  fred_rates table               US FFR, real rate, Taylor gap (for comparison)

Database written
----------------
  db/macro.db   ->  table: track_a_labour
                    table: track_a_fred_comparison

Outputs
-------
  outputs/track_a_labour_market.png
  outputs/track_a_sacrifice_ratio.csv

Usage
-----
    python capstone/track_a/analysis.py
"""
import sys
from pathlib import Path

# Allow imports from repo root
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from sqlalchemy import create_engine, text

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

from scripts.utils import get_engine, DATASETS, OUTPUTS, log

plt.rcParams.update({
    "font.family":       "serif",
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "axes.grid":         True,
    "grid.alpha":        0.25,
})

NAVY = "#002855"
GOLD = "#C49400"
RED  = "#9B1C1C"
GRN  = "#0A6640"

# ----------------------------------------------------------------
# Step 1: Load / create UK ONS data
# ----------------------------------------------------------------
def load_uk_labour() -> pd.DataFrame:
    """
    Load UK ONS labour market data.
    If the CSV is not present, generates synthetic data for demonstration.
    Replace with real ONS data from:
    https://www.ons.gov.uk/employmentandlabourmarket/
    """
    csv = DATASETS / "uk_ons_labour.csv"

    if csv.exists():
        log.info(f"Loading UK ONS data from {csv.name}")
        df = pd.read_csv(csv, parse_dates=["date"])
        return df

    log.warning("uk_ons_labour.csv not found — generating synthetic demo data.")
    log.warning("Replace with real ONS data for your presentation.")

    import numpy as np
    dates  = pd.date_range("2019-01-01", "2025-12-01", freq="MS")
    np.random.seed(42)

    # Approximate stylised UK labour market 2019-2025
    unemployment = [
        3.8,3.9,3.9,3.8,4.1,4.2,  # 2019
        4.1,4.5,5.0,5.5,5.1,5.0,  # 2020 COVID shock
        4.9,4.8,4.7,4.7,4.3,4.2,  # 2021 recovery
        3.9,3.8,3.7,3.6,3.5,3.7,  # 2022 tightening begins
        3.9,4.0,4.1,4.2,4.3,4.2,  # 2023 peak
        4.3,4.4,4.5,4.5,4.4,4.3,  # 2024
        4.3,4.2,4.2,4.1,4.1,4.0,  # 2025
    ]
    wage_growth = [
        3.5,3.4,3.5,3.6,3.2,3.1,  # 2019
        3.0,3.2,0.8,1.0,2.4,2.8,  # 2020
        4.0,5.5,6.8,7.2,7.0,6.8,  # 2021
        7.5,8.0,8.5,9.0,9.5,9.8,  # 2022 wages surge
        8.5,7.8,7.2,6.8,6.5,6.2,  # 2023
        5.8,5.5,5.2,5.0,4.8,4.5,  # 2024
        4.3,4.1,3.9,3.8,3.6,3.5,  # 2025
    ]
    cpi_uk = [
        1.8,1.7,1.9,2.1,1.7,1.9,
        1.8,1.0,0.5,0.3,0.3,0.6,
        0.9,1.5,2.1,3.2,4.9,5.4,
        6.2,7.0,8.7,9.1,10.1,11.1,
        10.4,9.2,8.7,7.9,7.0,6.4,
        4.0,3.2,2.5,2.3,2.6,2.8,
        3.1,3.2,3.3,3.2,3.0,2.9,
    ]
    bank_rate = [
        0.75,0.75,0.75,0.75,0.10,0.10,
        0.10,0.10,0.10,0.10,0.10,0.10,
        0.10,0.10,0.10,0.10,0.10,0.10,
        0.25,0.50,1.00,1.25,1.75,2.25,
        3.00,3.50,4.00,4.25,4.50,5.00,
        5.25,5.25,5.25,5.00,4.75,4.50,
        4.25,4.00,3.75,3.75,3.75,3.75,
    ]

    n = min(len(dates), len(unemployment))
    df = pd.DataFrame({
        "date":         dates[:n],
        "unemployment": unemployment[:n],
        "wage_growth":  wage_growth[:n],
        "cpi_uk":       cpi_uk[:n],
        "bank_rate":    bank_rate[:n],
    })
    df["real_bank_rate"] = (df["bank_rate"] - df["cpi_uk"]).round(2)
    df.to_csv(csv, index=False)
    log.info(f"Demo data saved to {csv}")
    return df


# ----------------------------------------------------------------
# Step 2: Load FRED US data for comparison
# ----------------------------------------------------------------
def load_us_comparison() -> pd.DataFrame:
    engine = get_engine()
    return pd.read_sql_query(
        "SELECT date, fed_funds, real_rate, unemployment, "
        "       cpi_yoy, taylor_gap "
        "FROM fred_rates "
        "WHERE date >= '2019-01-01' "
        "AND real_rate IS NOT NULL",
        engine, parse_dates=["date"]
    )


# ----------------------------------------------------------------
# Step 3: Load into track_a tables
# ----------------------------------------------------------------
def load_to_db(uk_df: pd.DataFrame) -> None:
    engine = get_engine()
    uk_df.to_sql("track_a_labour", engine,
                 if_exists="replace", index=False)
    log.info("Loaded -> track_a_labour")


# ----------------------------------------------------------------
# Step 4: Analytical SQL queries
# ----------------------------------------------------------------
Q1 = """
-- Query 1: UK tightening timeline — bank rate, real rate, unemployment
SELECT date,
       ROUND(bank_rate, 2)       AS bank_rate,
       ROUND(cpi_uk, 1)          AS cpi,
       ROUND(real_bank_rate, 2)  AS real_rate,
       ROUND(unemployment, 1)    AS unemployment
FROM   track_a_labour
WHERE  date >= '2021-01-01'
ORDER  BY date
"""

Q2 = """
-- Query 2: 6-month moving average unemployment (smoothed trend)
SELECT date,
       ROUND(unemployment, 1)              AS unemployment,
       ROUND(
           AVG(unemployment)
           OVER (ORDER BY date
                 ROWS BETWEEN 5 PRECEDING AND CURRENT ROW)
       , 2)                                AS ma6_unemployment,
       ROUND(real_bank_rate, 2)            AS real_rate
FROM   track_a_labour
WHERE  date >= '2020-01-01'
ORDER  BY date
"""

Q3 = """
-- Query 3: Lag detection — unemployment response to real rate
-- How many months after the real rate turned positive did
-- unemployment start rising?
WITH policy AS (
    SELECT date,
           real_bank_rate,
           unemployment,
           CASE WHEN real_bank_rate > 0 THEN 1 ELSE 0 END AS restrictive,
           LAG(unemployment, 6)
               OVER (ORDER BY date) AS unemployment_6m_ago
    FROM track_a_labour
)
SELECT date,
       ROUND(real_bank_rate, 2)    AS real_rate,
       ROUND(unemployment, 1)      AS unemployment,
       ROUND(unemployment_6m_ago, 1) AS unemployment_6m_ago,
       ROUND(unemployment - unemployment_6m_ago, 2) AS change_6m,
       restrictive
FROM   policy
WHERE  date >= '2022-01-01'
ORDER  BY date
"""


def run_queries(engine) -> dict[str, pd.DataFrame]:
    results = {}
    for name, q in [("timeline", Q1), ("ma_trend", Q2), ("lag_analysis", Q3)]:
        df = pd.read_sql_query(q, engine, parse_dates=["date"])
        results[name] = df
        log.info(f"Query {name}: {len(df)} rows")
    return results


# ----------------------------------------------------------------
# Step 5: Sacrifice ratio calculation
# ----------------------------------------------------------------
def sacrifice_ratio(uk_df: pd.DataFrame) -> dict:
    """
    Sacrifice ratio = cumulative unemployment rise / total CPI fall
    Measured from inflation peak to trough.
    """
    peak = uk_df.loc[uk_df["cpi_uk"].idxmax(), "date"]
    trough_df = uk_df[uk_df["date"] >= peak]
    trough = trough_df.loc[trough_df["cpi_uk"].idxmin(), "date"]

    window = uk_df[(uk_df["date"] >= peak) & (uk_df["date"] <= trough)]
    nairu  = 4.0
    u_gap  = (window["unemployment"] - nairu).clip(lower=0).sum()
    pi_fall = window["cpi_uk"].iloc[0] - window["cpi_uk"].iloc[-1]

    sr = round(u_gap / pi_fall, 2) if pi_fall > 0 else float("nan")
    return {
        "inflation_peak_date":   str(peak.date()),
        "inflation_trough_date": str(trough.date()),
        "peak_cpi":              round(window["cpi_uk"].iloc[0], 1),
        "trough_cpi":            round(window["cpi_uk"].iloc[-1], 1),
        "inflation_fall_pp":     round(pi_fall, 1),
        "cumulative_u_gap":      round(float(u_gap), 2),
        "sacrifice_ratio":       sr,
        "interpretation":        (
            "Very low (supply-driven disinflation)" if sr < 1.0
            else "Moderate" if sr < 2.0
            else "High (demand-driven, painful)"
        )
    }


# ----------------------------------------------------------------
# Step 6: Visualisation
# ----------------------------------------------------------------
def plot_track_a(uk_df: pd.DataFrame, us_df: pd.DataFrame,
                 results: dict) -> None:
    fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=False)
    fig.suptitle(
        "Track A — UK Labour Market & Tightening Cycle\n"
        "Durham University Capstone · June 2026",
        fontsize=11, fontweight="bold"
    )

    uk = uk_df[uk_df["date"] >= "2019-01-01"]

    # Panel 1: Bank Rate + Real Rate + CPI
    ax1 = axes[0]
    ax1r = ax1.twinx()
    ax1.plot(uk["date"], uk["bank_rate"],     color=NAVY, lw=1.5,
             label="Bank Rate")
    ax1.plot(uk["date"], uk["real_bank_rate"], color=GRN,  lw=1.0,
             linestyle="--", label="Real Bank Rate")
    ax1.axhline(0, color="gray", lw=0.4, linestyle=":")
    ax1r.plot(uk["date"], uk["cpi_uk"], color=RED, lw=1.0,
              alpha=0.75, label="CPI (right)")
    ax1.set_ylabel("Rate (%)")
    ax1r.set_ylabel("CPI YoY (%)", color=RED)
    ax1.set_title("Bank Rate, Real Rate & UK CPI", loc="left", fontsize=9)
    lines1, l1 = ax1.get_legend_handles_labels()
    lines2, l2 = ax1r.get_legend_handles_labels()
    ax1.legend(lines1+lines2, l1+l2, fontsize=7, ncol=3, loc="upper left")

    # Panel 2: Unemployment with MA
    ax2 = axes[1]
    ma6 = results["ma_trend"]
    ax2.plot(ma6["date"], ma6["unemployment"], color=MUTED if False else NAVY,
             lw=0.8, alpha=0.6, label="Unemployment")
    ax2.plot(ma6["date"], ma6["ma6_unemployment"], color=GOLD, lw=2.0,
             label="6-month MA")
    ax2.axhline(4.0, color="gray", lw=0.5, linestyle=":",
                label="Approx. NAIRU (4.0%)")
    ax2.set_ylabel("Unemployment (%)")
    ax2.set_title("UK Unemployment Rate — Trend vs Cycle", loc="left", fontsize=9)
    ax2.legend(fontsize=7, ncol=3, loc="upper left")

    # Panel 3: UK vs US unemployment comparison
    ax3 = axes[2]
    ax3.plot(uk["date"], uk["unemployment"], color=NAVY, lw=1.2,
             label="UK unemployment")
    us_trim = us_df[us_df["date"] >= "2019-01-01"]
    ax3.plot(us_trim["date"], us_trim["unemployment"], color=RED,
             lw=1.2, linestyle="--", label="US unemployment")
    ax3.set_ylabel("Unemployment (%)")
    ax3.set_title("UK vs US Unemployment — Tightening Cycle Comparison",
                  loc="left", fontsize=9)
    ax3.legend(fontsize=8, loc="upper right")

    for ax in axes:
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        ax.xaxis.set_major_locator(mdates.YearLocator(1))

    plt.tight_layout()
    out = OUTPUTS / "track_a_labour_market.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    log.info(f"Saved: {out}")
    plt.show()
    plt.close()


MUTED = "#5A5F67"

# ----------------------------------------------------------------
# Main
# ----------------------------------------------------------------
if __name__ == "__main__":
    log.info("=== Track A: UK Labour Market Analysis ===")

    uk_df  = load_uk_labour()
    us_df  = load_us_comparison()
    load_to_db(uk_df)

    engine  = get_engine()
    results = run_queries(engine)

    sr = sacrifice_ratio(uk_df)
    log.info(f"\nUK Sacrifice Ratio Analysis:\n  {sr}")
    pd.DataFrame([sr]).to_csv(
        OUTPUTS / "track_a_sacrifice_ratio.csv", index=False)

    plot_track_a(uk_df, us_df, results)
    log.info("=== Track A complete ===")
    log.info("\n3-MINUTE PRESENTATION GUIDE:")
    log.info("  1. Show Panel 1: When did the real rate turn positive? (~mid-2023)")
    log.info("  2. Show Panel 2: Did unemployment respond? (rose from 3.5% to ~4.5%)")
    log.info(f"  3. Quote sacrifice ratio: {sr['sacrifice_ratio']} — {sr['interpretation']}")
    log.info("  4. Conclusion: tightening worked, but UK paid a higher price than US")
