"""
scripts/fetch_fred.py
=====================
Fetches all FRED series needed for the Durham course.

Series fetched
--------------
Monetary policy
  FEDFUNDS        Federal Funds Rate (monthly)
  GS2             2-year Treasury yield
  GS10            10-year Treasury yield
  GS30            30-year Treasury yield

Inflation & money
  CPIAUCSL        CPI All Urban Consumers (index level)
  PCEPILFE        Core PCE price index (Fed's preferred measure)
  M2SL            M2 money supply (billions USD)
  M2V             M2 velocity (quarterly; forward-filled to monthly)

Labour market
  UNRATE          US civilian unemployment rate
  PAYEMS          Non-farm payrolls (thousands)
  LNS11300000     Labour force participation rate

Credit & mortgage markets
  BAMLC0A0CM      ICE BofA US Investment-Grade corporate spread (bp)
  BAMLH0A0HYM2    ICE BofA US High-Yield corporate spread (bp)
  MORTGAGE30US    30-year fixed mortgage rate

Fed balance sheet
  WALCL           Fed total assets (millions USD)

Derived series (computed here, not from FRED)
  cpi_yoy         12-month CPI inflation rate (%)
  real_rate       Ex-post real FFR = FEDFUNDS - cpi_yoy
  spread_10_2     10y - 2y Treasury spread (pp)
  inverted        1 if spread_10_2 < 0 else 0
  mortgage_spread MORTGAGE30US - GS10

Falls back to datasets/fred_rates_static.csv if the API is unavailable.

Run standalone:
    python scripts/fetch_fred.py
    # saves to datasets/fred_rates.csv and loads into macro.db
"""
import os
from functools import reduce
from pathlib import Path

import pandas as pd

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
# FRED series to download
# ----------------------------------------------------------------
SERIES: dict[str, str] = {
    # Monetary policy
    "fed_funds":        "FEDFUNDS",
    "rate_2y":          "GS2",
    "rate_10y":         "GS10",
    "rate_30y":         "GS30",
    # Inflation & money
    "cpi_index":        "CPIAUCSL",
    "core_pce":         "PCEPILFE",
    "m2":               "M2SL",
    "m2_velocity":      "M2V",          # quarterly
    # Labour market
    "unemployment":     "UNRATE",
    "payrolls":         "PAYEMS",
    "lfpr":             "CIVPART",
    # Credit & mortgage
    "ig_spread":        "BAMLC0A0CM",
    "hy_spread":        "BAMLH0A0HYM2",
    "mortgage_30y":     "MORTGAGE30US",
    # Fed balance sheet
    "fed_assets":       "WALCL",
}

START = "1990-01-01"
FALLBACK_CSV = DATASETS / "fred_rates_static.csv"


# ----------------------------------------------------------------
# Public API
# ----------------------------------------------------------------
def fetch(start: str = START, fallback: bool = True) -> pd.DataFrame:
    """
    Fetch all FRED series, merge on date, compute derived columns.

    Parameters
    ----------
    start   : earliest observation date (YYYY-MM-DD)
    fallback: if True, use FALLBACK_CSV when the API is unavailable

    Returns
    -------
    Wide-format DataFrame, one row per month.
    """
    from scripts.utils import fred_key
    try:
        key = fred_key()
        return _fetch_live(key, start)
    except EnvironmentError as e:
        log.warning(str(e))
        if fallback:
            return _load_fallback()
        raise
    except Exception as e:
        log.warning(f"FRED API error: {e}")
        if fallback:
            return _load_fallback()
        raise


# ----------------------------------------------------------------
# Internal helpers
# ----------------------------------------------------------------
def _fetch_live(api_key: str, start: str) -> pd.DataFrame:
    from fredapi import Fred
    fred = Fred(api_key=api_key)
    frames: list[pd.DataFrame] = []
    for col_name, series_id in SERIES.items():
        log.info(f"  Fetching {series_id} -> {col_name} ...")
        raw = fred.get_series(series_id, observation_start=start)
        df  = (raw
               .rename(col_name)
               .reset_index()
               .rename(columns={"index": "date"}))
        # Quarterly series: resample to monthly via forward-fill
        if col_name in ("m2_velocity",):
            df["date"] = pd.to_datetime(df["date"])
            df = (df.set_index("date")
                    .resample("MS").first()
                    .ffill()
                    .reset_index())
        frames.append(df)
        log.info(f"    {len(df):,} rows")

    df = reduce(
        lambda a, b: pd.merge(a, b, on="date", how="outer"),
        frames
    ).sort_values("date").reset_index(drop=True)

    return _derive(df)


def _derive(df: pd.DataFrame) -> pd.DataFrame:
    """Compute all derived indicators from raw series."""
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])

    # ICE BofA OAS series are reported by FRED in percent; this repo treats
    # credit spreads in basis points -> convert (matches the static fallback).
    for _c in ("ig_spread", "hy_spread"):
        if _c in df.columns:
            df[_c] = (df[_c] * 100).round(0)

    # Inflation
    df["cpi_yoy"] = df["cpi_index"].pct_change(12, fill_method=None).mul(100).round(3)

    # Real rate (Fisher equation: r = i - pi^e)
    df["real_rate"] = (df["fed_funds"] - df["cpi_yoy"]).round(3)

    # Yield curve
    df["spread_10_2"]   = (df["rate_10y"] - df["rate_2y"]).round(3)
    df["spread_30_2"]   = (df["rate_30y"] - df["rate_2y"]).round(3)
    df["inverted"]      = (df["spread_10_2"] < 0).astype(int)

    # Mortgage spread (over 10y Treasury)
    df["mortgage_spread"] = (df["mortgage_30y"] - df["rate_10y"]).round(3)

    # Taylor Rule (simplified: equal weights, r* = 0.5%, NAIRU = 4.0%)
    RSTAR   = 0.5
    PI_STAR = 2.0
    NAIRU   = 4.0
    df["output_gap_proxy"] = (-2.0 * (df["unemployment"] - NAIRU)).round(2)
    df["taylor_rule"] = (
        df["cpi_yoy"]
        + RSTAR
        + 0.5 * (df["cpi_yoy"] - PI_STAR)
        + 0.5 * df["output_gap_proxy"]
    ).round(3)
    df["taylor_gap"] = (df["taylor_rule"] - df["fed_funds"]).round(3)

    # M2 annual growth
    df["m2_yoy"] = df["m2"].pct_change(12, fill_method=None).mul(100).round(2)

    return df


def _load_fallback() -> pd.DataFrame:
    if not FALLBACK_CSV.exists():
        raise FileNotFoundError(
            f"Fallback CSV not found at {FALLBACK_CSV}.\n"
            "Run: python datasets/download.py --no-api"
        )
    log.info(f"  Loading fallback CSV from {FALLBACK_CSV}")
    df = pd.read_csv(FALLBACK_CSV, parse_dates=["date"])
    log.info(f"  {len(df):,} rows loaded from fallback")
    return df


# ----------------------------------------------------------------
# Standalone entry point
# ----------------------------------------------------------------
if __name__ == "__main__":
    log.info("=== fetch_fred.py ===")
    df = fetch()

    # Save CSV fallback
    out_csv = DATASETS / "fred_rates.csv"
    df.to_csv(out_csv, index=False)
    log.info(f"Saved {len(df):,} rows to {out_csv}")

    # Load into database
    engine = get_engine()
    df.to_sql("fred_rates", engine, if_exists="replace", index=False)
    log.info("Loaded into macro.db -> fred_rates")

    # Preview tail
    cols = ["date", "fed_funds", "cpi_yoy", "real_rate",
            "spread_10_2", "inverted", "hy_spread", "taylor_gap"]
    print("\n", df[cols].tail(12).to_string(index=False))
