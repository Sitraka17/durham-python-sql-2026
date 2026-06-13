"""
datasets/_build_static_csvs.py
==============================
PROVENANCE / INSTRUCTOR SCRIPT — students never need to run this.

This is how the bundled static fallback CSVs in this folder were produced.
It pulls REAL data from public, key-less endpoints so the offline
(`download.py --no-api`) path reproduces genuine macro history:

    datasets/wdi_indicators.csv            World Bank WDI REST API
    datasets/fred_rates_static.csv         FRED key-less fredgraph CSV endpoint
    datasets/oecd_unemployment_static.csv  FRED-hosted OECD harmonised series

Everything is resampled to a clean MONTHLY (FRED) / QUARTERLY (OECD) cadence
and the derived indicators are computed with the SAME formulae as
datasets/download.py, so the static path and the live-API path yield an
identical schema.

To refresh the bundled data (e.g. next year):

    python datasets/_build_static_csvs.py

Requires network access to fred.stlouisfed.org and api.worldbank.org.
"""
import io
import os
import json
import time
import logging
from pathlib import Path

import requests
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(message)s")
log = logging.getLogger("build_static")

HERE = Path(__file__).parent
START = "1990-01-01"
WB_YEARS = "1990:2024"

# Optional on-disk cache of raw API responses. Lets a flaky/throttled network
# be primed once (e.g. via curl) and then read locally for a deterministic
# build. Set STATIC_CACHE=/path to point elsewhere.
CACHE = Path(os.getenv("STATIC_CACHE", HERE / ".cache"))
CACHE.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------
# Shared HTTP helper (small retry — these endpoints are public + flaky)
# ----------------------------------------------------------------
def _get(url: str, tries: int = 5, timeout: int = 60) -> requests.Response:
    last = None
    for i in range(tries):
        try:
            r = requests.get(url, timeout=timeout,
                             headers={"User-Agent": "durham-course/1.0"})
            r.raise_for_status()
            return r
        except Exception as e:          # noqa: BLE001
            last = e
            log.warning(f"  retry {i + 1}/{tries}: {e}")
            time.sleep(2)
    raise RuntimeError(f"GET failed after {tries} tries: {url}\n{last}")


# ----------------------------------------------------------------
# 1. FRED monetary / credit series  ->  fred_rates_static.csv
# ----------------------------------------------------------------
FRED_SERIES = {           # column name : FRED series id (native frequency)
    "fed_funds":    "FEDFUNDS",        # M
    "rate_2y":      "GS2",             # M
    "rate_10y":     "GS10",            # M
    "rate_30y":     "GS30",            # M (gap 2002-2006)
    "cpi_index":    "CPIAUCSL",        # M
    "core_pce":     "PCEPILFE",        # M
    "m2":           "M2SL",            # M
    "m2_velocity":  "M2V",             # Q
    "unemployment": "UNRATE",          # M
    "payrolls":     "PAYEMS",          # M
    "lfpr":         "CIVPART",          # M
    "ig_spread":    "BAMLC0A0CM",      # D
    "hy_spread":    "BAMLH0A0HYM2",    # D
    "mortgage_30y": "MORTGAGE30US",    # W
    "fed_assets":   "WALCL",           # W
    "recession":    "USREC",           # M, NBER recession indicator (0/1) — ML target
}
LOW_FREQ_FFILL = {"m2_velocity"}      # quarterly -> forward fill across months


# Some series need extra query params on the key-less fredgraph endpoint.
# BAA10Y is a *daily* series whose full history is only returned when asked
# for monthly aggregation (the raw daily pull is truncated to a few years).
FRED_FETCH_PARAMS = {"BAA10Y": "&fq=Monthly&fam=avg"}


def _fred_text(series_id: str) -> str:
    """Raw CSV text for a FRED series, from cache if present else network."""
    cached = CACHE / f"fred_{series_id}.csv"
    if cached.exists() and cached.stat().st_size > 0:
        return cached.read_text()
    extra = FRED_FETCH_PARAMS.get(series_id, "")
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}{extra}"
    raw = _get(url).text
    cached.write_text(raw)
    return raw


def _fred_csv(series_id: str) -> pd.Series:
    """Download one FRED series from the key-less fredgraph CSV endpoint."""
    raw = _fred_text(series_id)
    df = pd.read_csv(io.StringIO(raw))
    # First column is the date (observation_date / DATE), second is the value.
    date_col, val_col = df.columns[0], df.columns[1]
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df[val_col] = pd.to_numeric(df[val_col], errors="coerce")  # "." -> NaN
    s = df.set_index(date_col)[val_col].dropna()
    # Collapse to month-start cadence: monthly stays put, daily/weekly averaged.
    return s.resample("MS").mean()


def _reconstruct_credit_spreads(df: pd.DataFrame) -> None:
    """Put ig_spread / hy_spread on a full-history basis-point footing.

    The codebase treats both columns as ICE BofA OAS in *basis points*.
    The public fredgraph endpoint only exposes the last ~3 years of the
    licensed ICE BofA OAS series, so we:

      1. Convert the real, recent ICE OAS (percent) to basis points (x100).
      2. Backfill the pre-2023 history from the full-history, key-less
         Moody's Baa-10y credit spread (BAA10Y), rescaled to OAS levels by
         the median ratio over the overlap window. Both inputs are real
         FRED series; the historical tail is a real-spread reconstruction,
         not synthetic noise. It reproduces the GFC, COVID and 2022 spikes.
    """
    df["ig_spread"] = (df["ig_spread"] * 100).round(0)   # percent -> bp
    df["hy_spread"] = (df["hy_spread"] * 100).round(0)

    baa = (_fred_csv("BAA10Y") * 100).reindex(df.index)   # bp, 1986+
    for col, label in (("ig_spread", "IG"), ("hy_spread", "HY")):
        overlap = df[col].notna() & baa.notna()
        ratio = float((df.loc[overlap, col] / baa[overlap]).median())
        backfill = (baa * ratio).round(0)
        n_real = int(df[col].notna().sum())
        df[col] = df[col].where(df[col].notna(), backfill)
        log.info(f"  {label} spread: {n_real} real ICE months + "
                 f"BAA10Y x{ratio:.2f} backfill -> {int(df[col].notna().sum())} total")


def build_fred() -> None:
    log.info(f"FRED: downloading {len(FRED_SERIES)} series (key-less)...")
    cols = {}
    for name, sid in FRED_SERIES.items():
        s = _fred_csv(sid)
        cols[name] = s
        log.info(f"  {sid:<14} -> {name:<13} {len(s):>4} monthly obs")
    df = pd.DataFrame(cols).sort_index()
    df = df[df.index >= START]

    for c in LOW_FREQ_FFILL:
        df[c] = df[c].ffill()

    _reconstruct_credit_spreads(df)

    # ---- Derived indicators (identical formulae to download.py) ----
    df["cpi_yoy"]         = df["cpi_index"].pct_change(12, fill_method=None).mul(100).round(3)
    df["real_rate"]       = (df["fed_funds"] - df["cpi_yoy"]).round(3)
    df["spread_10_2"]     = (df["rate_10y"] - df["rate_2y"]).round(3)
    df["spread_30_2"]     = (df["rate_30y"] - df["rate_2y"]).round(3)
    df["inverted"]        = (df["spread_10_2"] < 0).astype(int)
    df["mortgage_spread"] = (df["mortgage_30y"] - df["rate_10y"]).round(3)
    df["m2_yoy"]          = df["m2"].pct_change(12, fill_method=None).mul(100).round(2)

    RSTAR, PI_STAR, NAIRU = 0.5, 2.0, 4.0
    df["output_gap_proxy"] = (-2.0 * (df["unemployment"] - NAIRU)).round(3)
    df["taylor_rule"] = (
        df["cpi_yoy"] + RSTAR
        + 0.5 * (df["cpi_yoy"] - PI_STAR)
        + 0.5 * df["output_gap_proxy"]
    ).round(3)
    df["taylor_gap"] = (df["taylor_rule"] - df["fed_funds"]).round(3)

    # NBER recession label (0/1). The newest month may not be classified yet —
    # fill it with 0 (no recession declared) so the column is a clean integer.
    df["recession"] = df["recession"].fillna(0).astype(int)

    df = df.reset_index().rename(columns={"index": "date"})
    df = df.rename(columns={df.columns[0]: "date"})
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")

    order = (["date"] + list(FRED_SERIES.keys())
             + ["cpi_yoy", "real_rate", "spread_10_2", "spread_30_2", "inverted",
                "mortgage_spread", "m2_yoy", "output_gap_proxy",
                "taylor_rule", "taylor_gap"])
    df = df[order]

    out = HERE / "fred_rates_static.csv"
    df.to_csv(out, index=False)
    log.info(f"FRED: wrote {len(df):,} rows x {len(df.columns)} cols -> {out.name}")

    # Quick reality check against the brief's verified facts
    _sanity_fred(df)


def _sanity_fred(df: pd.DataFrame) -> None:
    d = df.set_index("date")
    def show(label, col, idx):
        if idx in d.index:
            log.info(f"    {label}: {d.loc[idx, col]}")
    log.info("  -- sanity (vs verified facts) --")
    peak_ff = d["fed_funds"].max()
    log.info(f"    Fed funds peak       : {peak_ff}  (brief: 5.25-5.50%)")
    peak_cpi = d["cpi_yoy"].max()
    log.info(f"    CPI YoY peak         : {peak_cpi}  (brief: 9.1%)")
    trough = d["spread_10_2"].min()
    log.info(f"    10y-2y trough (mthly): {trough}  (brief daily: -1.09)")


# ----------------------------------------------------------------
# 2. World Bank WDI panel  ->  wdi_indicators.csv
# ----------------------------------------------------------------
COUNTRIES = [
    "USA", "GBR", "DEU", "FRA", "JPN", "CHN", "IND", "BRA", "CAN", "AUS",
    "KOR", "ITA", "ESP", "NLD", "CHE", "SWE", "NOR", "DNK", "FIN", "BEL",
    "MEX", "ARG", "ZAF", "NGA", "EGY", "TUR", "IDN", "SAU", "POL", "CZE",
    "LUX", "IRL", "PRT", "GRC", "HUN", "COL", "CHL", "PER", "VNM", "THA",
]
WDI_INDICATORS = {
    "NY.GDP.PCAP.CD":   "gdp_per_capita",
    "FP.CPI.TOTL.ZG":   "inflation",
    "SL.UEM.TOTL.ZS":   "unemployment",
    "NY.GDP.MKTP.KD.ZG": "gdp_growth",
    "GC.NLD.TOTL.GD.ZS": "fiscal_balance",
    "BN.CAB.XOKA.GD.ZS": "current_account",
}


def _wb_indicator(code: str) -> pd.DataFrame:
    codes = ";".join(COUNTRIES)
    url = (f"https://api.worldbank.org/v2/country/{codes}/indicator/{code}"
           f"?format=json&per_page=20000&date={WB_YEARS}")
    cached = CACHE / f"wb_{code}.json"
    if cached.exists() and cached.stat().st_size > 0:
        data = json.loads(cached.read_text())
    else:
        data = _get(url).json()
        cached.write_text(json.dumps(data))
    if not isinstance(data, list) or len(data) < 2 or data[1] is None:
        log.warning(f"  WDI {code}: empty response")
        return pd.DataFrame(columns=["country_code", "year", code])
    rows = []
    for obs in data[1]:
        iso3 = obs.get("countryiso3code") or (obs.get("country") or {}).get("id")
        if obs.get("value") is None or not iso3:
            continue
        rows.append((iso3, int(obs["date"]), obs["value"]))
    return pd.DataFrame(rows, columns=["country_code", "year", code])


def build_wdi() -> None:
    log.info("WDI: downloading 6 indicators from World Bank REST API...")
    merged = None
    for code, name in WDI_INDICATORS.items():
        df = _wb_indicator(code).rename(columns={code: name})
        log.info(f"  {code:<18} -> {name:<15} {len(df):>5} obs")
        merged = df if merged is None else merged.merge(
            df, on=["country_code", "year"], how="outer")
    merged = merged.sort_values(["country_code", "year"]).reset_index(drop=True)
    order = (["country_code", "year"] + list(WDI_INDICATORS.values()))
    merged = merged[order]
    out = HERE / "wdi_indicators.csv"
    merged.to_csv(out, index=False)
    log.info(f"WDI: wrote {len(merged):,} rows -> {out.name}")


# ----------------------------------------------------------------
# 3. OECD harmonised quarterly unemployment  ->  oecd_unemployment_static.csv
#    Pulled via FRED-hosted OECD series (LRHUTTTT..Q156S, % SA).
# ----------------------------------------------------------------
OECD_Q_SERIES = {           # WDI iso3 : FRED OECD series id
    "USA": "LRHUTTTTUSQ156S",
    "GBR": "LRHUTTTTGBQ156S",
    "DEU": "LRHUTTTTDEQ156S",
    "FRA": "LRHUTTTTFRQ156S",
    "JPN": "LRHUTTTTJPQ156S",
    "ITA": "LRHUTTTTITQ156S",
    "CAN": "LRHUTTTTCAQ156S",
    "AUS": "LRHUTTTTAUQ156S",
    "ESP": "LRHUTTTTESQ156S",
    "KOR": "LRHUTTTTKRQ156S",
    "NLD": "LRHUTTTTNLQ156S",
    "SWE": "LRHUTTTTSEQ156S",
}


def build_oecd() -> None:
    log.info("OECD: downloading harmonised quarterly unemployment (key-less)...")
    frames = []
    for iso3, sid in OECD_Q_SERIES.items():
        raw = _fred_text(sid)
        df = pd.read_csv(io.StringIO(raw))
        dcol, vcol = df.columns[0], df.columns[1]
        df[dcol] = pd.to_datetime(df[dcol], errors="coerce")
        df[vcol] = pd.to_numeric(df[vcol], errors="coerce")
        df = df.dropna()
        df = df[df[dcol] >= "2000-01-01"]
        q = df[dcol].dt.year.astype(str) + "-Q" + df[dcol].dt.quarter.astype(str)
        out = pd.DataFrame({
            "country_code": iso3,
            "quarter": q.values,
            "unemployment_rate": df[vcol].round(2).values,
        })
        frames.append(out)
        log.info(f"  {sid:<16} -> {iso3}  {len(out):>3} quarters")
    panel = pd.concat(frames, ignore_index=True)
    panel = panel.sort_values(["country_code", "quarter"]).reset_index(drop=True)
    dest = HERE / "oecd_unemployment_static.csv"
    panel.to_csv(dest, index=False)
    log.info(f"OECD: wrote {len(panel):,} rows -> {dest.name}")


if __name__ == "__main__":
    log.info("=== Building static fallback CSVs from real public data ===")
    build_fred()
    build_wdi()
    build_oecd()
    log.info("=== Done. Commit datasets/*_static.csv + wdi_indicators.csv ===")
