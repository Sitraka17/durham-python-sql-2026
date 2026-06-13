# Block 7 — Machine Learning, locally

Applying machine learning to the same macro data, **entirely on your machine**:
scikit-learn, CPU only, **no GPU, no cloud, no internet**. Every script trains
in under a second on the bundled `macro.db`.

```bash
python ml/recession_prediction.py     # -> outputs/ml_recession_probability.png
python ml/inflation_forecast.py        # -> outputs/ml_inflation_forecast.png
python ml/taylor_rule_regression.py    # -> outputs/ml_reaction_function.png
python ml/country_clustering.py        # -> outputs/ml_country_clusters.png
```

Prerequisite: `python datasets/download.py --no-api && python scripts/setup_db.py`.

## ML is econometrics you already know — with new vocabulary

| You learned (econometrics) | ML calls it | Used in |
|----------------------------|-------------|---------|
| Logit / probit | Logistic regression (classification) | `recession_prediction.py` |
| OLS | Linear regression | `taylor_rule_regression.py`, `inflation_forecast.py` |
| Ridge / penalised regression | L2 regularisation | `inflation_forecast.py` |
| Variable selection | Lasso (L1 regularisation) | `inflation_forecast.py` |
| Out-of-sample testing | Train/test split, cross-validation | all |
| (no direct analogue) | Random forest, k-means clustering | recession, clustering |

The mindset shift: econometrics asks *"is this coefficient significant and
unbiased?"*; ML asks *"does this predict well on data it has never seen?"*.
Both matter — these scripts deliberately keep the **interpretable** models in
front so you never trade understanding for a black box.

## The four scripts

| Script | Technique | Headline result (from the bundled data) |
|--------|-----------|------------------------------------------|
| `recession_prediction.py` | Logistic regression vs random forest; walk-forward CV; permutation importance | Yield curve → recession. Walk-forward AUC **~0.80 (logistic) beats ~0.70 (forest)**. 2022→now predicted P(recession) ≈ **0.54** while **actual = 0** — the puzzle. |
| `inflation_forecast.py` | OLS vs Ridge vs Lasso (regularisation + selection) | Forecasting CPI 12m ahead is hard: **OLS R² ≈ −1.4 (overfit)**, Lasso the least bad. Lasso keeps `real_rate`, `m2_yoy` and **drops current inflation** — the monetary fundamentals win over a year. |
| `taylor_rule_regression.py` | Linear regression (learned policy rule) | `fed_funds ≈ 1.8 + 0.83·π + 0.28·gap`; inflation response **< 1** (Taylor principle violated); most "behind the curve" = **Mar 2022 (0.2% actual vs 9.1% implied)**. |
| `country_clustering.py` | k-means + PCA, silhouette k-selection | Unsupervised regimes: advanced economies / EM-periphery / **Norway** (oil surplus) / **Argentina + Turkey** (72% inflation). |

## Five pitfalls these scripts are built to teach

1. **Never shuffle a time series.** Use `TimeSeriesSplit` (walk-forward): train
   on the past, test on the future. A random shuffle leaks tomorrow into
   today and inflates every score.
2. **No leakage.** Features are dated at time *t*; targets look *forward*
   (recession in *t+1…t+12*, inflation at *t+12*). Never build a feature from
   information you would not have had in real time.
3. **Simple first.** With a few macro features the logistic regression matches
   or beats the random forest. Complexity is not free — start interpretable.
4. **Overfitting is real.** OLS has the best in-sample fit and the *worst*
   out-of-sample error in `inflation_forecast.py`. Regularisation (Ridge/Lasso)
   is the cure.
5. **Class imbalance & honest metrics.** Recessions are rare (~15% of months),
   so we report **ROC-AUC**, not accuracy (a "never recession" model is ~85%
   accurate and useless), and use `class_weight="balanced"`.

## Where ML stops and economics begins

The recession model is *confident* about 2022–24 and *wrong*. ML tells you the
historical pattern (inverted curve ⇒ recession); it cannot tell you why this
time was different (QT/term-premium distortions, a uniquely strong labour
market, real incomes recovering as inflation fell). That gap — between a
prediction and an explanation — is the whole point of the course.
