# 📖 New here? Plain-English concepts: docs/concepts_explained.md ·
# Why we code it this way: docs/why_we_code_this.md
"""
datasets/fetch_kaggle.py
========================
Bring a Kaggle dataset into the course's workflow — download it, peek at it,
and (optionally) load it straight into the SQLite database so you can query it
with SQL like everything else.

WHY add Kaggle?
  FRED / World Bank / OECD give you clean *official* macro series. Kaggle is the
  other half of the data world: thousands of community datasets — firm-level
  panels, alternative data, scraped prices, surveys — perfect for a dissertation
  that needs something the official sources don't publish.

WHY a script (not just clicking "Download" on the website)?
  REPRODUCIBILITY again. A scripted, named download (with the dataset slug and
  version) is something you — and your examiner — can re-run to get the exact
  same data. A file you hand-downloaded into Downloads/ is not reproducible.
  (See docs/why_we_code_this.md §5.)

ONE-TIME SETUP (free Kaggle account needed):
  1. kaggle.com -> your avatar -> Settings -> API -> "Create New Token".
     This downloads `kaggle.json` (your username + key).
  2. Put it where the client looks for it:
        mkdir -p ~/.kaggle && mv ~/Downloads/kaggle.json ~/.kaggle/
        chmod 600 ~/.kaggle/kaggle.json
     OR set environment variables (best in Codespaces — add them as
     *Codespaces secrets* named KAGGLE_USERNAME and KAGGLE_KEY):
        export KAGGLE_USERNAME=... ; export KAGGLE_KEY=...

USAGE:
  python datasets/fetch_kaggle.py <owner/dataset-slug>
  python datasets/fetch_kaggle.py <owner/dataset-slug> --to-db my_table
  # e.g. the slug for kaggle.com/datasets/<owner>/<name> is "<owner>/<name>"

Runs with NO credentials too: it just prints the setup steps and exits cleanly,
so it never breaks the build.
"""
import os
import sys
import argparse
import pathlib

import pandas as pd

# --- make the `scripts` package importable when run directly --------------
import sys as _sys, pathlib as _pl
for _p in _pl.Path(__file__).resolve().parents:
    if (_p / "scripts" / "utils.py").exists():
        if str(_p) not in _sys.path:
            _sys.path.insert(0, str(_p))
        break
# --------------------------------------------------------------------------

from scripts.utils import log


# ----------------------------------------------------------------
# Credentials — check WITHOUT importing kaggle (so the file is safe to import)
# ----------------------------------------------------------------
def has_credentials() -> bool:
    """True if a Kaggle token is available via env vars or ~/.kaggle/kaggle.json."""
    if os.getenv("KAGGLE_USERNAME") and os.getenv("KAGGLE_KEY"):
        return True
    return (pathlib.Path.home() / ".kaggle" / "kaggle.json").exists()


SETUP_HELP = """\
No Kaggle credentials found. This step is OPTIONAL — the course runs fully
without it. To enable Kaggle downloads:

  1. Create a free account at https://www.kaggle.com
  2. kaggle.com -> Settings -> API -> "Create New Token"  (downloads kaggle.json)
  3. Either place the file:
         mkdir -p ~/.kaggle && mv ~/Downloads/kaggle.json ~/.kaggle/
         chmod 600 ~/.kaggle/kaggle.json
     OR set environment variables:
         export KAGGLE_USERNAME=your_username
         export KAGGLE_KEY=your_key
     (In GitHub Codespaces, add KAGGLE_USERNAME and KAGGLE_KEY as Codespaces
      secrets so they're available automatically.)

Then re-run:  python datasets/fetch_kaggle.py <owner/dataset-slug>
"""


# ----------------------------------------------------------------
# Core helpers
# ----------------------------------------------------------------
def download(slug: str) -> pathlib.Path:
    """Download a Kaggle dataset and return the local folder it landed in."""
    import kagglehub                       # lazy import: only needed here
    log.info(f"Kaggle: downloading '{slug}' ...")
    path = pathlib.Path(kagglehub.dataset_download(slug))
    log.info(f"Kaggle: downloaded to {path}")
    return path


def load_csvs(folder: pathlib.Path) -> dict[str, pd.DataFrame]:
    """Read every CSV in the downloaded folder into a {name: DataFrame} dict."""
    frames = {}
    for csv in sorted(folder.rglob("*.csv")):
        try:
            frames[csv.stem] = pd.read_csv(csv)
        except Exception as e:               # noqa: BLE001
            log.warning(f"  could not read {csv.name}: {e}")
    return frames


def to_sqlite(df: pd.DataFrame, table: str) -> None:
    """Load a DataFrame into the course database so you can query it in SQL.

    WHY put it in the DB? So Kaggle data joins the same workflow as everything
    else — query it with SQL, JOIN it to the FRED/World Bank tables, build views.
    """
    from scripts.utils import get_engine
    df.to_sql(table, get_engine(), if_exists="replace", index=False)
    log.info(f"  loaded {len(df):,} rows into table '{table}' (db/macro.db)")


# ----------------------------------------------------------------
# Main
# ----------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description="Fetch a Kaggle dataset.")
    ap.add_argument("slug", nargs="?",
                    help="Kaggle dataset slug, e.g. 'owner/dataset-name'")
    ap.add_argument("--to-db", metavar="TABLE",
                    help="also load the first/largest CSV into db/macro.db as TABLE")
    args = ap.parse_args()

    if not has_credentials():
        print(SETUP_HELP)
        return 0                              # graceful: never break the build

    if not args.slug:
        log.info("Credentials OK. Pass a dataset slug, e.g.:")
        log.info("  python datasets/fetch_kaggle.py owner/dataset-name")
        return 0

    folder = download(args.slug)
    frames = load_csvs(folder)
    if not frames:
        log.warning("No CSV files found in that dataset.")
        return 0

    log.info(f"Found {len(frames)} CSV file(s):")
    for name, df in frames.items():
        log.info(f"  {name}: {df.shape[0]:,} rows x {df.shape[1]} cols "
                 f"-> columns: {list(df.columns)[:8]}{' ...' if df.shape[1] > 8 else ''}")

    if args.to_db:
        # load the CSV with the most rows (usually the main table)
        main_name = max(frames, key=lambda k: len(frames[k]))
        to_sqlite(frames[main_name], args.to_db)
        log.info(f"Try it:  SELECT * FROM {args.to_db} LIMIT 5;")

    return 0


if __name__ == "__main__":
    sys.exit(main())
