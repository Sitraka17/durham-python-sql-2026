"""
datasets/download.py
====================
Downloads every dataset needed for the Durham course.

Sources
-------
  World Bank WDI   GDP per capita, inflation, unemployment (via wbdata)
  FRED             Monetary, credit, mortgage, M2 series (via fredapi)
  OECD             Quarterly unemployment panel (public bulk CSV)

All downloads have a fallback: if an API is unavailable, the bundled
static CSV (datasets/*_static.csv) is used instead.

Usage
-----
    python datasets/download.py           # all sources, live API
    python datasets/download.py --no-api  # use static fallbacks only
"""
import sys
import logging
import argparse
from pathlib import Path
from functools import reduce

logging.basicConfig(level=logging.INFO,
                    format="%(levelname)-8s %(message)s")
log = logging.getLogger("download")

HERE = Path(__file__).parent


# ----------------------------------------------------------------
# Command-line arguments
# ----------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Download all course datasets")
    p.add_argument("--no-api", action="store_true",
                   help="Skip live API calls; use bundled static CSVs only")
    return p.parse_args()


# ----------------------------------------------------------------
# 1. World Bank WDI
# ----------------------------------------------------------------
COUNTRIES = [
    "USA","GBR","DEU","FRA","JPN","CHN","IND","BRA","CAN","AUS",
    "KOR","ITA","ESP","NLD","CHE","SWE","NOR","DNK","FIN","BEL",
    "MEX","ARG","ZAF","NGA","EGY","TUR","IDN","SAU","POL","CZE",
    "LUX","IRL","PRT","GRC","HUN","COL","CHL","PER","VNM","THA",
]

WDI_INDICATORS = {
    "NY.GDP.PCAP.CD":  "gdp_per_capita",   # GDP per capita (current USD)
    "FP.CPI.TOTL.ZG":  "inflation",        # CPI inflation (annual %)
    "SL.UEM.TOTL.ZS":  "unemployment",     # Unemployment (% labour force)
    "NY.GDP.MKTP.KD.ZG":"gdp_growth",      # GDP growth (annual %)
    "GC.NLD.TOTL.GD.ZS":"fiscal_balance",  # Net lending/borrowing (% GDP)
    "BN.CAB.XOKA.GD.ZS":"current_account", # Current account (% GDP)
}


def download_wdi(no_api: bool) -> None:
    out = HERE / "wdi_indicators.csv"
    if no_api and out.exists():
        log.info(f"WDI: using existing {out.name}")
        return

    log.info("WDI: downloading from World Bank API...")
    try:
        import wbdata
        import pandas as pd
        import datetime

        date_range = (
            datetime.datetime(1990, 1, 1),
            datetime.datetime(2024, 1, 1),
        )
        df = wbdata.get_dataframe(
            WDI_INDICATORS,
            country=COUNTRIES,
            date=date_range,
        )
        df = (df.reset_index()
               .rename(columns={"date": "year", "country": "country_code"}))
        df["year"] = df["year"].astype(int)
        df.to_csv(out, index=False)
        log.info(f"WDI: saved {len(df):,} rows to {out.name}")
    except Exception as e:
        log.warning(f"WDI download failed: {e} — check datasets/wdi_indicators.csv")


# ----------------------------------------------------------------
# 2. FRED
# ----------------------------------------------------------------
FRED_SERIES = {
    "fed_funds":    "FEDFUNDS",
    "rate_2y":      "GS2",
    "rate_10y":     "GS10",
    "rate_30y":     "GS30",
    "cpi_index":    "CPIAUCSL",
    "core_pce":     "PCEPILFE",
    "m2":           "M2SL",
    "m2_velocity":  "M2V",
    "unemployment": "UNRATE",
    "payrolls":     "PAYEMS",
    "lfpr":         "CIVPART",
    "ig_spread":    "BAMLC0A0CM",
    "hy_spread":    "BAMLH0A0HYM2",
    "mortgage_30y": "MORTGAGE30US",
    "fed_assets":   "WALCL",
}


def download_fred(no_api: bool) -> None:
    import os
    out = HERE / "fred_rates.csv"
    static = HERE / "fred_rates_static.csv"

    if no_api:
        if static.exists():
            log.info(f"FRED: using static fallback {static.name}")
            import shutil
            shutil.copy(static, out)
        else:
            log.warning("FRED: --no-api set but fred_rates_static.csv not found")
        return

    key = os.getenv("FRED_KEY", "")
    if not key or key == "your_fred_api_key_here":
        log.warning("FRED: FRED_KEY not set in .env — using static fallback")
        if static.exists():
            import shutil
            shutil.copy(static, out)
        return

    log.info("FRED: downloading from API...")
    try:
        import pandas as pd
        from fredapi import Fred

        fred   = Fred(api_key=key)
        frames = []
        for col, sid in FRED_SERIES.items():
            s = (fred.get_series(sid, observation_start="1990-01-01")
                     .rename(col).reset_index()
                     .rename(columns={"index": "date"}))
            frames.append(s)
            log.info(f"  {sid}: {len(s):,} rows")

        df = reduce(
            lambda a, b: a.merge(b, on="date", how="outer"),
            frames
        ).sort_values("date")

        # ICE BofA OAS series are reported by FRED in percent; the rest of
        # this repo treats credit spreads in basis points -> convert.
        df["ig_spread"]     = (df["ig_spread"] * 100).round(0)
        df["hy_spread"]     = (df["hy_spread"] * 100).round(0)

        # Derived columns
        df["cpi_yoy"]       = df["cpi_index"].pct_change(12, fill_method=None).mul(100).round(3)
        df["real_rate"]     = (df["fed_funds"] - df["cpi_yoy"]).round(3)
        df["spread_10_2"]   = (df["rate_10y"]  - df["rate_2y"]).round(3)
        df["spread_30_2"]   = (df["rate_30y"]  - df["rate_2y"]).round(3)
        df["inverted"]      = (df["spread_10_2"] < 0).astype(int)
        df["mortgage_spread"] = (df["mortgage_30y"] - df["rate_10y"]).round(3)
        df["m2_yoy"]        = df["m2"].pct_change(12, fill_method=None).mul(100).round(2)

        # Taylor Rule
        RSTAR, PI_STAR, NAIRU = 0.5, 2.0, 4.0
        df["output_gap_proxy"] = -2.0 * (df["unemployment"] - NAIRU)
        df["taylor_rule"] = (
            df["cpi_yoy"] + RSTAR
            + 0.5 * (df["cpi_yoy"] - PI_STAR)
            + 0.5 * df["output_gap_proxy"]
        ).round(3)
        df["taylor_gap"] = (df["taylor_rule"] - df["fed_funds"]).round(3)

        df.to_csv(out, index=False)
        log.info(f"FRED: saved {len(df):,} rows to {out.name}")

    except Exception as e:
        log.warning(f"FRED download failed: {e}")
        if static.exists():
            import shutil
            shutil.copy(static, out)
            log.info("FRED: fell back to static CSV")


# ----------------------------------------------------------------
# 3. OECD quarterly unemployment
# ----------------------------------------------------------------
OECD_URL = (
    "https://sdmx.oecd.org/public/rest/data/"
    "OECD.SDD.TPS,DF_LFS_INDIC,1.0/"
    "all?startPeriod=2000-Q1&dimensionAtObservation=AllDimensions"
    "&contentType=csvfilewithlabels"
)


def download_oecd(no_api: bool) -> None:
    out    = HERE / "oecd_unemployment.csv"
    static = HERE / "oecd_unemployment_static.csv"

    if no_api:
        if static.exists():
            log.info(f"OECD: using static fallback {static.name}")
            import shutil
            shutil.copy(static, out)
        return

    log.info("OECD: downloading quarterly unemployment...")
    try:
        import pandas as pd
        # Simpler OECD endpoint — main labour statistics bulk CSV
        url = (
            "https://stats.oecd.org/sdmx-json/data/"
            "DP_LIVE/.HUR.TOT.PC_LF.Q/"
            "OECD?contentType=csv&detail=code"
            "&separator=comma&csv-lang=en"
        )
        df = pd.read_csv(url)
        # Rename to standard columns
        rename_map = {}
        for c in df.columns:
            cl = c.lower()
            if "location" in cl or "country" in cl:
                rename_map[c] = "country_code"
            elif "time" in cl or "period" in cl:
                rename_map[c] = "quarter"
            elif "value" in cl or "obs" in cl:
                rename_map[c] = "unemployment_rate"
        df = df.rename(columns=rename_map)
        keep = ["country_code", "quarter", "unemployment_rate"]
        df   = df[[c for c in keep if c in df.columns]].dropna()
        df.to_csv(out, index=False)
        log.info(f"OECD: saved {len(df):,} rows to {out.name}")
    except Exception as e:
        log.warning(f"OECD download failed: {e}")
        if static.exists():
            import shutil
            shutil.copy(static, out)
            log.info("OECD: fell back to static CSV")


# ----------------------------------------------------------------
# Main
# ----------------------------------------------------------------
if __name__ == "__main__":
    args = parse_args()
    no   = args.no_api
    log.info("=== datasets/download.py ===")
    download_wdi(no)
    download_fred(no)
    download_oecd(no)
    log.info("=== Done. Run: python scripts/setup_db.py ===")
