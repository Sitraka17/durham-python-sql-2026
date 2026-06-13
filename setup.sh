#!/usr/bin/env bash
# Durham course — one-shot bootstrap for Mac/Linux/WSL
# Usage: bash setup.sh
set -e

echo "=== Durham University — Advanced Python & SQL ==="
echo "    'Did the Fed's Tightening Cycle Work?'"
echo ""

# 1. Virtual environment
if [ ! -d ".venv" ]; then
    echo "[1/4] Creating virtual environment..."
    python3 -m venv .venv
else
    echo "[1/4] Virtual environment already exists."
fi

# 2. Activate
source .venv/bin/activate

# 3. Install
echo "[2/4] Installing dependencies (this takes ~60s)..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "      Done."

# 4. Environment file
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "[3/4] Created .env"
    echo "      ACTION REQUIRED: edit .env and add your FRED_KEY"
    echo "      Free at: https://fred.stlouisfed.org/docs/api/api_key.html"
else
    echo "[3/4] .env already exists."
fi

echo "[4/4] Setup complete."
echo ""
echo "Next steps:"
echo "  1. Edit .env — add FRED_KEY"
echo "  2. python datasets/download.py"
echo "  3. python scripts/setup_db.py"
echo "  4. python scripts/utils.py  (verify)"
echo "  5. Open VS Code — select .venv as Python interpreter"
echo ""
echo "Quick run (Block 5 pipeline):"
echo "  python scripts/pipeline.py"
