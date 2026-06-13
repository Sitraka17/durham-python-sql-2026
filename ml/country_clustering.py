# 📖 New here? A plain-English (Feynman-style) explanation of every concept
# used below — Python, the economics, the ML — is in
# docs/concepts_explained.md. Read it alongside this file.
"""
ml/country_clustering.py
========================
MACHINE LEARNING (Block 7) — runs 100% locally, on CPU.

CONCEPT — Unsupervised learning (k-means + PCA)
-----------------------------------------------
No target variable this time. We hand k-means the 2022 macro profile of ~40
countries (inflation, growth, unemployment, fiscal & external balances, income)
and ask it to group them into "regimes" with NO labels. Then we use PCA to
squeeze the standardised features into 2 dimensions so we can SEE the clusters.

The economics: does an unsupervised algorithm rediscover groupings an economist
would recognise — a high-inflation EM-crisis cluster (Argentina, Turkey), a
stable advanced-economy cluster, and so on? Clustering is how you find structure
when you don't yet have a hypothesis.

    python ml/country_clustering.py
    # -> outputs/ml_country_clusters.png
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
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score

from scripts.utils import get_engine, OUTPUTS, log

PALETTE = ["#002855", "#C49400", "#9B1C1C", "#0A6640", "#5A5F67"]
FEATURES = ["inflation", "gdp_growth", "unemployment",
            "fiscal_balance", "current_account", "log_gdp_pc"]
YEAR = 2022
K = 4


def load() -> pd.DataFrame:
    eng = get_engine()
    df = pd.read_sql_query(
        f"""
        SELECT i.country_code, c.country_name, c.income_group,
               i.inflation, i.gdp_growth, i.unemployment,
               i.fiscal_balance, i.current_account, i.gdp_per_capita
        FROM indicators i JOIN countries c ON c.country_code = i.country_code
        WHERE i.year = {YEAR}
        """, eng)
    df["log_gdp_pc"] = np.log(df["gdp_per_capita"])
    return df.dropna(subset=FEATURES).reset_index(drop=True)


def main():
    log.info("=== ml/country_clustering.py — k-means macro regimes ===")
    df = load()
    log.info(f"{len(df)} countries with complete {YEAR} data; "
             f"features: {FEATURES}")

    X = StandardScaler().fit_transform(df[FEATURES])          # always standardise

    # How many clusters? Scan k and score each with the silhouette
    # (how tight/separated the clusters are; higher is better, max 1.0).
    log.info("  Choosing k by silhouette score:")
    for k in range(2, 7):
        labels = KMeans(n_clusters=k, n_init=10, random_state=42).fit_predict(X)
        marker = "  <- chosen" if k == K else ""
        log.info(f"    k={k}: silhouette {silhouette_score(X, labels):.3f}{marker}")
    # >>> NOTICE: the silhouette scores here are close (~0.22–0.29) — a flat
    # >>> landscape with no single obvious k. k=4 sits at a local optimum AND
    # >>> gives the most readable economic regimes, so we keep it. When the
    # >>> statistics are ambiguous, let interpretability break the tie.

    km = KMeans(n_clusters=K, n_init=10, random_state=42).fit(X)
    df["cluster"] = km.labels_

    # Describe each cluster in ORIGINAL units so it is economically readable
    log.info(f"  Cluster centroids ({YEAR}, original units):")
    centroids = (df.groupby("cluster")[["inflation", "gdp_growth",
                 "unemployment", "fiscal_balance", "current_account"]]
                 .mean().round(1))
    print(centroids.to_string())
    for cl in sorted(df["cluster"].unique()):
        members = df.loc[df["cluster"] == cl, "country_code"].tolist()
        log.info(f"    cluster {cl} (n={len(members)}): {', '.join(members)}")
    # >>> NOTICE: one small cluster should isolate the high-inflation economies
    # >>> (e.g. Argentina, Turkey). k-means found them WITHOUT being told what
    # >>> inflation is — the structure is in the data.

    plot(df, X)


def plot(df: pd.DataFrame, X: np.ndarray):
    # PCA -> 2D just for visualisation (the clustering used all 6 features)
    coords = PCA(n_components=2, random_state=42).fit_transform(X)
    df = df.assign(pc1=coords[:, 0], pc2=coords[:, 1])

    fig, ax = plt.subplots(figsize=(12, 8))
    fig.suptitle("Unsupervised Macro Regimes, 2022 (k-means + PCA)\n"
                 "Durham — Block 7 ML · clusters learned from 6 standardised "
                 "indicators, no labels",
                 fontweight="bold", fontsize=12)
    for cl in sorted(df["cluster"].unique()):
        sub = df[df["cluster"] == cl]
        ax.scatter(sub["pc1"], sub["pc2"], s=90, alpha=0.8,
                   color=PALETTE[cl % len(PALETTE)], label=f"cluster {cl}")
    for _, r in df.iterrows():
        ax.annotate(r["country_code"], (r["pc1"], r["pc2"]),
                    fontsize=7, ha="center", va="center", color="white")
    ax.set_xlabel("PC1  (overall macro stress →)")
    ax.set_ylabel("PC2")
    ax.legend(fontsize=8, loc="best")
    ax.grid(alpha=0.25)

    out = OUTPUTS / "ml_country_clusters.png"
    plt.tight_layout()
    plt.savefig(out, dpi=150, bbox_inches="tight")
    log.info(f"  Saved: {out}")
    plt.show()
    plt.close()


if __name__ == "__main__":
    main()
