"""
scripts/pipeline.py
===================
Block 5 deliverable: the complete ETL pipeline.

  EXTRACT   -> FRED API (or CSV fallback)
  TRANSFORM -> pandas: clean, reshape, compute indicators
  LOAD      -> SQLite via SQLAlchemy
  QUERY     -> Analytical SQL via read_sql_query()
  VISUALISE -> matplotlib three-panel chart

This script is self-contained: it can be run independently of
setup_db.py (it writes its own table `fred_macro`).

Usage
-----
    python scripts/pipeline.py
    # Output: outputs/yield_curve_dashboard.png
"""
import pandas as pd
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
from scripts.fetch_fred import fetch

START = "2000-01-01"
TABLE = "fred_macro"

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

# ----------------------------------------------------------------
# Analytical SQL — runs against fred_macro after LOAD step
# ----------------------------------------------------------------
SQL = f"""
WITH spread AS (
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
        AVG(spread_10_2)
            OVER (ORDER BY date
                  ROWS BETWEEN 11 PRECEDING AND CURRENT ROW) AS ma12_spread,
        -- Cumulative months of inversion (running total)
        SUM(inverted)
            OVER (ORDER BY date
                  ROWS UNBOUNDED PRECEDING)                  AS cum_inv_months,
        -- Year-on-year change in HY spread (stress signal)
        ROUND(
            hy_spread - LAG(hy_spread, 12) OVER (ORDER BY date),
            0
        )                                                    AS hy_spread_yoy
    FROM {TABLE}
    WHERE date >= '{START}'
)
SELECT * FROM spread ORDER BY date
"""


# ----------------------------------------------------------------
# Pipeline steps
# ----------------------------------------------------------------
def extract() -> pd.DataFrame:
    log.info("[1/5] EXTRACT")
    return fetch(start=START)


def transform(raw: pd.DataFrame) -> pd.DataFrame:
    log.info("[2/5] TRANSFORM")
    return (
        raw
        .assign(date=lambda x: pd.to_datetime(x["date"]))
        .query("date >= @START")
        .dropna(subset=["fed_funds", "rate_10y", "rate_2y"])
        .reset_index(drop=True)
    )


def load(df: pd.DataFrame) -> None:
    log.info(f"[3/5] LOAD  — {len(df):,} rows -> {TABLE}")
    engine = get_engine()
    df.to_sql(TABLE, engine, if_exists="replace", index=False)


def query() -> pd.DataFrame:
    log.info("[4/5] QUERY")
    engine  = get_engine()
    result  = pd.read_sql_query(SQL, engine, parse_dates=["date"])
    log.info(f"      {len(result):,} rows returned")
    return result


def visualise(df: pd.DataFrame) -> None:
    log.info("[5/5] VISUALISE")
    fig, axes = plt.subplots(3, 1, figsize=(12, 9), sharex=True)
    fig.suptitle(
        "US Monetary Policy Dashboard — Block 5 Pipeline Output\n"
        "Durham University · Advanced Python & SQL · June 2026",
        fontsize=11, fontweight="bold", y=0.99,
    )

    # Panel 1: Yield curve spread
    ax1 = axes[0]
    ax1.axhline(0, color=RED, lw=0.8, linestyle="--", alpha=0.7)
    ax1.fill_between(df["date"], df["spread_10_2"], 0,
                     where=(df["spread_10_2"] < 0),
                     color=RED, alpha=0.20, label="Inversion")
    ax1.fill_between(df["date"], df["spread_10_2"], 0,
                     where=(df["spread_10_2"] >= 0),
                     color=NAVY, alpha=0.08)
    ax1.plot(df["date"], df["spread_10_2"], color=NAVY, lw=0.8, alpha=0.7)
    ax1.plot(df["date"], df["ma12_spread"], color=GOLD, lw=2.0,
             label="12-month MA")
    ax1.set_ylabel("Spread (pp)")
    ax1.set_title("Yield Curve Spread — 10y minus 2y Treasury", loc="left")
    ax1.legend(fontsize=8, loc="upper right")

    # Panel 2: Real rate vs Taylor Rule gap
    ax2 = axes[1]
    ax2.axhline(0, color="gray", lw=0.4, linestyle=":")
    ax2.plot(df["date"], df["real_rate"],  color=NAVY, lw=1.2,
             label="Real FFR (Fisher)")
    ax2.plot(df["date"], df["taylor_gap"], color=RED,  lw=1.0,
             linestyle="--", label="Taylor Rule gap")
    ax2.fill_between(df["date"], df["taylor_gap"], 0,
                     where=(df["taylor_gap"] > 0),
                     color=RED, alpha=0.12, label="Behind curve")
    ax2.set_ylabel("Rate (%)")
    ax2.set_title("Real Interest Rate & Taylor Rule Policy Gap", loc="left")
    ax2.legend(fontsize=8, loc="upper right")

    # Panel 3: Credit spreads
    ax3 = axes[2]
    ax3r = ax3.twinx()
    hy  = df["hy_spread"].notna()
    ig  = df["ig_spread"].notna()
    ax3.plot(df.loc[hy, "date"], df.loc[hy, "hy_spread"], color=RED, lw=1.0,
             label="HY spread (left)")
    ax3r.plot(df.loc[ig, "date"], df.loc[ig, "ig_spread"], color=NAVY, lw=0.9,
              alpha=0.75, label="IG spread (right)")
    ax3.set_ylabel("HY spread (bp)", color=RED)
    ax3r.set_ylabel("IG spread (bp)", color=NAVY)
    ax3.set_title("Corporate Credit Spreads — HY & IG", loc="left")
    lines = (ax3.get_legend_handles_labels()[0]
             + ax3r.get_legend_handles_labels()[0])
    labels = (ax3.get_legend_handles_labels()[1]
              + ax3r.get_legend_handles_labels()[1])
    ax3.legend(lines, labels, fontsize=8, loc="upper right")

    for ax in axes:
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        ax.xaxis.set_major_locator(mdates.YearLocator(2))

    plt.tight_layout()
    out = OUTPUTS / "yield_curve_dashboard.png"
    plt.savefig(out, dpi=160, bbox_inches="tight")
    log.info(f"Saved to {out}")
    plt.show()
    plt.close()


# ----------------------------------------------------------------
# Main
# ----------------------------------------------------------------
if __name__ == "__main__":
    log.info("=== pipeline.py — Block 5 ETL ===")
    raw    = extract()
    clean  = transform(raw)
    load(clean)
    result = query()
    visualise(result)
    log.info("=== Pipeline complete ===")
