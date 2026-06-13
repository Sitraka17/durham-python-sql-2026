"""
scripts/setup_db.py
===================
Builds db/macro.db from CSV files in datasets/.

Creates tables
--------------
  countries          : 40-country reference dimension table
  indicators         : World Bank WDI macroeconomic panel
  fred_rates         : FRED monthly financial & monetary series
  oecd_unemployment  : OECD quarterly unemployment panel

Creates views
-------------
  v_gdp_ranked       : indicators enriched with country metadata + rank
  v_yield_curve      : yield spread with moving average and inversion flag
  v_real_rates       : Fisher real rate + Taylor Rule gap timeline
  v_credit_dashboard : policy rate, spreads, mortgage rate, M2

Safe to re-run: all tables use IF NOT EXISTS / REPLACE strategy.

Usage
-----
    python scripts/setup_db.py
"""
import pandas as pd
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

from scripts.utils import get_engine, DATASETS, log

# ----------------------------------------------------------------
# Table loading
# ----------------------------------------------------------------
def load_csv(filename: str, table: str, parse_dates: list[str] | None = None):
    path = DATASETS / filename
    if not path.exists():
        log.warning(f"  {filename} not found — skipping {table}")
        return
    kw = {"parse_dates": parse_dates} if parse_dates else {}
    df  = pd.read_csv(path, **kw)
    engine = get_engine()
    df.to_sql(table, engine, if_exists="replace", index=False)
    log.info(f"  {table:<28} {len(df):>9,} rows  ({filename})")


# ----------------------------------------------------------------
# SQL views — analytical layers on top of raw tables
# ----------------------------------------------------------------
VIEWS: dict[str, str] = {

    "v_gdp_ranked": """
        CREATE VIEW v_gdp_ranked AS
        SELECT
            i.country_code,
            c.country_name,
            c.region,
            c.income_group,
            i.year,
            i.gdp_per_capita,
            i.inflation,
            i.unemployment,
            RANK()
                OVER (PARTITION BY i.year
                      ORDER BY i.gdp_per_capita DESC)   AS rank_in_year,
            RANK()
                OVER (PARTITION BY i.year
                      ORDER BY i.inflation DESC)         AS inflation_rank_in_year
        FROM indicators i
        JOIN countries  c ON c.country_code = i.country_code
    """,

    "v_yield_curve": """
        CREATE VIEW v_yield_curve AS
        SELECT
            date,
            fed_funds,
            rate_2y,
            rate_10y,
            rate_30y,
            ROUND(rate_10y - rate_2y, 3)                    AS spread_10_2,
            ROUND(rate_30y - rate_2y, 3)                    AS spread_30_2,
            CASE WHEN rate_10y < rate_2y THEN 1 ELSE 0 END  AS inverted,
            ROUND(
                AVG(rate_10y - rate_2y)
                OVER (ORDER BY date
                      ROWS BETWEEN 11 PRECEDING
                               AND CURRENT ROW)
            , 3)                                             AS ma12_spread,
            ROUND(
                (rate_10y - rate_2y)
                - LAG(rate_10y - rate_2y, 12)
                  OVER (ORDER BY date)
            , 3)                                             AS spread_yoy_change
        FROM fred_rates
        WHERE rate_10y IS NOT NULL
          AND rate_2y  IS NOT NULL
    """,

    "v_real_rates": """
        CREATE VIEW v_real_rates AS
        SELECT
            date,
            fed_funds,
            cpi_yoy,
            core_pce,
            ROUND(fed_funds - cpi_yoy, 3)              AS real_rate_cpi,
            ROUND(
                fed_funds
                - (core_pce - LAG(core_pce, 12)
                   OVER (ORDER BY date))
                  / LAG(core_pce, 12)
                    OVER (ORDER BY date) * 100
            , 3)                                        AS real_rate_pce,
            taylor_rule,
            taylor_gap,
            ROUND(
                AVG(taylor_gap)
                OVER (ORDER BY date
                      ROWS BETWEEN 5 PRECEDING
                               AND CURRENT ROW)
            , 3)                                        AS ma6_taylor_gap
        FROM fred_rates
        WHERE cpi_yoy IS NOT NULL
    """,

    "v_credit_dashboard": """
        CREATE VIEW v_credit_dashboard AS
        SELECT
            date,
            fed_funds,
            rate_10y,
            mortgage_30y,
            mortgage_spread,
            ig_spread,
            hy_spread,
            m2,
            m2_yoy,
            real_rate,
            spread_10_2,
            inverted,
            ROUND(
                AVG(hy_spread)
                OVER (ORDER BY date
                      ROWS BETWEEN 11 PRECEDING
                               AND CURRENT ROW)
            , 0)                                   AS ma12_hy_spread,
            ROUND(
                hy_spread
                - LAG(hy_spread, 12)
                  OVER (ORDER BY date)
            , 0)                                   AS hy_spread_yoy
        FROM fred_rates
        WHERE fed_funds IS NOT NULL
    """,
}


# ----------------------------------------------------------------
# Country metadata (embedded — no download needed)
# ----------------------------------------------------------------
COUNTRIES = {
    "country_code": [
        "USA","GBR","DEU","FRA","JPN","CHN","IND","BRA","CAN","AUS",
        "KOR","ITA","ESP","NLD","CHE","SWE","NOR","DNK","FIN","BEL",
        "MEX","ARG","ZAF","NGA","EGY","TUR","IDN","SAU","POL","CZE",
        "LUX","IRL","PRT","GRC","HUN","COL","CHL","PER","VNM","THA",
    ],
    "country_name": [
        "United States","United Kingdom","Germany","France","Japan",
        "China","India","Brazil","Canada","Australia",
        "South Korea","Italy","Spain","Netherlands","Switzerland",
        "Sweden","Norway","Denmark","Finland","Belgium",
        "Mexico","Argentina","South Africa","Nigeria","Egypt",
        "Turkey","Indonesia","Saudi Arabia","Poland","Czech Republic",
        "Luxembourg","Ireland","Portugal","Greece","Hungary",
        "Colombia","Chile","Peru","Vietnam","Thailand",
    ],
    "region": [
        "North America","Europe","Europe","Europe","Asia Pacific",
        "Asia Pacific","Asia Pacific","Latin America","North America","Asia Pacific",
        "Asia Pacific","Europe","Europe","Europe","Europe",
        "Europe","Europe","Europe","Europe","Europe",
        "Latin America","Latin America","Africa","Africa","Middle East & Africa",
        "Middle East & Africa","Asia Pacific","Middle East & Africa","Europe","Europe",
        "Europe","Europe","Europe","Europe","Europe",
        "Latin America","Latin America","Latin America","Asia Pacific","Asia Pacific",
    ],
    "income_group": [
        "High","High","High","High","High",
        "Upper middle","Lower middle","Upper middle","High","High",
        "High","High","High","High","High",
        "High","High","High","High","High",
        "Upper middle","Upper middle","Upper middle","Lower middle","Lower middle",
        "Upper middle","Upper middle","High","High","High",
        "High","High","High","High","High",
        "Upper middle","High","Upper middle","Lower middle","Upper middle",
    ],
    "g20": [
        1,1,1,1,1, 1,1,1,1,1,
        1,1,1,0,0, 0,0,0,0,0,
        1,1,1,0,0, 1,1,1,0,0,
        0,0,0,0,0, 0,0,0,0,0,
    ],
    "eu_member": [
        0,0,1,1,0, 0,0,0,0,0,
        0,1,1,1,0, 1,0,1,1,1,
        0,0,0,0,0, 0,0,0,1,1,
        0,1,1,1,1, 0,0,0,0,0,
    ],
}


def create_countries():
    df = pd.DataFrame(COUNTRIES)
    engine = get_engine()
    df.to_sql("countries", engine, if_exists="replace", index=False)
    log.info(f"  {'countries':<28} {len(df):>9,} rows  (embedded)")


# ----------------------------------------------------------------
# Main
# ----------------------------------------------------------------
def main():
    log.info("=== Building macro.db ===")

    create_countries()
    load_csv("wdi_indicators.csv",    "indicators")
    load_csv("fred_rates.csv",        "fred_rates",       ["date"])
    load_csv("oecd_unemployment.csv", "oecd_unemployment")

    # Create views
    engine = get_engine()
    with engine.connect() as conn:
        for name, ddl in VIEWS.items():
            conn.execute(text(f"DROP VIEW IF EXISTS {name}"))
            conn.execute(text(ddl.strip()))
            conn.commit()
            log.info(f"  View created: {name}")

    log.info("=== Done. Verify with: python scripts/utils.py ===")


if __name__ == "__main__":
    main()
