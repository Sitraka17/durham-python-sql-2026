# 📖 New here? A plain-English (Feynman-style) explanation of every concept
# used below — Python, the economics, the ML — is in
# docs/concepts_explained.md. Read it alongside this file.
"""
ml/taylor_rule_regression.py
============================
MACHINE LEARNING (Block 7) — runs 100% locally, on CPU.

CONCEPT — Supervised regression / learning a policy reaction function
---------------------------------------------------------------------
Instead of ASSUMING the Taylor Rule coefficients (as scripts/concepts.py does),
we LEARN the Fed's actual reaction function from history with ordinary least
squares (linear regression):

        fed_funds ≈ b0 + b1·inflation + b2·output_gap

The fitted coefficients ARE an estimated Taylor Rule. The "Taylor principle"
says b1 should exceed 1 for inflation to be stabilising — we can check whether
the data agrees.

Then we do something genuinely useful: fit the rule on the PRE-PANDEMIC era
(1990–2019) and ask the model what the Fed "should" have done in 2020–2024
given its OWN historical behaviour. Where the actual rate sits far BELOW that
prediction, the Fed was "behind the curve" — the 2021–22 story, now produced by
a learned model rather than a hand-set formula.

    python ml/taylor_rule_regression.py
    # -> outputs/ml_reaction_function.png
"""
import sys as _sys, pathlib as _pl
for _p in _pl.Path(__file__).resolve().parents:
    if (_p / "scripts" / "utils.py").exists():
        if str(_p) not in _sys.path:
            _sys.path.insert(0, str(_p))
        break

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

from scripts.utils import get_engine, OUTPUTS, log

NAVY, GOLD, RED, GRN, MUTED = "#002855", "#C49400", "#9B1C1C", "#0A6640", "#5A5F67"
FEATURES = ["cpi_yoy", "output_gap_proxy"]
TRAIN_END = "2019-12-31"


def load() -> pd.DataFrame:
    eng = get_engine()
    return pd.read_sql_query(
        "SELECT date, fed_funds, cpi_yoy, output_gap_proxy "
        "FROM fred_rates ORDER BY date",
        eng, parse_dates=["date"],
    ).dropna().reset_index(drop=True)


def main():
    log.info("=== ml/taylor_rule_regression.py — learning the Fed's rule ===")
    df = load()
    train = df[df["date"] <= TRAIN_END]

    reg = LinearRegression().fit(train[FEATURES], train["fed_funds"])
    b1, b2 = reg.coef_
    b0 = reg.intercept_
    r2 = r2_score(train["fed_funds"], reg.predict(train[FEATURES]))

    log.info(f"  Estimated reaction function (1990–2019, n={len(train)}):")
    log.info(f"    fed_funds = {b0:+.2f} {b1:+.2f}·inflation {b2:+.2f}·output_gap")
    log.info(f"    R² = {r2:.3f}")
    log.info(f"  Inflation response b1 = {b1:.2f}  "
             f"(Taylor principle needs > 1: {'YES' if b1 > 1 else 'NO'})")
    # >>> NOTICE: a textbook Taylor Rule uses 1.5 on inflation. If the estimated
    # >>> b1 is well below 1, the Fed historically did NOT raise rates more than
    # >>> one-for-one with inflation — a "passive" rule that can let inflation
    # >>> drift. This is part of why 2021–22 inflation got away.

    # Counterfactual: what the learned rule implies for the WHOLE sample
    df["rule_implied"] = reg.predict(df[FEATURES])
    df["deviation"] = df["fed_funds"] - df["rule_implied"]   # <0 = behind the curve

    post = df[df["date"] > TRAIN_END]
    worst = post.loc[post["deviation"].idxmin()]
    log.info(f"  Most 'behind the curve' month post-2019: "
             f"{worst['date'].strftime('%Y-%m')} — actual {worst['fed_funds']:.2f}% "
             f"vs rule {worst['rule_implied']:.2f}% "
             f"(gap {worst['deviation']:.2f}pp)")
    # >>> NOTICE: expect early-to-mid 2022 — the rule (trained only on
    # >>> 1990–2019) implies a far higher rate than the Fed actually set.

    plot(df, (b0, b1, b2))


def plot(df: pd.DataFrame, betas):
    b0, b1, b2 = betas
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 7), sharex=True,
                                   gridspec_kw={"height_ratios": [2, 1]})
    fig.suptitle("Learning the Fed's Reaction Function with Linear Regression\n"
                 f"Durham — Block 7 ML · rule = {b0:+.1f} {b1:+.2f}·π "
                 f"{b2:+.2f}·gap (trained 1990–2019)",
                 fontweight="bold", fontsize=12)

    ax1.plot(df["date"], df["fed_funds"], color=NAVY, lw=1.6,
             label="Actual Fed Funds Rate")
    ax1.plot(df["date"], df["rule_implied"], color=GOLD, lw=1.4, ls="--",
             label="Learned reaction-function prediction")
    ax1.axvline(pd.Timestamp(TRAIN_END), color=MUTED, lw=0.8, ls=":")
    ax1.text(pd.Timestamp("2018-01-01"), df["fed_funds"].max() * 0.9,
             "← trained    predicted →", fontsize=7, color=MUTED, ha="right")
    ax1.set_ylabel("Rate (%)")
    ax1.legend(fontsize=8, loc="upper left")

    ax2.axhline(0, color=MUTED, lw=0.6)
    ax2.fill_between(df["date"], df["deviation"], 0,
                     where=df["deviation"] < 0, color=RED, alpha=0.25,
                     label="Behind the curve (actual < rule)")
    ax2.fill_between(df["date"], df["deviation"], 0,
                     where=df["deviation"] >= 0, color=GRN, alpha=0.20,
                     label="Ahead of the rule")
    ax2.plot(df["date"], df["deviation"], color=NAVY, lw=0.8)
    ax2.set_ylabel("Actual − rule (pp)")
    ax2.legend(fontsize=7, ncol=2, loc="lower left")
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax2.xaxis.set_major_locator(mdates.YearLocator(3))

    out = OUTPUTS / "ml_reaction_function.png"
    plt.tight_layout()
    plt.savefig(out, dpi=150, bbox_inches="tight")
    log.info(f"  Saved: {out}")
    plt.show()
    plt.close()


if __name__ == "__main__":
    main()
