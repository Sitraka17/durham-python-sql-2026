.PHONY: all setup data db pipeline dashboard track-a track-b track-c ml verify test clean

PYTHON := .venv/bin/python

# ----------------------------------------------------------------
# Full setup from scratch
# ----------------------------------------------------------------
all: setup data db
	@echo ""
	@echo "=== Ready. Open VS Code and select the .venv interpreter. ==="
	@echo "    Run: make pipeline   — to run the Block 5 ETL pipeline"
	@echo "    Run: make dashboard  — to generate the full financial dashboard"

# ----------------------------------------------------------------
# Create virtual environment and install dependencies
# ----------------------------------------------------------------
setup:
	python3 -m venv .venv
	$(PYTHON) -m pip install --upgrade pip -q
	$(PYTHON) -m pip install -r requirements.txt -q
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "Created .env — add your FRED_KEY before running 'make data'"; \
	fi

# ----------------------------------------------------------------
# Download all datasets
# ----------------------------------------------------------------
data:
	$(PYTHON) datasets/download.py

# ----------------------------------------------------------------
# Build the SQLite database from downloaded CSVs
# ----------------------------------------------------------------
db:
	$(PYTHON) scripts/setup_db.py

# ----------------------------------------------------------------
# Run the Block 5 ETL pipeline end-to-end
# ----------------------------------------------------------------
pipeline:
	$(PYTHON) scripts/pipeline.py

# ----------------------------------------------------------------
# Generate the full five-panel financial dashboard
# ----------------------------------------------------------------
dashboard:
	$(PYTHON) scripts/financial_indicators.py

# ----------------------------------------------------------------
# Run capstone tracks
# ----------------------------------------------------------------
track-a:
	$(PYTHON) capstone/track_a/analysis.py

track-b:
	$(PYTHON) capstone/track_b/analysis.py

track-c:
	$(PYTHON) capstone/track_c/analysis.py

# ----------------------------------------------------------------
# Run all Block 7 machine-learning scripts (local, CPU)
# ----------------------------------------------------------------
ml:
	$(PYTHON) ml/recession_prediction.py
	$(PYTHON) ml/inflation_forecast.py
	$(PYTHON) ml/taylor_rule_regression.py
	$(PYTHON) ml/country_clustering.py

# ----------------------------------------------------------------
# End-to-end self-check (offline) — mirrors what CI does
# ----------------------------------------------------------------
verify:
	$(PYTHON) datasets/download.py --no-api
	$(PYTHON) scripts/setup_db.py
	$(PYTHON) scripts/utils.py
	$(PYTHON) scripts/pipeline.py
	@echo "=== verify OK: data built, DB populated, pipeline ran ==="

# ----------------------------------------------------------------
# Verify the database
# ----------------------------------------------------------------
test:
	$(PYTHON) scripts/utils.py

# ----------------------------------------------------------------
# Clean generated files (keeps raw datasets)
# ----------------------------------------------------------------
clean:
	rm -f db/*.db
	rm -f outputs/*.png outputs/*.csv
	find . -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.ipynb_checkpoints" -exec rm -rf {} + 2>/dev/null || true
	@echo "Cleaned db/ and outputs/"
