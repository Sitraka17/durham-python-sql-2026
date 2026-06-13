# 📖 New here? A plain-English (Feynman-style) explanation of every concept
# used below — Python, the economics, the ML — is in
# docs/concepts_explained.md. Read it alongside this file.
"""
scripts/concepts.py
====================
Runnable demonstrations of every financial concept in the course.

Each concept is a self-contained function that:
  1. Explains the concept in a docstring
  2. Fetches or generates the relevant data
  3. Computes the indicator
  4. Prints an interpretation
  5. Saves a chart to outputs/

Run: python scripts/concepts.py
  or import individual functions in a notebook.

Concepts covered
----------------
  1. Fisher equation          -- real interest rate
  2. Taylor Rule              -- benchmark policy rate
  3. Yield curve shapes       -- normal, flat, inverted
  4. Term premium             -- why long rates differ from expected short rates
  5. Credit spreads           -- IG vs HY, what they measure
  6. Sacrifice ratio          -- cost of disinflation in unemployment
  7. Quantity theory (MV=PY)  -- money growth and inflation
  8. Mortgage market          -- lock-in effect and pass-through
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
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

plt.rcParams.update({
    "font.family": "serif",
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.25,
})
NAVY, GOLD, RED, GRN, MUTED = "#002855","#C49400","#9B1C1C","#0A6640","#5A5F67"


def _load_fred() -> pd.DataFrame:
    """Load the fred_rates table from macro.db."""
    engine = get_engine()
    return pd.read_sql_query(
        "SELECT * FROM fred_rates WHERE date >= '2000-01-01' "
        "AND cpi_yoy IS NOT NULL",
        engine, parse_dates=["date"]
    )


# ================================================================
# CONCEPT 1: The Fisher Equation
# ================================================================
def demo_fisher():
    """
    The Fisher Equation: r = i - pi_expected

    WHY IT MATTERS
    ---------------
    The NOMINAL interest rate (what the Fed sets) is not what drives
    economic decisions. Firms and households care about the REAL cost
    of borrowing -- the nominal rate minus the expected rate of inflation.

    If you borrow at 5% but inflation is 8%, you are being paid 3%
    in real terms to borrow money. That is NOT tight monetary policy.
    This is exactly what happened in 2021-22:
      - Fed Funds Rate: ~0%
      - CPI inflation: rising toward 9%
      - Real rate: deeply negative (accommodative, not restrictive)

    The Fed only achieved a POSITIVE real rate in mid-2023, after
    525bp of hikes. That is the real inflection point of tightening.

    FORMULA
    -------
    r_real_approximate = i_nominal - pi_expected
    (For the exact formula: (1+r) = (1+i)/(1+pi), but the approximation
    is standard in policy analysis.)

    We use realised CPI as the proxy for expected inflation (ex-post
    real rate). The market-implied version uses breakeven inflation
    from TIPS bonds (FRED: T10YIE).
    """
    print("\n" + "="*55)
    print("CONCEPT 1: The Fisher Equation")
    print("="*55)
    df = _load_fred()

    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(df["date"], df["fed_funds"], NAVY, lw=1.5, label="Nominal FFR")
    ax.plot(df["date"], df["real_rate"],  GRN,  lw=1.5, ls="--",
            label="Real FFR = nominal - CPI YoY")
    ax.fill_between(df["date"], df["real_rate"], 0,
                    where=(df["real_rate"] < 0),
                    color=RED, alpha=0.12, label="Negative real rate")
    ax.axhline(0, color="gray", lw=0.5, ls=":")
    ax.axhline(0.5, color=GOLD, lw=0.7, ls=":",
               label="Estimated neutral real rate (~0.5%)")
    ax.set_title(
        "Fisher Equation: r = i - \u03c0\n"
        "The real rate turned positive only in mid-2023",
        fontsize=10, fontweight="bold"
    )
    ax.set_ylabel("Rate (%)")
    ax.legend(fontsize=8, ncol=2, loc="upper right")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.xaxis.set_major_locator(mdates.YearLocator(2))

    # Key moment: when did real rate turn positive?
    turns_positive = df[df["real_rate"] > 0].sort_values("date")
    if not turns_positive.empty:
        last_neg = df[df["real_rate"] <= 0].iloc[-1]
        first_pos = turns_positive.iloc[0]
        print(f"  Last negative real rate: {last_neg['date'].strftime('%Y-%m')} "
              f"(real = {last_neg['real_rate']:.2f}%)")
        print(f"  First positive real rate: {first_pos['date'].strftime('%Y-%m')} "
              f"(real = {first_pos['real_rate']:.2f}%)")
        print(f"  Interpretation: policy only became restrictive in real terms"
              f" after 525bp of hikes.")

    plt.tight_layout()
    out = OUTPUTS / "concept1_fisher.png"
    plt.savefig(out, dpi=140, bbox_inches="tight")
    log.info(f"  Saved: {out}")
    plt.show(); plt.close()


# ================================================================
# CONCEPT 2: The Taylor Rule
# ================================================================
def demo_taylor_rule():
    """
    The Taylor Rule (John Taylor, 1993)

    WHY IT MATTERS
    ---------------
    The Taylor Rule is the benchmark against which central bank policy
    is judged. It says: given inflation and the output gap, here is the
    rate a well-functioning central bank SHOULD set.

    i* = pi + r* + 0.5*(pi - pi*) + 0.5*y_gap

    Where:
      pi    = current inflation
      r*    = neutral real rate (estimated 0.5-1.5%, debated)
      pi*   = target inflation = 2%
      y_gap = output gap (actual - potential GDP, % of potential)

    We approximate y_gap using Okun's law:
      y_gap = -2 * (UNRATE - NAIRU), NAIRU = 4.0%
    Okun: 1pp rise in unemployment above NAIRU = ~2pp fall in output gap.

    THE "BEHIND THE CURVE" VERDICT
    --------------------------------
    In June 2022 (CPI=9.1%, UNRATE=3.6%):
      taylor_rule = 9.1 + 0.5 + 0.5*(9.1-2) + 0.5*(-2*(3.6-4.0))
                  = 9.1 + 0.5 + 3.55 + 0.4 = 13.55%
      actual rate = 1.58%
      taylor_gap  = 13.55 - 1.58 = ~12pp

    The Fed was 12 percentage points below the Taylor Rule.
    This is the empirical basis for "the Fed was catastrophically
    behind the curve" -- not a political claim, but a model estimate.

    IMPORTANT CAVEAT
    -----------------
    The Taylor Rule is a benchmark, not a law. r* (the neutral rate)
    is unobserved. Different assumptions about r* produce different gaps.
    The Laubach-Williams model estimates r* in real time (FRED: REAINTRATREARAT10Y).
    """
    print("\n" + "="*55)
    print("CONCEPT 2: The Taylor Rule")
    print("="*55)
    df = _load_fred()

    # Print the worst "behind the curve" months
    worst = df.nlargest(5, "taylor_gap")[
        ["date", "fed_funds", "cpi_yoy", "taylor_rule", "taylor_gap"]
    ]
    print("\n  5 months most behind the curve:")
    print(worst.round(2).to_string(index=False))

    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(df["date"], df["fed_funds"],  NAVY, lw=1.5,
            label="Actual Fed Funds Rate")
    ax.plot(df["date"], df["taylor_rule"], GOLD, lw=1.5, ls="--",
            label="Taylor Rule implied rate (r*=0.5%, NAIRU=4%)")
    ax.fill_between(df["date"], df["fed_funds"], df["taylor_rule"],
                    where=(df["taylor_gap"] > 0),
                    color=RED, alpha=0.15, label="Behind the curve (gap > 0)")
    ax.fill_between(df["date"], df["fed_funds"], df["taylor_rule"],
                    where=(df["taylor_gap"] <= 0),
                    color=GRN, alpha=0.12, label="Ahead of the curve (gap <= 0)")
    ax.set_title(
        "Taylor Rule: i* = \u03c0 + r* + 0.5(\u03c0 - \u03c0*) + 0.5\u1ef9\n"
        "How far was the Fed from the Taylor Rule benchmark?",
        fontsize=10, fontweight="bold"
    )
    ax.set_ylabel("Rate (%)")
    ax.legend(fontsize=8, ncol=2, loc="upper left")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    plt.tight_layout()
    out = OUTPUTS / "concept2_taylor.png"
    plt.savefig(out, dpi=140, bbox_inches="tight")
    log.info(f"  Saved: {out}")
    plt.show(); plt.close()


# ================================================================
# CONCEPT 3: Yield Curve Shapes
# ================================================================
def demo_yield_curve_shapes():
    """
    Yield Curve Shapes: Normal, Flat, Inverted

    WHY IT MATTERS
    ---------------
    The yield curve plots the yield (interest rate) of bonds of
    the SAME issuer (US Treasury) against their maturity.

    NORMAL (upward sloping):
      Long-term yields > short-term yields.
      Investors demand extra compensation for lending longer.
      This extra compensation is the TERM PREMIUM.
      Normal conditions -> banks earn positive carry (borrow short, lend long).

    FLAT:
      Short and long yields are similar.
      Indicates uncertainty about future rates.
      Often a transition state between normal and inverted.

    INVERTED (downward sloping):
      Short-term yields > long-term yields.
      Markets expect the current short rate is ABOVE where it will be
      in the long run -> they expect RATE CUTS (because slowdown ahead).
      Historically preceded every US recession since 1955.

    THE TERM PREMIUM
    -----------------
    10y yield = (expected average 1y rate over 10 years) + term premium
    Term premium compensates for:
      - Interest rate uncertainty
      - Inflation uncertainty
      - Liquidity risk (long bonds are harder to sell quickly)
    The ACM model (NY Fed) estimates this. In 2022-23, the term premium
    turned NEGATIVE -- unusual, driven by structural demand for safe assets.

    This is part of why the inversion was so deep: the term premium
    compressed long yields even as the Fed pushed short yields up.
    """
    print("\n" + "="*55)
    print("CONCEPT 3: Yield Curve Shapes")
    print("="*55)

    df = _load_fred()

    # Select three representative dates
    scenarios = {
        "Normal (Jan 2021)":   "2021-01-01",
        "Flat (Feb 2022)":     "2022-02-01",
        "Inverted (Jul 2023)": "2023-07-01",
    }
    maturities = {"2y": "rate_2y", "10y": "rate_10y", "30y": "rate_30y"}
    colours    = {
        "Normal (Jan 2021)":   GRN,
        "Flat (Feb 2022)":     GOLD,
        "Inverted (Jul 2023)": RED,
    }

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Panel 1: Curve shapes
    for label, date_str in scenarios.items():
        row = df[df["date"] >= date_str].iloc[0]
        yields = [
            row.get("rate_2y",  np.nan),
            row.get("rate_10y", np.nan),
            row.get("rate_30y", np.nan),
        ]
        if all(pd.notna(y) for y in yields):
            ax1.plot([2, 10, 30], yields, "o-", color=colours[label],
                     lw=2, ms=7, label=label)
    ax1.set_xlabel("Maturity (years)")
    ax1.set_ylabel("Yield (%)")
    ax1.set_title("Yield Curve Shapes\n(same issuer, different maturities)",
                  fontsize=9, fontweight="bold")
    ax1.legend(fontsize=8)
    ax1.set_xticks([2, 10, 30])

    # Panel 2: 10y-2y spread over time
    ax2.axhline(0, color=RED, lw=0.9, ls="--", alpha=0.7)
    ax2.fill_between(df["date"], df["spread_10_2"], 0,
                     where=(df["spread_10_2"] < 0),
                     color=RED, alpha=0.22, label="Inverted")
    ax2.fill_between(df["date"], df["spread_10_2"], 0,
                     where=(df["spread_10_2"] >= 0),
                     color=GRN, alpha=0.10, label="Normal")
    ax2.plot(df["date"], df["spread_10_2"], NAVY, lw=0.8, alpha=0.8)
    ax2.set_ylabel("10y minus 2y spread (pp)")
    ax2.set_title("10y-2y Spread History\n(negative = inverted curve)",
                  fontsize=9, fontweight="bold")
    ax2.legend(fontsize=8)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax2.xaxis.set_major_locator(mdates.YearLocator(3))

    plt.suptitle("Concept 3: Yield Curve Shapes & the Inversion Signal",
                 fontsize=10, fontweight="bold")
    plt.tight_layout()
    out = OUTPUTS / "concept3_yield_curve.png"
    plt.savefig(out, dpi=140, bbox_inches="tight")
    log.info(f"  Saved: {out}")
    plt.show(); plt.close()


# ================================================================
# CONCEPT 4: Credit Spreads and the Tightening Paradox
# ================================================================
def demo_credit_spreads():
    """
    Credit Spreads: IG, HY, and the 2022-23 Paradox

    WHY IT MATTERS
    ---------------
    Corporate bonds do not yield the Treasury rate.
    They yield:  Treasury rate + credit spread

    The credit spread compensates investors for:
      - Default risk   (probability the borrower cannot repay)
      - Liquidity risk (harder to sell corporate bonds than Treasuries)

    Investment-Grade (IG) spread: BBB/A/AA rated companies. ~85-200bp normal.
    High-Yield (HY) spread:       BB/B/CCC rated companies. ~300-600bp normal.
    The HY-IG ratio measures relative risk appetite in the market.

    THE PARADOX
    ------------
    Standard economic theory: when the Fed hikes aggressively, credit
    spreads WIDEN (more default risk, higher risk premium demanded).
    What actually happened in 2022-23:
      - Fed hiked 525bp (fastest in 40 years)
      - IG spreads TIGHTENED from ~165bp (Oct 2022) to ~85bp (end 2023)
      - HY spreads TIGHTENED from ~600bp (Jul 2022) to ~310bp (end 2023)

    THREE REASONS this happened:
    1. Corporates had locked in long-dated cheap debt in 2020-21.
       Rising rates did not immediately raise their interest expense.
    2. Strong nominal GDP growth (real + inflation) kept revenues robust,
       supporting corporate earnings and debt coverage ratios.
    3. The labour market held firm, keeping consumer spending strong.

    This paradox explains why the "hard landing" never arrived:
    the credit channel of monetary transmission was substantially blocked.

    SACRIFICE RATIO
    ----------------
    SR = (cumulative unemployment gap) / (total inflation reduction)
    Historical US estimates: 1.0-2.0 (DeLong-Summers 1988, Ball 1994).
    2022-24 preliminary estimate: <0.5 -- historically low.
    This suggests disinflation was achieved with unusually little
    labour market pain. One explanation: supply-side reversal,
    not demand destruction, did most of the heavy lifting.
    """
    print("\n" + "="*55)
    print("CONCEPT 4: Credit Spreads & the Tightening Paradox")
    print("="*55)
    df = _load_fred()

    df_cs = df[df["hy_spread"].notna() & df["ig_spread"].notna()]

    # Print extreme values
    for col, label in [("hy_spread", "HY"), ("ig_spread", "IG")]:
        peak = df_cs.loc[df_cs[col].idxmax()]
        trough = df_cs.loc[df_cs[col].idxmin()]
        print(f"\n  {label} spread:")
        print(f"    Peak:   {peak[col]:.0f}bp on {peak['date'].strftime('%Y-%m')}")
        print(f"    Trough: {trough[col]:.0f}bp on {trough['date'].strftime('%Y-%m')}")

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 8), sharex=True)
    fig.suptitle(
        "Concept 4: Credit Spreads -- The Tightening Paradox\n"
        "HY and IG spreads TIGHTENED during the fastest rate hike cycle in 40 years",
        fontsize=10, fontweight="bold"
    )

    # Panel 1: HY spread + Fed Funds Rate
    ax1r = ax1.twinx()
    ax1.plot(df_cs["date"], df_cs["hy_spread"], RED, lw=1.2,
             label="HY spread (left)")
    ax1.axhline(600, color=RED, ls=":", lw=0.5, alpha=0.6, label="600bp stress threshold")
    ax1r.plot(df_cs["date"], df_cs["fed_funds"], NAVY, lw=1.0, ls="--",
              alpha=0.7, label="Fed Funds Rate (right)")
    ax1.set_ylabel("HY spread (bp)", color=RED)
    ax1r.set_ylabel("Fed Funds Rate (%)", color=NAVY)
    ax1.set_title("High-Yield Spread vs Fed Funds Rate", loc="left", fontsize=9)
    l1, n1 = ax1.get_legend_handles_labels()
    l2, n2 = ax1r.get_legend_handles_labels()
    ax1.legend(l1+l2, n1+n2, fontsize=7, ncol=3, loc="upper left")

    # Panel 2: IG spread
    ax2r = ax2.twinx()
    ax2.plot(df_cs["date"], df_cs["ig_spread"], NAVY, lw=1.2,
             label="IG spread (left)")
    ax2r.plot(df_cs["date"], df_cs["hy_spread"] / df_cs["ig_spread"],
              GOLD, lw=1.0, ls="--", label="HY/IG ratio (right)")
    ax2.set_ylabel("IG spread (bp)", color=NAVY)
    ax2r.set_ylabel("HY / IG ratio", color=GOLD)
    ax2.set_title("Investment-Grade Spread & HY/IG Risk Ratio",
                  loc="left", fontsize=9)
    l3, n3 = ax2.get_legend_handles_labels()
    l4, n4 = ax2r.get_legend_handles_labels()
    ax2.legend(l3+l4, n3+n4, fontsize=7, ncol=2, loc="upper left")

    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax2.xaxis.set_major_locator(mdates.YearLocator(2))
    plt.tight_layout()
    out = OUTPUTS / "concept4_credit_spreads.png"
    plt.savefig(out, dpi=140, bbox_inches="tight")
    log.info(f"  Saved: {out}")
    plt.show(); plt.close()


# ================================================================
# Run all concepts
# ================================================================
if __name__ == "__main__":
    log.info("=== Running all concept demonstrations ===")
    demo_fisher()
    demo_taylor_rule()
    demo_yield_curve_shapes()
    demo_credit_spreads()
    log.info("=== All concepts complete. Charts saved to outputs/ ===")
    print("\nCHECK YOUR OUTPUT:")
    print("  outputs/concept1_fisher.png        -- Fisher equation & real rate")
    print("  outputs/concept2_taylor.png         -- Taylor Rule & policy gap")
    print("  outputs/concept3_yield_curve.png    -- Curve shapes & spread history")
    print("  outputs/concept4_credit_spreads.png -- IG/HY spreads & paradox")
