"""
ml/recession_prediction.py
==========================
MACHINE LEARNING (Block 7) — runs 100% locally, on CPU, no GPU or cloud.

CONCEPT — Supervised classification, done honestly on a time series
-------------------------------------------------------------------
We ask the question the whole course is built around as a *prediction* problem:
given today's yield curve (and a few friends), what is the probability the US
economy is in recession within the next 12 months? This is the classic
Estrella–Mishkin "yield-curve recession probit".

What this script teaches beyond "fit a model":
  1. NEVER shuffle a time series. We evaluate with walk-forward
     cross-validation (sklearn's TimeSeriesSplit): always train on the past,
     test on the future. Shuffling would leak the future into the past and
     give a dishonestly high score.
  2. SIMPLE vs COMPLEX. We pit an interpretable logistic regression against a
     random forest. On macro data with few features the fancy model rarely
     wins — a result worth internalising before reaching for deep learning.
  3. WHICH FEATURE MATTERS. Permutation importance measures how much the
     held-out score drops when we shuffle each feature — model-agnostic and
     honest.

The punchline: the 2022–24 inversion makes this model SCREAM recession — yet
none arrived. We watch it be "wrong" in real time. That is the economics.

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
import matplotlib.gridspec as gridspec
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.inspection import permutation_importance
from sklearn.metrics import roc_auc_score, accuracy_score, roc_curve

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


def make_models() -> dict:
    """An interpretable linear model vs a flexible non-linear one."""
    return {
        "logistic": make_pipeline(
            StandardScaler(),
            LogisticRegression(max_iter=1000, class_weight="balanced")),
        "random_forest": RandomForestClassifier(
            n_estimators=300, max_depth=4, min_samples_leaf=8,
            class_weight="balanced", random_state=42),
    }


def main():
    log.info("=== ml/recession_prediction.py — yield-curve recession model ===")
    df = load()
    known = df.dropna(subset=["y"]).copy()
    log.info(f"Loaded {len(df):,} months; "
             f"{int(known['y'].sum())} positive labels (recession within {HORIZON}m)")

    X_all, y_all = known[FEATURES], known["y"].astype(int)
    models = make_models()

    # ---- (1) Walk-forward cross-validation: honest out-of-time AUC ----
    tscv = TimeSeriesSplit(n_splits=5)
    log.info("  Walk-forward CV (TimeSeriesSplit, 5 folds) — ROC-AUC:")
    cv_auc = {}
    for name, model in models.items():
        scores = cross_val_score(model, X_all, y_all, cv=tscv, scoring="roc_auc")
        cv_auc[name] = scores.mean()
        log.info(f"    {name:<14} {scores.mean():.3f}  (folds: "
                 f"{', '.join(f'{s:.2f}' for s in scores)})")
    # >>> NOTICE: with only a handful of macro features the simple logistic
    # >>> regression is typically as good as the random forest — complexity
    # >>> buys little here. Reach for interpretability first.

    # ---- (2) Fixed split for ROC curve + permutation importance ----
    train, test = known[known["date"] <= TRAIN_END], known[known["date"] > TRAIN_END]
    Xtr, ytr = train[FEATURES], train["y"].astype(int)
    Xte, yte = test[FEATURES],  test["y"].astype(int)

    roc_data, perm_imp = {}, None
    for name, model in models.items():
        model.fit(Xtr, ytr)
        p = model.predict_proba(Xte)[:, 1]
        roc_data[name] = (roc_curve(yte, p), roc_auc_score(yte, p))
        log.info(f"  {name}: held-out AUC {roc_data[name][1]:.3f}, "
                 f"acc {accuracy_score(yte, (p >= 0.5).astype(int)):.3f}")

    # Permutation importance on the interpretable model (held-out set)
    logit = models["logistic"]
    pi = permutation_importance(logit, Xte, yte, n_repeats=30,
                                random_state=42, scoring="roc_auc")
    perm_imp = pd.Series(pi.importances_mean, index=FEATURES).sort_values()
    log.info("  Permutation importance (logistic, AUC drop when shuffled):")
    for name, v in perm_imp.iloc[::-1].items():
        log.info(f"    {name:<14} {v:+.3f}")
    coefs = logit.named_steps["logisticregression"].coef_[0]
    log.info("  Logistic coefficients (standardised): "
             + ", ".join(f"{n}={c:+.2f}" for n, c in zip(FEATURES, coefs)))
    # >>> NOTICE: spread_10_2 carries a strong NEGATIVE coefficient and high
    # >>> importance — a flatter/inverted 10y-2y curve RAISES recession risk.
    # >>> That is the yield-curve signal, learned straight from the data.

    # ---- (3) Predicted probability over the WHOLE sample for the chart ----
    df["p_recession"] = logit.predict_proba(df[FEATURES])[:, 1]
    plot(df, roc_data, perm_imp, cv_auc)

    recent = df[df["date"] >= "2022-07-01"]
    if not recent.empty:
        log.info(f"  Mean predicted P(recession) Jul-2022→now: "
                 f"{recent['p_recession'].mean():.2f}  "
                 f"(actual recession months in that window: "
                 f"{int(recent['recession'].sum())})")
    # >>> NOTICE: high predicted probability with ZERO realised recession is the
    # >>> central puzzle of 2022–24 — the model trusted the inverted curve, the
    # >>> economy did not oblige. WHY? (term-premium/QT distortions, a strong
    # >>> labour market, real-income recovery as inflation fell.)


def plot(df, roc_data, perm_imp, cv_auc):
    fig = plt.figure(figsize=(13, 9))
    gs = gridspec.GridSpec(2, 2, figure=fig, height_ratios=[2, 1.3],
                           hspace=0.35, wspace=0.25)
    fig.suptitle("Can the Yield Curve Predict Recessions? (logistic regression)\n"
                 f"Durham — Block 7 ML · walk-forward CV AUC: "
                 f"logistic {cv_auc['logistic']:.2f} vs forest "
                 f"{cv_auc['random_forest']:.2f}",
                 fontweight="bold", fontsize=12)

    # Top (full width): predicted probability + actual recession shading
    ax1 = fig.add_subplot(gs[0, :])
    ax1.fill_between(df["date"], 0, 1, where=df["recession"] == 1,
                     color=MUTED, alpha=0.25, label="NBER recession (actual)")
    ax1.plot(df["date"], df["p_recession"], color=RED, lw=1.4,
             label="Predicted P(recession within 12m)")
    ax1.axhline(0.5, color=MUTED, lw=0.6, ls=":")
    ax1.axvspan(pd.Timestamp("2022-07-01"), df["date"].max(),
                color=GOLD, alpha=0.10)
    ax1.set_ylabel("Probability"); ax1.set_ylim(0, 1)
    ax1.legend(fontsize=8, loc="upper left")
    ax1.set_title("Gold band = the 2022–24 inversion: model predicts, "
                  "economy resists", loc="left", fontsize=9)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax1.xaxis.set_major_locator(mdates.YearLocator(3))

    # Bottom-left: ROC curves (held-out)
    ax2 = fig.add_subplot(gs[1, 0])
    for (name, ((fpr, tpr, _), auc_)), col in zip(roc_data.items(), [NAVY, GOLD]):
        ax2.plot(fpr, tpr, color=col, lw=1.6, label=f"{name} (AUC {auc_:.2f})")
    ax2.plot([0, 1], [0, 1], color=MUTED, lw=0.8, ls="--")
    ax2.set_xlabel("False positive rate"); ax2.set_ylabel("True positive rate")
    ax2.set_title("ROC — held-out 2015+", loc="left", fontsize=9)
    ax2.legend(fontsize=7, loc="lower right")

    # Bottom-right: permutation importance
    ax3 = fig.add_subplot(gs[1, 1])
    ax3.barh(perm_imp.index, perm_imp.values, color=NAVY, alpha=0.85)
    ax3.set_xlabel("AUC drop when feature shuffled")
    ax3.set_title("Permutation importance (logistic)", loc="left", fontsize=9)
    ax3.axvline(0, color=MUTED, lw=0.6)

    out = OUTPUTS / "ml_recession_probability.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    log.info(f"  Saved: {out}")
    plt.show()
    plt.close()


if __name__ == "__main__":
    main()
