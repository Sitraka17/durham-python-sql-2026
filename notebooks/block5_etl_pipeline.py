"""
notebooks/block5_etl_pipeline.py
=================================
BLOCK 5 -- Python x SQL: Building the Monitoring System
"Can we automate this analysis so it runs every Monday morning?"

CONCEPT OF THIS BLOCK
At the Bank of England, the Fed, and every major macro hedge fund,
there is a system that:
  1. Fetches fresh data automatically (EXTRACT)
  2. Cleans and computes derived indicators (TRANSFORM)
  3. Stores the results in a database (LOAD)
  4. Runs analytical queries against the stored data (QUERY)
  5. Produces a chart for the morning briefing (VISUALISE)

This is the ETL pattern (Extract, Transform, Load).
You are going to build a minimal version of it in this notebook.

By the end you will have:
  - A 5-function pipeline (one function per step)
  - A SQL query running INSIDE Python (read_sql_query)
  - A 3-panel chart produced automatically from fresh data
  - An understanding of WHEN to use Python vs SQL at each step

Run: python notebooks/block5_etl_pipeline.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from sqlalchemy import text

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
from scripts.fetch_fred import fetch   # reuse our Block 4 fetch function

plt.rcParams.update({
    "font.family": "serif",
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.25,
})
NAVY, GOLD, RED, GRN, MUTED = "#002855", "#C49400", "#9B1C1C", "#0A6640", "#5A5F67"

START = "2000-01-01"
TABLE = "block5_macro"   # private table for this notebook


# ================================================================
# CONCEPT: Why separate functions?
# ================================================================
# We could write this entire pipeline in one function.
# We don't, for three reasons:
#
# 1. TESTABILITY: each function can be tested independently.
#    If LOAD fails, you know exactly where to look.
#
# 2. REUSABILITY: fetch() is already written in scripts/fetch_fred.py.
#    We import it rather than rewrite it. DRY principle (Don't Repeat Yourself).
#
# 3. READABILITY: the main() function at the bottom reads like English:
#    raw = extract() -> clean = transform(raw) -> load(clean) -> ...
#    A new reader understands the architecture in 10 seconds.


# ================================================================
# STEP 1: EXTRACT -- get raw data
# ================================================================
def extract(start: str = START) -> pd.DataFrame:
    """
    Fetch all FRED series.

    CONCEPT: We do NOT compute any derived indicators here.
    Extract = "get the raw data exactly as the source provides it."
    Transformation is a separate step.

    This is important because:
    - You might want to store the raw data for auditing.
    - If your transformation has a bug, you can re-run it without
      re-fetching (which may be slow or rate-limited).
    """
    log.info("[1/5] EXTRACT: fetching FRED data...")
    df = fetch(start=start)
    log.info(f"       {len(df):,} rows fetched, {df.shape[1]} columns")
    return df


# ================================================================
# STEP 2: TRANSFORM -- clean and compute
# ================================================================
def transform(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the raw data and compute all derived indicators.

    CONCEPT: The transform step is where Python shines.
    We use method chaining to build a readable pipeline.
    Each .assign() adds ONE new concept with a clear name.

    After transform(), the DataFrame is ready to be stored and queried.
    We never put business logic in the extract or load steps.
    """
    log.info("[2/5] TRANSFORM: computing indicators...")

    # CONCEPT: .pipe() lets you call a standalone function within a chain.
    # Instead of: df2 = my_function(df1), you can write: df.pipe(my_function)
    # Useful for complex transformations that deserve their own function.
    def add_inversion_episodes(df: pd.DataFrame) -> pd.DataFrame:
        """
        Add a running count of inversion months.
        Each month's value = total months inverted UP TO that point.
        This is the PANDAS equivalent of:
          SUM(inverted) OVER (ORDER BY date ROWS UNBOUNDED PRECEDING)
        """
        df = df.copy()
        if "inverted" in df.columns:
            df["cum_inv_months"] = df["inverted"].cumsum()
        return df

    result = (
        df
        .assign(date=lambda x: pd.to_datetime(x["date"]))
        .query(f"date >= '{START}'")
        .dropna(subset=["fed_funds", "rate_10y", "rate_2y"])
        .sort_values("date")
        .pipe(add_inversion_episodes)
        .reset_index(drop=True)
    )
    log.info(f"       {len(result):,} rows after transform")
    return result


# ================================================================
# STEP 3: LOAD -- write to the database
# ================================================================
def load(df: pd.DataFrame) -> None:
    """
    Write the transformed DataFrame to SQLite.

    CONCEPT: DataFrame.to_sql() is the Python -> SQL bridge.
    Parameters:
      name       = table name
      con        = SQLAlchemy engine (not a sqlite3 connection directly)
      if_exists  = 'replace' overwrites the table on each run.
                   'append' adds rows without deleting existing ones.
                   'fail'   raises an error if the table exists.
      index      = False -- don't write the pandas RangeIndex as a column.

    CONCEPT: Why SQLite instead of CSV?
    - You can run SQL queries against it (window functions, JOINs).
    - Multiple Python scripts can read it simultaneously.
    - It does not load everything into memory.
    - It is portable -- one file you can share.
    """
    log.info(f"[3/5] LOAD: writing {len(df):,} rows to {TABLE}...")
    engine = get_engine()
    df.to_sql(TABLE, engine, if_exists="replace", index=False)
    log.info(f"       Table '{TABLE}' written to macro.db")


# ================================================================
# STEP 4: QUERY -- analytical SQL inside Python
# ================================================================

# CONCEPT: Analytical SQL belongs in SQL, not in Python.
# We could compute moving averages and episode counts in pandas.
# But we ALREADY know how to do this in SQL (Block 3!).
# The professional pattern: store data in SQL, analyse in SQL,
# bring results back into Python only for visualisation.
#
# pandas.read_sql_query() runs a SQL query against a database
# and returns the results as a DataFrame.
# The query is a normal SQL string -- you can write it exactly
# as you would in VS Code SQLite Viewer.

DASHBOARD_QUERY = f"""
WITH

-- Step 1: compute the yield spread and all derived metrics
spread AS (
    SELECT
        date,
        fed_funds,
        real_rate,
        spread_10_2,
        inverted,
        taylor_rule,
        taylor_gap,
        hy_spread,
        ig_spread,
        -- 12-month moving average of yield spread
        -- NOTICE: this is window SQL running inside Python via read_sql_query()
        ROUND(
            AVG(spread_10_2)
            OVER (ORDER BY date
                  ROWS BETWEEN 11 PRECEDING AND CURRENT ROW)
        , 3)                                           AS ma12_spread,
        -- Year-on-year change in HY spread (credit stress signal)
        ROUND(
            hy_spread - LAG(hy_spread, 12) OVER (ORDER BY date),
            0
        )                                              AS hy_spread_yoy,
        -- Running count of inversion months
        SUM(inverted)
            OVER (ORDER BY date ROWS UNBOUNDED PRECEDING) AS total_inv_months
    FROM {TABLE}
    WHERE date >= '{START}'
)

SELECT * FROM spread ORDER BY date
"""


def query() -> pd.DataFrame:
    """
    Run analytical SQL and return results as a DataFrame.

    CONCEPT: Python calls SQL; SQL does the analysis; Python gets results.
    This is the key integration pattern.

    The DASHBOARD_QUERY string above is exactly what you would run
    in VS Code SQLite Viewer -- just passed as a string to Python.
    """
    log.info("[4/5] QUERY: running analytical SQL...")
    engine = get_engine()
    result = pd.read_sql_query(DASHBOARD_QUERY, engine, parse_dates=["date"])
    log.info(f"       {len(result):,} rows returned from SQL")

    # Print a summary of the most important moments
    if "taylor_gap" in result.columns:
        max_gap = result.loc[result["taylor_gap"].idxmax()]
        log.info(f"\n  Peak Taylor gap: {max_gap['taylor_gap']:.1f}pp "
                 f"on {max_gap['date'].strftime('%Y-%m')}")
        log.info(f"  (The Fed was {max_gap['taylor_gap']:.1f}pp BELOW the Taylor Rule)")

    if "spread_10_2" in result.columns:
        trough = result.loc[result["spread_10_2"].idxmin()]
        log.info(f"\n  Deepest inversion: {trough['spread_10_2']:.3f}pp "
                 f"= {trough['spread_10_2']*100:.0f}bp "
                 f"on {trough['date'].strftime('%Y-%m')}")

    return result


# ================================================================
# STEP 5: VISUALISE -- the morning briefing chart
# ================================================================
def visualise(result: pd.DataFrame) -> None:
    """
    Produce a 3-panel dashboard chart from the SQL query result.

    CONCEPT: Visualisation is the LAST step, not the first.
    Many students jump straight to plotting before understanding the data.
    The correct order: understand (SQL) -> compute (Python) -> show (matplotlib).

    Each panel tells one part of the story:
    Panel 1: Where was the yield curve?  -> inversion depth and duration
    Panel 2: Was policy actually tight?  -> real rate + Taylor gap
    Panel 3: What were markets pricing? -> credit spreads (IG + HY)
    """
    log.info("[5/5] VISUALISE: generating dashboard chart...")

    fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
    fig.suptitle(
        "Block 5 Output: Full ETL Pipeline Dashboard\n"
        "Did the Fed's tightening cycle work? (2000-2026)",
        fontsize=11, fontweight="bold", y=0.99
    )

    # --------------------------------------------------------
    # PANEL 1: Yield curve spread
    # --------------------------------------------------------
    ax1 = axes[0]

    # fill_between creates the visual area under/over a line.
    # 'where' is a boolean Series that controls WHERE the fill applies.
    ax1.axhline(0, color=RED, lw=0.9, ls="--", alpha=0.7)
    ax1.fill_between(result["date"], result["spread_10_2"], 0,
                     where=(result["spread_10_2"] < 0),
                     color=RED, alpha=0.22, label="Inverted")
    ax1.fill_between(result["date"], result["spread_10_2"], 0,
                     where=(result["spread_10_2"] >= 0),
                     color=NAVY, alpha=0.08)
    ax1.plot(result["date"], result["spread_10_2"],
             color=NAVY, lw=0.8, alpha=0.7)
    ax1.plot(result["date"], result["ma12_spread"],
             color=GOLD, lw=2.0, label="12-month MA")

    # Annotate the trough -- teaching the reader where to look
    if "spread_10_2" in result.columns:
        trough_i   = result["spread_10_2"].idxmin()
        trough_row = result.iloc[trough_i]
        ax1.annotate(
            f"{trough_row['spread_10_2']*100:.0f} bp\n"
            f"{trough_row['date'].strftime('%b %Y')}\nDeepest since 1981",
            xy=(trough_row["date"], trough_row["spread_10_2"]),
            xytext=(40, -18), textcoords="offset points",
            fontsize=7, color=RED,
            arrowprops=dict(arrowstyle="->", color=RED, lw=0.8)
        )

    ax1.set_ylabel("Spread (pp)")
    ax1.set_title("Yield Curve: 10y minus 2y Treasury", loc="left", fontsize=9)
    ax1.legend(fontsize=7, ncol=3, loc="upper right")

    # --------------------------------------------------------
    # PANEL 2: Real rate and Taylor Rule gap
    # --------------------------------------------------------
    ax2 = axes[1]
    rr = result["real_rate"].notna()
    tg = result["taylor_gap"].notna()
    ax2.axhline(0, color="gray", lw=0.4, ls=":")
    ax2.plot(result.loc[rr, "date"], result.loc[rr, "real_rate"],
             color=GRN, lw=1.2, label="Real FFR (Fisher)")
    ax2.fill_between(result.loc[rr, "date"], result.loc[rr, "real_rate"], 0,
                     where=(result.loc[rr, "real_rate"] < 0),
                     color=GRN, alpha=0.12, label="Negative real rate")

    # Taylor gap on the same panel with a secondary axis
    ax2r = ax2.twinx()
    ax2r.plot(result.loc[tg, "date"], result.loc[tg, "taylor_gap"],
              color=RED, lw=1.0, ls="--", alpha=0.8,
              label="Taylor gap (right)")
    ax2r.axhline(0, color=RED, lw=0.3, ls=":")
    ax2r.set_ylabel("Taylor gap (pp)", color=RED)

    ax2.set_ylabel("Real FFR (%)")
    ax2.set_title("Real Interest Rate & Taylor Rule Gap -- policy stance",
                  loc="left", fontsize=9)
    l2a, n2a = ax2.get_legend_handles_labels()
    l2b, n2b = ax2r.get_legend_handles_labels()
    ax2.legend(l2a+l2b, n2a+n2b, fontsize=7, ncol=3, loc="upper left")

    # --------------------------------------------------------
    # PANEL 3: Credit spreads
    # --------------------------------------------------------
    ax3 = axes[2]
    ax3r = ax3.twinx()

    hy = result["hy_spread"].notna()
    ig = result["ig_spread"].notna()

    ax3.plot(result.loc[hy, "date"], result.loc[hy, "hy_spread"],
             color=RED, lw=1.0, label="HY spread (left, bp)")
    ax3r.plot(result.loc[ig, "date"], result.loc[ig, "ig_spread"],
              color=NAVY, lw=0.9, alpha=0.7, label="IG spread (right, bp)")

    # Add reference lines for crisis levels
    ax3.axhline(600, color=RED,  lw=0.5, ls=":", alpha=0.6)
    ax3r.axhline(200, color=NAVY, lw=0.5, ls=":", alpha=0.6)

    ax3.set_ylabel("HY spread (bp)", color=RED)
    ax3r.set_ylabel("IG spread (bp)", color=NAVY)
    ax3.set_title("Credit Spreads: IG & HY -- what markets were pricing",
                  loc="left", fontsize=9)
    l3a, n3a = ax3.get_legend_handles_labels()
    l3b, n3b = ax3r.get_legend_handles_labels()
    ax3.legend(l3a+l3b, n3a+n3b, fontsize=7, ncol=2, loc="upper right")

    for ax in axes:
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        ax.xaxis.set_major_locator(mdates.YearLocator(2))

    plt.tight_layout()
    out = OUTPUTS / "block5_dashboard.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    log.info(f"  Saved: {out}")
    plt.show()
    plt.close()


# ================================================================
# MAIN -- the pipeline orchestrator
# ================================================================
def main():
    """
    Run the full pipeline.

    CONCEPT: This function reads like a specification.
    You can understand what the pipeline does without reading
    any of the implementation details.
    This is called the "composition pattern" -- each step is a
    composable function, and main() composes them.
    """
    log.info("=" * 55)
    log.info("Block 5 ETL Pipeline")
    log.info("=" * 55)

    raw    = extract()
    clean  = transform(raw)
    load(clean)
    result = query()
    visualise(result)

    log.info("=" * 55)
    log.info("Pipeline complete.")
    log.info("=" * 55)

    # Interpretation guide
    print("""
ECONOMIC INTERPRETATION OF YOUR OUTPUT:

Panel 1 -- Yield curve:
  The 2022-24 inversion (red shading) was the longest on record
  and reached -109 bp. Historical median lead to recession: ~14 months.
  But no NBER recession followed as of 2026.

Panel 2 -- Real rate + Taylor gap:
  Find the month real_rate turned positive (mid-2023).
  That is when policy ACTUALLY became restrictive.
  The Taylor gap peak (red dashes) shows the Fed was far behind the curve
  through most of 2022.

Panel 3 -- Credit spreads:
  Notice that HY spreads TIGHTENED in 2023 even as rates peaked.
  This is the "tightening paradox": credit markets did not price in
  recession risk despite the deepest yield curve inversion in 40 years.
  Explanation: corporates had locked in long-dated cheap debt in 2020-21.
  Rising rates did not immediately hit their interest expense.
""")


# ================================================================
# EXERCISE
# ================================================================
print("""
EXERCISE (25 minutes -- the capstone warm-up)

The pipeline you just ran computes and stores 5 indicators.
Your task: add a SIXTH indicator to the pipeline and show it on the chart.

Choose one:

Option A: M2 annual growth (quantity theory test)
  Definition: m2.pct_change(12) * 100
  Add to transform(), store in TABLE, add a Panel 4 to the chart.
  Economic question: does M2 growth in year T predict CPI in year T+1.5?
  Test it by plotting M2 YoY with an 18-month forward shift against CPI.

Option B: Unemployment rate of change (labour market stress)
  Definition: unemployment.diff(6)  (6-month change)
  Positive = unemployment rising (labour market weakening).
  Find the months in 2022-24 where this was most positive.
  Is there a lag between the real rate turning positive and unemployment
  starting to rise?

Option C: Mortgage market lock-in index
  Definition: (mortgage_30y - mortgage_30y.shift(24))  <- 2-year change
  When this is large and positive, many homeowners are "locked in" to
  their old lower-rate mortgage and will not sell their home to get a
  new one at a higher rate. This suppresses housing supply.
  Plot this against the Fed Funds Rate on a shared timeline.

Scaffold for the transform() function:
  def transform(df):
      return (
          df
          ... (existing code) ...
          .assign(
              YOUR_INDICATOR = lambda x: ???
          )
      )

After implementing:
  - Explain the economic meaning in one sentence.
  - State one thing the chart shows that surprised you.
""")


if __name__ == "__main__":
    main()
