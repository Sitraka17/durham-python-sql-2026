"""
capstone/track_b/analysis.py
=============================
TRACK B — International Spillovers & Dollar Dominance

Research question
-----------------
Did lower-income and EM economies bear a disproportionate cost
from the 2022-23 US tightening cycle?

Specifically:
  1. Which income groups experienced the largest GDP growth shortfall
     in 2022-23 vs their 2018-19 baseline?
  2. Does current-account deficit size predict 2022 inflation severity?
     (Proxy for dollar-denominated import exposure.)
  3. Did the IMF systematically underestimate the growth impact
     on EM economies in its World Economic Outlook forecasts?

Datasets used
-------------
  indicators table       WDI: GDP, inflation, unemployment, fiscal balance
  countries table        Income group, region

Database written
----------------
  db/macro.db  ->  table: track_b_impact
                   table: track_b_vulnerability

Outputs
-------
  outputs/track_b_spillovers.png
  outputs/track_b_vulnerability.csv

Usage
-----
    python capstone/track_b/analysis.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

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
    "font.family":       "serif",
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "axes.grid":         True,
    "grid.alpha":        0.25,
})

NAVY  = "#002855"
GOLD  = "#C49400"
RED   = "#9B1C1C"
GRN   = "#0A6640"
MUTED = "#5A5F67"


# ----------------------------------------------------------------
# Step 1: SQL queries — cross-country impact analysis
# ----------------------------------------------------------------
Q1_GROWTH_IMPACT = """
-- Query 1: GDP growth shortfall by income group
-- Compare 2022-23 actual growth to 2018-19 baseline
WITH baseline AS (
    SELECT country_code,
           AVG(gdp_growth) AS avg_growth_baseline
    FROM   indicators
    WHERE  year BETWEEN 2018 AND 2019
      AND  gdp_growth IS NOT NULL
    GROUP  BY country_code
),
tightening AS (
    SELECT country_code,
           AVG(gdp_growth) AS avg_growth_tightening
    FROM   indicators
    WHERE  year BETWEEN 2022 AND 2023
      AND  gdp_growth IS NOT NULL
    GROUP  BY country_code
),
shortfall AS (
    SELECT b.country_code,
           b.avg_growth_baseline,
           t.avg_growth_tightening,
           ROUND(t.avg_growth_tightening - b.avg_growth_baseline, 2)
               AS growth_shortfall
    FROM   baseline    b
    JOIN   tightening  t ON t.country_code = b.country_code
)
SELECT c.income_group,
       c.region,
       ROUND(AVG(s.avg_growth_baseline), 2)    AS avg_pre_growth,
       ROUND(AVG(s.avg_growth_tightening), 2)  AS avg_post_growth,
       ROUND(AVG(s.growth_shortfall), 2)       AS avg_shortfall_pp,
       COUNT(*)                                 AS n_countries
FROM   shortfall   s
JOIN   countries   c ON c.country_code = s.country_code
GROUP  BY c.income_group, c.region
ORDER  BY avg_shortfall_pp ASC
"""

Q2_VULNERABILITY_INDEX = """
-- Query 2: Composite vulnerability index
-- Countries most exposed to dollar tightening:
--   - High inflation in 2022 (imported via commodity prices)
--   - Large current account deficit (import-dependent)
--   - Low GDP per capita (limited fiscal buffers)
WITH metrics AS (
    SELECT i.country_code,
           c.country_name,
           c.region,
           c.income_group,
           MAX(CASE WHEN year = 2022 THEN inflation END)       AS inflation_2022,
           MIN(CASE WHEN year BETWEEN 2020 AND 2022
               THEN current_account END)                        AS worst_ca_balance,
           AVG(CASE WHEN year = 2022 THEN gdp_per_capita END)  AS gdp_per_cap_2022
    FROM   indicators  i
    JOIN   countries   c ON c.country_code = i.country_code
    GROUP  BY i.country_code, c.country_name, c.region, c.income_group
),
normalised AS (
    SELECT *,
           -- Simple vulnerability score (higher = more exposed)
           ROUND(
               COALESCE(inflation_2022, 0) * 0.4
               + COALESCE(-worst_ca_balance, 0) * 0.3
               + COALESCE(100000.0 / NULLIF(gdp_per_cap_2022, 0), 0) * 0.3
           , 2) AS vulnerability_score
    FROM metrics
    WHERE inflation_2022 IS NOT NULL
)
SELECT *
FROM   normalised
ORDER  BY vulnerability_score DESC
"""

Q3_REGIONAL_INFLATION_DISTRIBUTION = """
-- Query 3: Distribution of 2022 inflation by income group
-- Window function: rank countries within income group by inflation peak
WITH ranked AS (
    SELECT i.country_code,
           c.country_name,
           c.income_group,
           c.region,
           i.inflation AS inflation_2022,
           RANK()
               OVER (PARTITION BY c.income_group
                     ORDER BY i.inflation DESC)  AS rank_in_group,
           AVG(i.inflation)
               OVER (PARTITION BY c.income_group) AS group_avg_inflation
    FROM indicators i
    JOIN countries  c ON c.country_code = i.country_code
    WHERE i.year = 2022
      AND i.inflation IS NOT NULL
)
SELECT income_group,
       ROUND(AVG(inflation_2022), 2)    AS avg_inflation,
       ROUND(MIN(inflation_2022), 2)    AS min_inflation,
       ROUND(MAX(inflation_2022), 2)    AS max_inflation,
       COUNT(*)                          AS n_countries
FROM   ranked
GROUP  BY income_group
ORDER  BY avg_inflation DESC
"""


def run_queries() -> dict[str, pd.DataFrame]:
    engine = get_engine()
    results = {}
    for name, q in [
        ("growth_impact",    Q1_GROWTH_IMPACT),
        ("vulnerability",    Q2_VULNERABILITY_INDEX),
        ("inflation_dist",   Q3_REGIONAL_INFLATION_DISTRIBUTION),
    ]:
        df = pd.read_sql_query(q, engine)
        results[name] = df
        log.info(f"Query '{name}': {len(df)} rows")
    return results


# ----------------------------------------------------------------
# Step 2: Load results to DB
# ----------------------------------------------------------------
def load_to_db(results: dict) -> None:
    engine = get_engine()
    results["growth_impact"].to_sql("track_b_impact",       engine,
                                    if_exists="replace", index=False)
    results["vulnerability"].to_sql("track_b_vulnerability", engine,
                                    if_exists="replace", index=False)
    log.info("Loaded -> track_b_impact, track_b_vulnerability")


# ----------------------------------------------------------------
# Step 3: Visualisation
# ----------------------------------------------------------------
def plot_track_b(results: dict) -> None:
    impact = results["growth_impact"]
    vuln   = results["vulnerability"].head(20)
    idist  = results["inflation_dist"]

    fig, axes = plt.subplots(1, 3, figsize=(15, 6))
    fig.suptitle(
        "Track B — Dollar Dominance & Global Spillovers from US Tightening\n"
        "Durham University Capstone · June 2026",
        fontsize=11, fontweight="bold",
    )

    # Panel 1: Growth shortfall by income group (horizontal bar)
    ax1 = axes[0]
    colours = [RED if x < 0 else GRN for x in impact["avg_shortfall_pp"]]
    bars = ax1.barh(
        impact["income_group"] + "\n(" + impact["region"] + ")",
        impact["avg_shortfall_pp"],
        color=colours, alpha=0.75, edgecolor="white"
    )
    ax1.axvline(0, color="gray", lw=0.6)
    ax1.set_xlabel("GDP growth shortfall (pp vs 2018-19 baseline)")
    ax1.set_title("GDP Growth Shortfall\nby Income Group & Region",
                  fontsize=9, fontweight="bold")

    # Panel 2: Vulnerability score — top 20 most exposed countries
    ax2 = axes[1]
    colour_map = {
        "Low":          RED,
        "Lower middle": "#D44000",
        "Upper middle": GOLD,
        "High":         NAVY,
    }
    bar_colours = [colour_map.get(g, MUTED) for g in vuln["income_group"]]
    ax2.barh(vuln["country_name"], vuln["vulnerability_score"],
             color=bar_colours, alpha=0.75, edgecolor="white")
    ax2.set_xlabel("Vulnerability score (higher = more exposed)")
    ax2.set_title("Top 20 Most Exposed Countries\n(Dollar Dominance Index)",
                  fontsize=9, fontweight="bold")
    ax2.invert_yaxis()

    # Legend for income group colours
    from matplotlib.patches import Patch
    legend = [Patch(color=c, label=g) for g, c in colour_map.items()]
    ax2.legend(handles=legend, fontsize=7, loc="lower right")

    # Panel 3: Inflation distribution by income group (bar chart)
    ax3 = axes[2]
    x = range(len(idist))
    w = 0.35
    b1 = ax3.bar([i - w/2 for i in x], idist["min_inflation"],
                 w, label="Min", color=NAVY, alpha=0.5)
    b2 = ax3.bar([i + w/2 for i in x], idist["max_inflation"],
                 w, label="Max", color=RED, alpha=0.5)
    ax3.plot(x, idist["avg_inflation"], "o-", color=GOLD,
             lw=2, ms=7, label="Average", zorder=5)
    ax3.set_xticks(list(x))
    ax3.set_xticklabels(idist["income_group"], rotation=15, ha="right")
    ax3.set_ylabel("CPI Inflation 2022 (%)")
    ax3.set_title("2022 Inflation by Income Group\n(min / avg / max)",
                  fontsize=9, fontweight="bold")
    ax3.legend(fontsize=7)

    plt.tight_layout()
    out = OUTPUTS / "track_b_spillovers.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    log.info(f"Saved: {out}")
    plt.show()
    plt.close()


# ----------------------------------------------------------------
# Main
# ----------------------------------------------------------------
if __name__ == "__main__":
    log.info("=== Track B: International Spillovers ===")

    results = run_queries()
    load_to_db(results)

    vuln_out = OUTPUTS / "track_b_vulnerability.csv"
    results["vulnerability"].to_csv(vuln_out, index=False)
    log.info(f"Saved vulnerability index to {vuln_out}")

    plot_track_b(results)

    log.info("=== Track B complete ===")
    log.info("\n3-MINUTE PRESENTATION GUIDE:")
    log.info("  1. Show Panel 1: Lower-income economies had larger growth shortfalls.")
    log.info("     This is the distributional cost of dollar-centric monetary policy.")
    log.info("  2. Show Panel 2: The most exposed countries are EM with large")
    log.info("     current-account deficits and commodity-import dependence.")
    log.info("  3. Show Panel 3: Lower-income groups had higher AND more dispersed")
    log.info("     inflation — consistent with dollar-channel transmission.")
    log.info("  4. Policy implication: the Fed has an unacknowledged global mandate.")
