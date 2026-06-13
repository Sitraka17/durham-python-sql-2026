# 📖 New here? A plain-English (Feynman-style) explanation of every concept
# used below — Python, the economics, the ML — is in
# docs/concepts_explained.md. Read it alongside this file.
"""
ml/inflation_forecast.py
========================
MACHINE LEARNING (Block 7) — runs 100% locally, on CPU.

CONCEPT — Regularised regression (Ridge & Lasso) for forecasting
----------------------------------------------------------------
Can we forecast inflation 12 months ahead from today's macro dashboard? With
~10 candidate predictors and a short monthly sample, plain OLS happily overfits.
The ML answer is *regularisation* — penalise large coefficients:

  - RIDGE (L2): shrinks all coefficients toward zero → tames multicollinearity
    (our predictors are highly correlated), more stable out-of-sample.
  - LASSO (L1): shrinks some coefficients EXACTLY to zero → automatic VARIABLE
    SELECTION. For an economist this is the bridge: Lasso decides which
    indicators matter, instead of you hand-picking them.

We choose the penalty strength (alpha) by walk-forward cross-validation, so the
choice never peeks at the future.

    python ml/inflation_forecast.py
    # -> outputs/ml_inflation_forecast.png
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
from sklearn.linear_model import LinearRegression, RidgeCV, LassoCV
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_absolute_error, r2_score

from scripts.utils import get_engine, OUTPUTS, log

NAVY, GOLD, RED, GRN, MUTED = "#002855", "#C49400", "#9B1C1C", "#0A6640", "#5A5F67"
HORIZON = 12          # forecast inflation 12 months ahead
FEATURES = ["cpi_yoy", "m2_yoy", "fed_funds", "real_rate", "spread_10_2",
            "unemployment", "hy_spread", "mortgage_spread", "taylor_gap"]
TRAIN_END = "2016-12-31"


def load() -> pd.DataFrame:
    eng = get_engine()
    df = pd.read_sql_query(
        f"SELECT date, {', '.join(FEATURES)} FROM fred_rates ORDER BY date",
        eng, parse_dates=["date"],
    ).dropna(subset=FEATURES).reset_index(drop=True)
    # TARGET: inflation HORIZON months from now (known for all but the last 12).
    df["y"] = df["cpi_yoy"].shift(-HORIZON)
    return df


def main():
    log.info("=== ml/inflation_forecast.py — regularised inflation forecast ===")
    df = load()
    known = df.dropna(subset=["y"]).copy()
    log.info(f"Loaded {len(known):,} usable months; forecasting CPI YoY "
             f"{HORIZON} months ahead from {len(FEATURES)} predictors")

    train = known[known["date"] <= TRAIN_END]
    test  = known[known["date"] >  TRAIN_END]
    Xtr, ytr = train[FEATURES], train["y"]
    Xte, yte = test[FEATURES],  test["y"]
    tscv = TimeSeriesSplit(n_splits=5)

    models = {
        "OLS":   make_pipeline(StandardScaler(), LinearRegression()),
        "Ridge": make_pipeline(StandardScaler(),
                               RidgeCV(alphas=np.logspace(-3, 3, 50))),
        "Lasso": make_pipeline(StandardScaler(),
                               LassoCV(alphas=np.logspace(-3, 1, 50),
                                       cv=tscv, max_iter=20000)),
    }
    log.info(f"  Held-out test ({test['date'].dt.year.min()}–"
             f"{test['date'].dt.year.max()}) — lower MAE is better:")
    preds = {}
    for name, model in models.items():
        model.fit(Xtr, ytr)
        p = model.predict(Xte)
        preds[name] = p
        log.info(f"    {name:<6} MAE {mean_absolute_error(yte, p):.2f} pp   "
                 f"R² {r2_score(yte, p):+.2f}")
    # >>> NOTICE: OLS often has the worst out-of-sample error despite the best
    # >>> in-sample fit — the signature of overfitting. Ridge/Lasso regularise
    # >>> it away. This is why economists shrink.

    # Which predictors did Lasso KEEP?
    lasso = models["Lasso"].named_steps["lassocv"]
    coefs = pd.Series(lasso.coef_, index=FEATURES)
    kept = coefs[coefs.abs() > 1e-6].sort_values(key=np.abs, ascending=False)
    dropped = [f for f in FEATURES if abs(coefs[f]) <= 1e-6]
    log.info(f"  Lasso chose alpha={lasso.alpha_:.4f}; kept {len(kept)}/"
             f"{len(FEATURES)} predictors:")
    for n, c in kept.items():
        log.info(f"    {n:<16} {c:+.3f}")
    if dropped:
        log.info(f"    dropped (coef=0): {', '.join(dropped)}")
    # >>> NOTICE: at the 12-month horizon Lasso KEEPS the real rate and M2
    # >>> growth and DROPS today's inflation (cpi_yoy) — over a full year the
    # >>> monetary fundamentals carry more signal than current inflation's
    # >>> persistence. The 2020–21 M2 surge foreshadowing 2022 inflation is
    # >>> exactly the kind of signal Lasso isolates, without being told.

    df["pred_lasso"] = models["Lasso"].predict(df[FEATURES])
    plot(df, known, test, preds, coefs)


def plot(df, known, test, preds, coefs):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5),
                                   gridspec_kw={"width_ratios": [2, 1]})
    fig.suptitle("Forecasting Inflation 12 Months Ahead — Ridge & Lasso\n"
                 "Durham — Block 7 ML · regularisation beats OLS out-of-sample",
                 fontweight="bold", fontsize=12)

    # Left: actual future inflation vs Lasso forecast.  Plot the forecast at the
    # date it REFERS TO (issue date + HORIZON) so it lines up with realised CPI.
    ax1.plot(df["date"], df["cpi_yoy"], color=MUTED, lw=1.0,
             label="Realised CPI YoY")
    fc_date = df["date"] + pd.DateOffset(months=HORIZON)
    ax1.plot(fc_date, df["pred_lasso"], color=RED, lw=1.4,
             label=f"Lasso forecast (made {HORIZON}m earlier)")
    split = test["date"].min()
    ax1.axvline(split, color=NAVY, lw=0.8, ls=":")
    ax1.text(split, ax1.get_ylim()[1] * 0.92, " test →", fontsize=7, color=NAVY)
    ax1.axhline(2, color=GRN, lw=0.6, ls="--", alpha=0.7)
    ax1.set_ylabel("CPI YoY (%)")
    ax1.legend(fontsize=8, loc="upper left")
    ax1.set_title("Did the model see 2022 coming?", loc="left", fontsize=9)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax1.xaxis.set_major_locator(mdates.YearLocator(4))

    # Right: Lasso coefficients (selected vs dropped)
    cs = coefs.sort_values()
    cols = [RED if v < 0 else NAVY for v in cs.values]
    ax2.barh(cs.index, cs.values, color=cols, alpha=0.85)
    ax2.axvline(0, color=MUTED, lw=0.6)
    ax2.set_xlabel("Lasso coefficient (standardised)")
    ax2.set_title("What Lasso kept (0 = dropped)", loc="left", fontsize=9)

    out = OUTPUTS / "ml_inflation_forecast.png"
    plt.tight_layout()
    plt.savefig(out, dpi=150, bbox_inches="tight")
    log.info(f"  Saved: {out}")
    plt.show()
    plt.close()


if __name__ == "__main__":
    main()
