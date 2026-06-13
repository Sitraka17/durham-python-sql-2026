"""
ml/recession_prediction.py
==========================
MACHINE LEARNING (Block 7) — runs 100% locally, on CPU, no GPU or cloud.

CONCEPT — Supervised classification
-----------------------------------
We ask the question the whole course is built around, but now as a *prediction*
problem: given today's yield curve (and a few friends), what is the probability
the US economy is in recession within the next 12 months?

This is the classic Estrella–Mishkin "yield-curve recession probit". We use
logistic regression — the workhorse classifier — because it is:
  - interpretable (each coefficient has a sign and a meaning),
  - calibrated (it outputs a probability, not just a label),
  - tiny (trains in milliseconds on a laptop).

The punchline of the course: the 2022–24 inversion would have made this model
SCREAM recession — yet none arrived. We can see the model being "wrong" in
real time, which is exactly the economic puzzle worth discussing.

    python ml/recession_prediction.py
    # -> outputs/ml_recession_probability.png
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
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.metrics import roc_auc_score, accuracy_score, confusion_matrix

from scripts.utils import get_engine, OUTPUTS, log

NAVY, GOLD, RED, GRN, MUTED = "#002855", "#C49400", "#9B1C1C", "#0A6640", "#5A5F67"
HORIZON = 12          # predict recession within the next 12 months
FEATURES = ["spread_10_2", "real_rate", "fed_funds", "hy_spread"]
TRAIN_END = "2014-12-31"   # time-ordered split — NEVER shuffle a time series


def load() -> pd.DataFrame:
    """Pull the monthly macro panel and build the forward-looking target."""
    eng = get_engine()
    df = pd.read_sql_query(
        "SELECT date, spread_10_2, real_rate, fed_funds, hy_spread, recession "
        "FROM fred_rates ORDER BY date",
        eng, parse_dates=["date"],
    ).dropna(subset=FEATURES + ["recession"]).reset_index(drop=True)

    # TARGET: 1 if a recession occurs in ANY of the next HORIZON months.
    # We look forward, so the most recent HORIZON rows have an unknown future
    # (NaN) — we still PREDICT on them for the chart, but never TRAIN on them.
    rec = df["recession"].to_numpy()
    n = len(rec)
    y = np.full(n, np.nan)
    for i in range(n):
        future = rec[i + 1: i + 1 + HORIZON]
        if len(future) == HORIZON:                 # full 12-month future known
            y[i] = 1.0 if future.max() > 0 else 0.0
    df["y"] = y
    return df


def main():
    log.info("=== ml/recession_prediction.py — yield-curve recession model ===")
    df = load()
    log.info(f"Loaded {len(df):,} months; "
             f"{int(df['y'].sum())} positive labels (recession within {HORIZON}m)")

    known = df.dropna(subset=["y"]).copy()
    train = known[known["date"] <= TRAIN_END]
    test  = known[known["date"] >  TRAIN_END]

    Xtr, ytr = train[FEATURES], train["y"].astype(int)
    Xte, yte = test[FEATURES],  test["y"].astype(int)

    # StandardScaler + LogisticRegression in one pipeline (scale, then fit).
    model = make_pipeline(StandardScaler(),
                          LogisticRegression(max_iter=1000, class_weight="balanced"))
    model.fit(Xtr, ytr)

    # ---- Evaluation on the held-out (later) period ----
    p_te = model.predict_proba(Xte)[:, 1]
    yhat = (p_te >= 0.5).astype(int)
    auc  = roc_auc_score(yte, p_te) if yte.nunique() > 1 else float("nan")
    acc  = accuracy_score(yte, yhat)
    log.info(f"  Train: {len(train)} months ({train['date'].dt.year.min()}–"
             f"{train['date'].dt.year.max()})")
    log.info(f"  Test : {len(test)} months ({test['date'].dt.year.min()}–"
             f"{test['date'].dt.year.max()})")
    log.info(f"  Test ROC-AUC = {auc:.3f}   accuracy = {acc:.3f}")

    # Coefficients (on standardised features → comparable magnitudes)
    clf = model.named_steps["logisticregression"]
    coefs = pd.Series(clf.coef_[0], index=FEATURES).sort_values()
    log.info("  Standardised coefficients (sign = direction of risk):")
    for name, c in coefs.items():
        log.info(f"    {name:<14} {c:+.3f}")
    # >>> NOTICE: spread_10_2 should carry a strong NEGATIVE coefficient —
    # >>> a lower / inverted 10y-2y spread RAISES the recession probability.
    # >>> That is the yield-curve signal, learned straight from the data.

    # ---- Predicted probability over the WHOLE sample (incl. recent months) ----
    df["p_recession"] = model.predict_proba(df[FEATURES])[:, 1]

    plot(df, auc)

    # The 2022–24 verdict
    recent = df[df["date"] >= "2022-07-01"]
    if not recent.empty:
        log.info(f"  Mean predicted P(recession) Jul-2022→now: "
                 f"{recent['p_recession'].mean():.2f}  "
                 f"(actual recession months in that window: "
                 f"{int(recent['recession'].sum())})")
    # >>> NOTICE: a high predicted probability with ZERO realised recession
    # >>> months is the central puzzle of 2022–24 — the model trusted the
    # >>> inverted curve, the economy did not oblige. Discuss WHY.


def plot(df: pd.DataFrame, auc: float):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 7), sharex=True,
                                   gridspec_kw={"height_ratios": [2, 1]})
    fig.suptitle("Can the Yield Curve Predict Recessions? (logistic regression)\n"
                 f"Durham — Block 7 ML · held-out ROC-AUC = {auc:.2f}",
                 fontweight="bold", fontsize=12)

    # Top: predicted probability + actual recession shading
    ax1.fill_between(df["date"], 0, 1, where=df["recession"] == 1,
                     color=MUTED, alpha=0.25, label="NBER recession (actual)")
    ax1.plot(df["date"], df["p_recession"], color=RED, lw=1.4,
             label="Predicted P(recession within 12m)")
    ax1.axhline(0.5, color=MUTED, lw=0.6, ls=":")
    ax1.axvspan(pd.Timestamp("2022-07-01"), df["date"].max(),
                color=GOLD, alpha=0.10)
    ax1.set_ylabel("Probability")
    ax1.set_ylim(0, 1)
    ax1.legend(fontsize=8, loc="upper left")
    ax1.set_title("Gold band = the 2022–24 inversion: model predicts, "
                  "economy resists", loc="left", fontsize=9)

    # Bottom: the feature the model leans on most — the yield-curve spread
    ax2.axhline(0, color=RED, lw=0.8, ls="--")
    ax2.fill_between(df["date"], df["spread_10_2"], 0,
                     where=df["spread_10_2"] < 0, color=RED, alpha=0.20)
    ax2.plot(df["date"], df["spread_10_2"], color=NAVY, lw=1.0)
    ax2.set_ylabel("10y − 2y (pp)")
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax2.xaxis.set_major_locator(mdates.YearLocator(3))

    out = OUTPUTS / "ml_recession_probability.png"
    plt.tight_layout()
    plt.savefig(out, dpi=150, bbox_inches="tight")
    log.info(f"  Saved: {out}")
    plt.show()
    plt.close()


if __name__ == "__main__":
    main()
