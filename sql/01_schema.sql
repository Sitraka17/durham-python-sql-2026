-- 📖 New here? A plain-English (Feynman-style) explanation of every
-- concept below — the economics, the SQL, the why — is in
-- docs/concepts_explained.md. Read it alongside this file.
-- ----------------------------------------------------------------
-- ================================================================
-- 01_schema.sql
-- Block 1 — Database schema
-- Run: sqlite3 db/macro.db < sql/01_schema.sql
--   OR: open this file in VS Code SQLite Viewer and run manually
-- ================================================================

-- ----------------------------------------------------------------
-- Dimension table: countries
-- One row per country — static reference data.
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS countries (
    country_code   TEXT PRIMARY KEY,   -- ISO 3166-1 alpha-3
    country_name   TEXT NOT NULL,
    region         TEXT,               -- Geographic region
    income_group   TEXT,               -- High / Upper middle / Lower middle / Low
    g20            INTEGER DEFAULT 0,  -- 1 = G20 member
    eu_member      INTEGER DEFAULT 0   -- 1 = EU member state
);

-- ----------------------------------------------------------------
-- Fact table: annual macroeconomic indicators
-- Many rows per country (one per year).
-- Linked to countries via country_code (foreign key).
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS indicators (
    country_code    TEXT    REFERENCES countries(country_code),
    year            INTEGER NOT NULL,
    gdp_per_capita  REAL,   -- GDP per capita, current USD
    inflation       REAL,   -- CPI inflation, annual %
    unemployment    REAL,   -- Unemployment rate, % of labour force
    gdp_growth      REAL,   -- Real GDP growth, annual %
    fiscal_balance  REAL,   -- General govt balance, % of GDP
    current_account REAL,   -- Current account balance, % of GDP
    PRIMARY KEY (country_code, year)
);

-- ----------------------------------------------------------------
-- Fact table: FRED monthly financial & monetary series
-- One row per month (date = first of month, YYYY-MM-DD).
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fred_rates (
    date             TEXT    PRIMARY KEY,  -- YYYY-MM-DD
    -- Monetary policy
    fed_funds        REAL,  -- Federal Funds Rate, %
    rate_2y          REAL,  -- 2-year Treasury yield, %
    rate_10y         REAL,  -- 10-year Treasury yield, %
    rate_30y         REAL,  -- 30-year Treasury yield, %
    -- Inflation & money
    cpi_index        REAL,  -- CPI All Urban Consumers (index level)
    core_pce         REAL,  -- Core PCE price index (level)
    m2               REAL,  -- M2 money supply, billions USD
    m2_velocity      REAL,  -- M2 velocity (quarterly, forward-filled)
    -- Labour market
    unemployment     REAL,  -- US civilian unemployment rate, %
    payrolls         REAL,  -- Non-farm payrolls, thousands
    lfpr             REAL,  -- Labour force participation rate, %
    -- Credit & mortgage
    ig_spread        REAL,  -- ICE BofA IG corporate spread, bp
    hy_spread        REAL,  -- ICE BofA HY corporate spread, bp
    mortgage_30y     REAL,  -- 30-year fixed mortgage rate, %
    -- Fed balance sheet
    fed_assets       REAL,  -- Fed total assets, millions USD
    -- Machine-learning target
    recession        INTEGER, -- NBER recession indicator (1=recession), USREC
    -- Derived series (computed by fetch_fred.py)
    cpi_yoy          REAL,  -- 12-month CPI inflation rate, %
    real_rate        REAL,  -- Fisher real FFR = fed_funds - cpi_yoy, %
    spread_10_2      REAL,  -- 10y minus 2y yield, pp
    spread_30_2      REAL,  -- 30y minus 2y yield, pp
    inverted         INTEGER, -- 1 if rate_10y < rate_2y
    mortgage_spread  REAL,  -- mortgage_30y minus rate_10y, pp
    m2_yoy           REAL,  -- M2 annual growth rate, %
    output_gap_proxy REAL,  -- -2 * (UNRATE - NAIRU), Okun's law
    taylor_rule      REAL,  -- Taylor Rule implied rate, %
    taylor_gap       REAL   -- taylor_rule - fed_funds, pp
);

-- ----------------------------------------------------------------
-- Fact table: OECD quarterly unemployment
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS oecd_unemployment (
    country_code      TEXT,
    quarter           TEXT,   -- Format: YYYY-QN  e.g. "2022-Q3"
    unemployment_rate REAL,
    PRIMARY KEY (country_code, quarter)
);
