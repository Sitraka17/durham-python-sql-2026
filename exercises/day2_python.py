"""
exercises/day2_python.py
=========================
Day 2 Exercise Set -- Python for Economic Analysis

HOW TO USE THIS FILE
--------------------
Each exercise is a function with:
  - CONTEXT: the economic question
  - TASK: what to build
  - SCAFFOLD: the structure to fill in
  - HINT comments where you are likely to get stuck
  - DISCUSSION QUESTIONS to go beyond the code

Run:  python exercises/day2_python.py
  -> this runs the check() function which verifies your implementations.

Attempt each exercise before looking at the next one.
Mark an exercise DONE when you can run it AND explain every line.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

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

from scripts.utils import get_engine, OUTPUTS, log

NAVY, GOLD, RED, GRN = "#002855", "#C49400", "#9B1C1C", "#0A6640"
plt.rcParams.update({
    "font.family": "serif",
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.25,
})


def load_fred() -> pd.DataFrame:
    """Load the pre-built FRED dataset from macro.db."""
    engine = get_engine()
    return pd.read_sql_query(
        "SELECT * FROM fred_rates WHERE date >= '2000-01-01'",
        engine, parse_dates=["date"]
    )


# ================================================================
# EXERCISE 1 -- Method chaining and derived indicators
# Difficulty: EASY | Time: 15 min
# ================================================================
def exercise1_method_chaining(df: pd.DataFrame) -> pd.DataFrame:
    """
    CONTEXT:
      The mortgage market was one of the clearest channels through which
      the 2022-23 tightening was transmitted to the real economy.
      30-year mortgage rates rose from 3.1% (Dec 2021) to 7.8% (Oct 2023).
      This effectively doubled monthly payments on a median-priced US home.
      Yet housing prices barely fell, and sales volumes collapsed instead.
      This is the "lock-in effect" -- homeowners with 3% mortgages would not
      sell into a 7.5% market.

    TASK:
      Add these four indicators to the DataFrame using a single method chain:
        1. mortgage_spread: mortgage_30y minus rate_10y
           (the "risk premium" over Treasuries for mortgage lending,
            normal range: 150-200bp, peaked at ~290bp in 2022-23)
        2. m2_yoy: M2 annual growth rate (pct_change(12) * 100)
           (M2 grew 26% in 2020-21 -- largest peacetime expansion ever)
        3. hy_ig_ratio: hy_spread divided by ig_spread
           (ratio of HY to IG spread; rises in risk-off episodes;
            when it spikes, markets fear defaults are rising)
        4. curve_steepness: spread_30_2 minus spread_10_2
           (measures the long-end of the curve separately from the short-end)

    THEN:
      Print the last 6 rows showing only the new columns.
      Find the month with the highest mortgage_spread.
      Find the month with the lowest m2_yoy (the 2023 money contraction).

    SCAFFOLD:
    """
    # HINT: method chaining starts with ( df and ends with )
    # HINT: each .assign() takes keyword arguments: new_col_name = lambda x: ...
    # HINT: x inside the lambda refers to the DataFrame AT THAT POINT in the chain
    # HINT: for hy_ig_ratio, handle division by zero with .replace(0, np.nan)

    result = (
        df
        .assign(date=lambda x: pd.to_datetime(x["date"]))
        .sort_values("date")
        .assign(
            # YOUR CODE HERE
            mortgage_spread  = lambda x: None,   # replace None with formula
            m2_yoy           = lambda x: None,
            hy_ig_ratio      = lambda x: None,
            curve_steepness  = lambda x: None,
        )
    )

    # Print new columns
    new_cols = ["date", "mortgage_spread", "m2_yoy", "hy_ig_ratio", "curve_steepness"]
    avail    = [c for c in new_cols if result[c].notna().any()]
    print("\nExercise 1 -- new indicators (last 6 rows):")
    print(result[avail].dropna().tail(6).to_string(index=False))

    # Find extremes
    for col, label in [
        ("mortgage_spread", "Highest mortgage spread"),
        ("m2_yoy",          "Lowest M2 growth (money contraction)"),
    ]:
        if col in result.columns and result[col].notna().any():
            if "lowest" in label.lower() or "min" in label.lower():
                idx = result[col].idxmin()
            else:
                idx = result[col].idxmax()
            row = result.iloc[idx]
            print(f"\n  {label}: {row[col]:.2f} on {row['date'].strftime('%Y-%m')}")

    return result


# ================================================================
# EXERCISE 2 -- groupby().transform() for relative analysis
# Difficulty: MEDIUM | Time: 20 min
# ================================================================
def exercise2_transform(df: pd.DataFrame) -> pd.DataFrame:
    """
    CONTEXT:
      Context is everything in macroeconomics. A real interest rate
      of -2% was normal in the 1970s (stagflation era).
      The SAME -2% real rate in 2015 indicated extraordinary accommodation.
      To understand whether current policy is tight or loose, you need
      to compare it to a relevant historical benchmark -- not just an
      absolute threshold.

    TASK:
      Using groupby().transform(), compute:
        1. For each row: decade label ("2000s", "2010s", "2020s")
        2. decade_mean_real_rate: the mean real_rate for that decade
        3. deviation_from_decade_mean: real_rate minus decade_mean_real_rate
        4. decade_pct_negative: fraction of months in that decade where
           real_rate < 0 (computed with transform as well)

      Then for each decade, print:
        - average real rate
        - fraction of months with negative real rate
        - single most extreme month (highest absolute deviation)

    KEY CONCEPT:
      transform() keeps ALL rows -- it "broadcasts" the group statistic
      back to every row in that group.
      This is the pandas equivalent of SQL window functions.

    SCAFFOLD:
    """
    df_dec = df[["date", "real_rate"]].dropna().copy()
    df_dec["date"] = pd.to_datetime(df_dec["date"])

    # STEP 1: Create decade label (floor year to nearest decade)
    # HINT: df_dec["date"].dt.year gives integer year
    # HINT: (year // 10) * 10 floors to decade start
    # HINT: then convert to string + "s": "2000s", "2010s", "2020s"
    df_dec["decade"] = None  # REPLACE WITH YOUR CODE

    # STEP 2: Use transform() to broadcast group statistics to every row
    # HINT: groupby("decade")["real_rate"].transform("mean")
    #       gives each row the mean of its decade's real_rate values
    df_dec["decade_mean"]      = None  # REPLACE
    df_dec["deviation"]        = None  # real_rate - decade_mean
    df_dec["negative_flag"]    = None  # 1 if real_rate < 0 else 0
    df_dec["pct_neg_in_decade"] = None  # fraction of months negative (use transform)

    # STEP 3: Print decade summary
    print("\nExercise 2 -- real rate by decade:")
    if df_dec["decade"].notna().any():
        summary = df_dec.groupby("decade").agg(
            avg_real_rate      = ("real_rate",    "mean"),
            pct_months_negative = ("negative_flag", "mean"),
            total_months        = ("real_rate",    "count"),
        ).round(2)
        print(summary.to_string())

    print("\nLast 6 rows with decade context:")
    cols = [c for c in ["date","real_rate","decade","decade_mean","deviation"] if c in df_dec]
    print(df_dec[cols].tail(6).to_string(index=False))

    return df_dec


# ================================================================
# EXERCISE 3 -- read_sql_query: bring SQL results into Python
# Difficulty: MEDIUM | Time: 20 min
# ================================================================
def exercise3_sql_in_python() -> pd.DataFrame:
    """
    CONTEXT:
      The Python x SQL integration is the core skill of Block 5.
      We use Python for FETCHING and TRANSFORMING raw data.
      We use SQL for ANALYSING stored data.
      Then we use Python to VISUALISE the SQL results.

    TASK:
      Write a SQL query using read_sql_query() that:
        1. Selects from the fred_rates table
        2. Computes the 12-month moving average of the HY spread in SQL
           (using AVG(hy_spread) OVER (...))
        3. Flags months where the YoY change in HY spread > 100bp
           (HINT: hy_spread - LAG(hy_spread, 12) > 100)
        4. Filters to dates >= 2000-01-01
        5. Returns: date, hy_spread, ma12_hy_spread, hy_stress_flag

      Then use the result to produce a chart with:
        - HY spread as a line
        - 12-month MA as a thicker line
        - Stress months highlighted with a red background (axvspan or fill_between)

      Title the chart: "High-Yield Spread: Stress Detection via SQL Window Functions"

    SCAFFOLD:
    """
    engine = get_engine()

    # WRITE YOUR SQL QUERY HERE
    # HINT: AVG(hy_spread) OVER (ORDER BY date ROWS BETWEEN 11 PRECEDING AND CURRENT ROW)
    # HINT: hy_spread - LAG(hy_spread, 12) OVER (ORDER BY date) for YoY change
    # HINT: CASE WHEN yoy_change > 100 THEN 1 ELSE 0 END for the flag
    SQL = """
    SELECT
        date,
        hy_spread,
        -- YOUR WINDOW FUNCTION HERE (moving average)
        NULL AS ma12_hy_spread,
        -- YOUR FLAG HERE
        0    AS hy_stress_flag
    FROM fred_rates
    WHERE date >= '2000-01-01'
      AND hy_spread IS NOT NULL
    ORDER BY date
    """
    result = pd.read_sql_query(SQL, engine, parse_dates=["date"])

    print(f"\nExercise 3 -- SQL query returned {len(result)} rows")
    print(result.tail(6).to_string(index=False))

    # BUILD YOUR CHART HERE
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.set_title("Exercise 3: HY Spread + Stress Detection (your chart here)",
                 fontsize=10)
    # HINT: ax.plot(result["date"], result["hy_spread"], ...)
    # HINT: ax.plot(result["date"], result["ma12_hy_spread"], ...)
    # HINT: for stress months: plot or fill_between where hy_stress_flag == 1
    plt.tight_layout()
    out = OUTPUTS / "exercise3_hy_stress.png"
    plt.savefig(out, dpi=140, bbox_inches="tight")
    log.info(f"  Saved: {out}")
    plt.show(); plt.close()

    return result


# ================================================================
# EXERCISE 4 (CHALLENGE) -- Build a Taylor Rule sensitivity analysis
# Difficulty: HARD | Time: 30 min
# ================================================================
def exercise4_taylor_sensitivity(df: pd.DataFrame) -> pd.DataFrame:
    """
    CONTEXT:
      The Taylor Rule has a key unobserved parameter: r* (the neutral
      real interest rate). Different economists estimate it differently.
      The Laubach-Williams model puts it at ~0.5% post-GFC.
      Some estimates after the pandemic are 1.5-2.5% (the "R-star has risen"
      argument). If r* is higher, the same nominal rate is LESS restrictive
      than it appears.

      The policy debate: if r* = 0.5%, a 5.33% rate with 3% inflation
      gives a real rate of 2.33%, which is 1.83pp above neutral.
      If r* = 2%, the same rate is only 0.33pp above neutral -- barely tight.

    TASK:
      Compute the Taylor Rule implied rate for THREE different values of r*:
        r* = 0.5%  (pre-pandemic consensus)
        r* = 1.0%  (middle estimate)
        r* = 2.0%  (post-pandemic "R-star has risen" view)

      For each r*, compute the Taylor gap (implied - actual).
      Plot all three on one chart from 2015 to present.
      Add a horizontal line at taylor_gap = 0.
      
      Interpretation: the SPREAD between the three lines tells you how
      SENSITIVE the "behind the curve" verdict is to your assumption about r*.
      If all three lines agree the Fed was far behind in 2022, the conclusion
      is robust. If they disagree, you need to know r* before concluding.

    SCAFFOLD:
    """
    df_s = df[["date", "fed_funds", "cpi_yoy", "unemployment"]].dropna().copy()
    df_s["date"] = pd.to_datetime(df_s["date"])

    PI_STAR = 2.0
    NAIRU   = 4.0
    R_STARS = {
        "r*=0.5% (pre-pandemic)":     0.5,
        "r*=1.0% (middle estimate)":  1.0,
        "r*=2.0% (R-star has risen)": 2.0,
    }

    # Compute output gap proxy
    df_s["output_gap"] = -2.0 * (df_s["unemployment"] - NAIRU)

    # For each r* value, compute the Taylor Rule and gap
    for label, rstar in R_STARS.items():
        col_tr  = f"taylor_r{rstar}"
        col_gap = f"gap_r{rstar}"
        # HINT: taylor_rule = cpi_yoy + rstar + 0.5*(cpi_yoy - PI_STAR) + 0.5*output_gap
        # HINT: gap = taylor_rule - fed_funds
        df_s[col_tr]  = None   # YOUR CODE
        df_s[col_gap] = None   # YOUR CODE

    print(f"\nExercise 4 columns: {list(df_s.columns)}")

    # BUILD YOUR CHART HERE
    plot_df = df_s[df_s["date"] >= "2015-01-01"].dropna()
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.axhline(0, color="gray", lw=0.6, ls="--")
    colours = [NAVY, GOLD, RED]
    for (label, rstar), colour in zip(R_STARS.items(), colours):
        col_gap = f"gap_r{rstar}"
        if col_gap in plot_df.columns and plot_df[col_gap].notna().any():
            ax.plot(plot_df["date"], plot_df[col_gap],
                    color=colour, lw=1.5, label=label)
    ax.set_ylabel("Taylor Rule Gap (pp above/below Taylor Rule)")
    ax.set_title(
        "Exercise 4: Taylor Rule Sensitivity to r*\n"
        "How sensitive is the 'behind the curve' verdict to the neutral rate assumption?",
        fontsize=10
    )
    ax.legend(fontsize=8)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.xaxis.set_major_locator(mdates.YearLocator(1))
    plt.tight_layout()
    out = OUTPUTS / "exercise4_taylor_sensitivity.png"
    plt.savefig(out, dpi=140, bbox_inches="tight")
    log.info(f"  Saved: {out}")
    plt.show(); plt.close()

    return df_s


# ================================================================
# VERIFICATION FUNCTION
# ================================================================
def check():
    """Run all exercises and check for obvious errors."""
    print("\n" + "="*60)
    print("Day 2 Python Exercises")
    print("="*60)

    df = load_fred()
    print(f"\nLoaded {len(df):,} rows from macro.db")

    print("\n--- Exercise 1: Method chaining ---")
    try:
        r1 = exercise1_method_chaining(df)
        new_cols = ["mortgage_spread", "m2_yoy", "hy_ig_ratio", "curve_steepness"]
        nulls = [c for c in new_cols if c not in r1.columns or r1[c].isna().all()]
        if nulls:
            print(f"  TODO: {nulls} still return None. Fill in the lambda formulas.")
        else:
            print("  PASS: all four indicators computed.")
    except Exception as e:
        print(f"  ERROR: {e}")

    print("\n--- Exercise 2: groupby().transform() ---")
    try:
        r2 = exercise2_transform(df)
        if r2["decade"].isna().all():
            print("  TODO: add the decade label (see HINT in function).")
        else:
            print("  PASS: decade column populated.")
    except Exception as e:
        print(f"  ERROR: {e}")

    print("\n--- Exercise 3: SQL in Python ---")
    try:
        r3 = exercise3_sql_in_python()
        if r3["ma12_hy_spread"].isna().all():
            print("  TODO: replace NULL with the window function in your SQL.")
        else:
            print("  PASS: SQL query returned real data.")
    except Exception as e:
        print(f"  ERROR: {e}")

    print("\n--- Exercise 4 (CHALLENGE): Taylor sensitivity ---")
    try:
        r4 = exercise4_taylor_sensitivity(df)
        gap_cols = [c for c in r4.columns if c.startswith("gap_")]
        if not gap_cols or r4[gap_cols[0]].isna().all():
            print("  TODO: compute the Taylor Rule for each r* value.")
        else:
            print("  PASS: sensitivity analysis computed.")
    except Exception as e:
        print(f"  ERROR: {e}")

    print("\n" + "="*60)
    print("Complete all exercises before the capstone presentation.")
    print("You should be able to EXPLAIN every line of every function.")
    print("="*60)


if __name__ == "__main__":
    check()
