"""
scripts/financial_indicators.py
================================
Computes and visualises the full suite of financial indicators
introduced in the course reader.

Indicators
----------
  1. Fisher real interest rate  (Block 4)
  2. Taylor Rule implied rate and gap  (Block 4)
  3. Yield curve spread + inversion episodes  (Block 3)
  4. Credit spread dashboard: IG, HY, mortgage  (Block 5)
  5. M2 money supply and velocity  (Block 5)
  6. Five-panel macro dashboard chart  (Block 5)

Usage
-----
    python scripts/financial_indicators.py
    # Outputs: outputs/financial_dashboard.png
               outputs/yield_curve_episodes.csv
               outputs/taylor_gap_history.csv
"""
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.gridspec as gridspec
import numpy as np
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

plt.rcParams.update({
    "font.family":      "serif",
    "axes.spines.top":  False,
    "axes.spines.right":False,
    "axes.grid":        True,
    "grid.alpha":       0.25,
    "grid.linewidth":   0.5,
    "axes.titlesize":   10,
    "axes.titleweight": "bold",
    "axes.labelsize":   9,
    "xtick.labelsize":  8,
    "ytick.labelsize":  8,
})

NAVY  = "#002855"
GOLD  = "#C49400"
RED   = "#9B1C1C"
GREEN = "#0A6640"
MUTED = "#5A5F67"


# ----------------------------------------------------------------
# 1.  Load from database
# ----------------------------------------------------------------
def load_all(start: str = "2000-01-01") -> pd.DataFrame:
    engine = get_engine()
    df = pd.read_sql_query(
        f"SELECT * FROM v_credit_dashboard WHERE date >= '{start}'",
        engine, parse_dates=["date"]
    )
    # Merge Taylor Rule columns from fred_rates
    # m2_yoy already comes from v_credit_dashboard; don't re-select it here
    # or the merge would collide (m2_yoy_x / m2_yoy_y).
    tr = pd.read_sql_query(
        f"SELECT date, taylor_rule, taylor_gap, "
        f"       cpi_yoy, core_pce, unemployment "
        f"FROM fred_rates WHERE date >= '{start}'",
        engine, parse_dates=["date"]
    )
    df = df.merge(tr, on="date", how="left")
    # 12-month moving average of the 10y-2y spread (same definition as the
    # v_yield_curve view; recomputed here so this script only needs one view).
    df["ma12_spread"] = (df["spread_10_2"]
                         .rolling(12, min_periods=1).mean().round(3))
    log.info(f"Loaded {len(df):,} rows from macro.db")
    return df


# ----------------------------------------------------------------
# 2.  Yield curve inversion episodes
# ----------------------------------------------------------------
def yield_curve_episodes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Identify every contiguous inversion episode.
    Returns a summary DataFrame with start, end, depth, duration.
    """
    df = df[["date", "spread_10_2", "inverted"]].dropna().copy()
    df["episode_start"] = (
        df["inverted"] - df["inverted"].shift(1, fill_value=0)
    ).clip(lower=0)
    df["episode_id"] = df["episode_start"].cumsum()

    episodes = []
    for eid, grp in df[df["inverted"] == 1].groupby("episode_id"):
        episodes.append({
            "episode_id":    int(eid),
            "start_date":    grp["date"].iloc[0].strftime("%Y-%m"),
            "end_date":      grp["date"].iloc[-1].strftime("%Y-%m"),
            "months":        len(grp),
            "deepest_bp":    round(grp["spread_10_2"].min() * 100, 1),
            "avg_spread_bp": round(grp["spread_10_2"].mean() * 100, 1),
        })
    out = pd.DataFrame(episodes).sort_values("deepest_bp")
    return out


# ----------------------------------------------------------------
# 3.  Taylor Rule summary statistics
# ----------------------------------------------------------------
def taylor_summary(df: pd.DataFrame) -> pd.DataFrame:
    d = df[["date", "fed_funds", "taylor_rule", "taylor_gap",
            "cpi_yoy"]].dropna()
    d["behind_curve"] = (d["taylor_gap"] > 2).astype(int)
    d["ahead_curve"]  = (d["taylor_gap"] < -2).astype(int)
    return d


# ----------------------------------------------------------------
# 4.  Five-panel dashboard chart
# ----------------------------------------------------------------
def plot_dashboard(df: pd.DataFrame, start: str = "2000-01-01") -> None:
    df = df[df["date"] >= start].copy()

    fig = plt.figure(figsize=(14, 13))
    fig.suptitle(
        "US Monetary Policy & Financial Markets Dashboard\n"
        "Durham University — Advanced Python & SQL for Economists",
        fontsize=12, fontweight="bold", y=0.98,
    )

    gs = gridspec.GridSpec(5, 1, figure=fig,
                           hspace=0.45, left=0.09, right=0.97,
                           top=0.93, bottom=0.05)

    # ----------------------------------------------------------
    # Panel 1: Policy rates — nominal, real, Taylor Rule
    # ----------------------------------------------------------
    ax1 = fig.add_subplot(gs[0])
    ax1.plot(df["date"], df["fed_funds"],   color=NAVY, lw=1.4,
             label="Federal Funds Rate")
    ax1.plot(df["date"], df["real_rate"],   color=GREEN, lw=1.0,
             linestyle="--", label="Real FFR (Fisher)")
    ax1.plot(df["date"], df["taylor_rule"], color=GOLD, lw=1.4,
             label="Taylor Rule implied rate")
    ax1.axhline(0, color=MUTED, lw=0.5, linestyle=":")
    ax1.fill_between(df["date"], df["fed_funds"], df["taylor_rule"],
                     where=(df["taylor_gap"] > 0),
                     color=RED, alpha=0.12, label="Behind curve")
    ax1.fill_between(df["date"], df["fed_funds"], df["taylor_rule"],
                     where=(df["taylor_gap"] < 0),
                     color=GREEN, alpha=0.12, label="Ahead of curve")
    ax1.set_ylabel("Rate (%)")
    ax1.set_title("Panel 1 — Nominal, Real & Taylor Rule Policy Rate")
    ax1.legend(fontsize=7, ncol=3, loc="upper left")

    # ----------------------------------------------------------
    # Panel 2: Yield curve spread
    # ----------------------------------------------------------
    ax2 = fig.add_subplot(gs[1])
    ax2.axhline(0, color=RED, lw=0.9, linestyle="--", alpha=0.8)
    ax2.fill_between(df["date"], df["spread_10_2"], 0,
                     where=(df["spread_10_2"] < 0),
                     color=RED, alpha=0.22, label="Inverted")
    ax2.fill_between(df["date"], df["spread_10_2"], 0,
                     where=(df["spread_10_2"] >= 0),
                     color=NAVY, alpha=0.10, label="Normal")
    ax2.plot(df["date"], df["spread_10_2"], color=NAVY, lw=0.8)
    ax2.plot(df["date"], df["ma12_spread"], color=GOLD, lw=1.8,
             label="12m MA")
    # Annotate trough
    trough_row = df.loc[df["spread_10_2"].idxmin()]
    ax2.annotate(
        f"Trough: {trough_row['spread_10_2']:.2f} pp\n{trough_row['date'].strftime('%b %Y')}",
        xy=(trough_row["date"], trough_row["spread_10_2"]),
        xytext=(30, -20), textcoords="offset points",
        fontsize=7, color=RED, arrowprops=dict(arrowstyle="->", color=RED, lw=0.8)
    )
    ax2.set_ylabel("Spread (pp)")
    ax2.set_title("Panel 2 — 10y – 2y Treasury Yield Spread")
    ax2.legend(fontsize=7, ncol=3, loc="upper right")

    # ----------------------------------------------------------
    # Panel 3: Credit spreads (IG and HY)
    # ----------------------------------------------------------
    ax3 = fig.add_subplot(gs[2])
    ax3_r = ax3.twinx()

    hy_ok = df["hy_spread"].notna()
    ig_ok = df["ig_spread"].notna()

    ax3.plot(df.loc[hy_ok, "date"], df.loc[hy_ok, "hy_spread"],
             color=RED, lw=1.0, label="HY spread (left)")
    ax3.plot(df.loc[hy_ok, "date"], df.loc[hy_ok, "ma12_hy_spread"],
             color=RED, lw=1.8, linestyle="--", label="HY 12m MA (left)")
    ax3_r.plot(df.loc[ig_ok, "date"], df.loc[ig_ok, "ig_spread"],
               color=NAVY, lw=1.0, label="IG spread (right)", alpha=0.7)
    ax3.set_ylabel("HY spread (bp)", color=RED)
    ax3_r.set_ylabel("IG spread (bp)", color=NAVY)
    ax3.set_title("Panel 3 — Credit Spreads: High-Yield & Investment-Grade")
    lines1, labels1 = ax3.get_legend_handles_labels()
    lines2, labels2 = ax3_r.get_legend_handles_labels()
    ax3.legend(lines1 + lines2, labels1 + labels2, fontsize=7, ncol=3,
               loc="upper right")

    # ----------------------------------------------------------
    # Panel 4: Mortgage rate and spread
    # ----------------------------------------------------------
    ax4 = fig.add_subplot(gs[3])
    m_ok = df["mortgage_30y"].notna()
    ax4.plot(df.loc[m_ok, "date"], df.loc[m_ok, "mortgage_30y"],
             color=NAVY, lw=1.2, label="30y Mortgage Rate")
    ax4.plot(df.loc[m_ok, "date"], df.loc[m_ok, "rate_10y"],
             color=GOLD, lw=1.0, linestyle="--", label="10y Treasury")
    ax4.fill_between(
        df.loc[m_ok, "date"],
        df.loc[m_ok, "mortgage_30y"], df.loc[m_ok, "rate_10y"],
        color=MUTED, alpha=0.15, label="Mortgage spread"
    )
    ax4.set_ylabel("Rate (%)")
    ax4.set_title("Panel 4 — 30-Year Mortgage Rate & Spread Over 10y Treasury")
    ax4.legend(fontsize=7, ncol=3, loc="upper left")

    # ----------------------------------------------------------
    # Panel 5: CPI and M2 growth
    # ----------------------------------------------------------
    ax5 = fig.add_subplot(gs[4])
    ax5_r = ax5.twinx()
    cpi_ok = df["cpi_yoy"].notna()
    m2_ok  = df["m2_yoy"].notna()
    ax5.plot(df.loc[cpi_ok, "date"], df.loc[cpi_ok, "cpi_yoy"],
             color=RED, lw=1.2, label="CPI YoY (left)")
    ax5.axhline(2, color=RED, lw=0.5, linestyle=":", alpha=0.6)
    ax5_r.plot(df.loc[m2_ok, "date"], df.loc[m2_ok, "m2_yoy"],
               color=GREEN, lw=1.0, alpha=0.8, label="M2 YoY growth (right)")
    ax5_r.axhline(0, color=MUTED, lw=0.5, linestyle=":")
    ax5.set_ylabel("CPI YoY (%)", color=RED)
    ax5_r.set_ylabel("M2 growth (%)", color=GREEN)
    ax5.set_title("Panel 5 — CPI Inflation and M2 Money Supply Growth (QTM)")
    lines1, labels1 = ax5.get_legend_handles_labels()
    lines2, labels2 = ax5_r.get_legend_handles_labels()
    ax5.legend(lines1 + lines2, labels1 + labels2, fontsize=7, ncol=2,
               loc="upper left")

    # Format all x-axes
    for ax in [ax1, ax2, ax3, ax4, ax5]:
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        ax.xaxis.set_major_locator(mdates.YearLocator(2))
        ax.xaxis.set_tick_params(rotation=0)

    out = OUTPUTS / "financial_dashboard.png"
    plt.savefig(out, dpi=160, bbox_inches="tight")
    log.info(f"Saved financial dashboard to {out}")
    plt.show()
    plt.close()


# ----------------------------------------------------------------
# Main
# ----------------------------------------------------------------
if __name__ == "__main__":
    log.info("=== financial_indicators.py ===")

    df = load_all()

    # Inversion episodes
    episodes = yield_curve_episodes(df)
    log.info(f"\nYield curve inversion episodes:\n{episodes.to_string(index=False)}")
    ep_out = OUTPUTS / "yield_curve_episodes.csv"
    episodes.to_csv(ep_out, index=False)
    log.info(f"Saved to {ep_out}")

    # Taylor Rule history
    taylor_df = taylor_summary(df)
    t_out = OUTPUTS / "taylor_gap_history.csv"
    taylor_df.to_csv(t_out, index=False)
    log.info(f"Taylor gap saved to {t_out}")

    # Dashboard
    plot_dashboard(df)
    log.info("=== Done ===")
