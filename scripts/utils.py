"""
scripts/utils.py
================
Shared utilities used by every script in this repository.

Provides:
  - Canonical path constants
  - SQLAlchemy engine factory (singleton)
  - Logging configuration
  - db_info() for quick sanity checks

Usage:
    from scripts.utils import get_engine, DATASETS, OUTPUTS, log
"""
import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ----------------------------------------------------------------
# Root paths
# ----------------------------------------------------------------
ROOT     = Path(__file__).resolve().parents[1]
DATASETS = ROOT / "datasets"
DB_PATH  = ROOT / os.getenv("DB_PATH", "db/macro.db")
OUTPUTS  = ROOT / "outputs"

# Ensure generated directories exist at import time
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
OUTPUTS.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------
# Logging
# ----------------------------------------------------------------
logging.basicConfig(
    level   = logging.INFO,
    format  = "%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt = "%H:%M:%S",
    stream  = sys.stdout,
)
log = logging.getLogger("durham")


# ----------------------------------------------------------------
# SQLAlchemy engine (singleton — import once, reuse everywhere)
# ----------------------------------------------------------------
_engine = None

def get_engine():
    """Return a cached SQLAlchemy engine for db/macro.db."""
    global _engine
    if _engine is None:
        from sqlalchemy import create_engine
        _engine = create_engine(
            f"sqlite:///{DB_PATH}",
            connect_args={"check_same_thread": False},
        )
    return _engine


# ----------------------------------------------------------------
# Quick database health check
# ----------------------------------------------------------------
def db_info():
    """Print row counts for all tables in macro.db."""
    from sqlalchemy import text
    engine = get_engine()
    with engine.connect() as conn:
        tables = conn.execute(
            text("SELECT name FROM sqlite_master "
                 "WHERE type='table' ORDER BY name")
        ).fetchall()
        if not tables:
            print("  (database is empty — run: python scripts/setup_db.py)")
            return
        for (t,) in tables:
            n = conn.execute(text(f"SELECT COUNT(*) FROM [{t}]")).scalar()
            print(f"  {t:<32} {n:>9,} rows")


# ----------------------------------------------------------------
# FRED key helper
# ----------------------------------------------------------------
def fred_key() -> str:
    """Return FRED API key from .env, or raise with a clear message."""
    key = os.getenv("FRED_KEY", "")
    if not key or key == "your_fred_api_key_here":
        raise EnvironmentError(
            "FRED_KEY not set.\n"
            "1. Get a free key at https://fred.stlouisfed.org/docs/api/api_key.html\n"
            "2. Edit .env and set FRED_KEY=<your_key>\n"
            "   OR: export FRED_KEY=<your_key> in your terminal"
        )
    return key


# ----------------------------------------------------------------
# Run as script: report DB status
# ----------------------------------------------------------------
if __name__ == "__main__":
    print(f"DB  : {DB_PATH}")
    print(f"Data: {DATASETS}")
    print(f"Out : {OUTPUTS}")
    print()
    db_info()
