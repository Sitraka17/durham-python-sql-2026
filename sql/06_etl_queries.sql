-- 📖 New here? A plain-English (Feynman-style) explanation of every
-- concept below — the economics, the SQL, the why — is in
-- docs/concepts_explained.md. Read it alongside this file.
-- ----------------------------------------------------------------
-- ================================================================
-- 06_etl_queries.sql
-- Block 5 — SQL queries run INSIDE the Python ETL pipeline
--
-- These are the queries called via pandas.read_sql_query() in
-- scripts/pipeline.py and scripts/financial_indicators.py.
-- They demonstrate the Python × SQL integration pattern.
--
-- You can also run them directly in SQLite Viewer against fred_macro
-- (the table written by scripts/pipeline.py).
--
-- PREREQUISITE: run `python scripts/pipeline.py` once first. Its ETL "load"
-- step creates the fred_macro table that every query below reads. (The other
-- sql/*.sql files only need `python scripts/setup_db.py`.)
-- ================================================================


-- ----------------------------------------------------------------
-- The main pipeline query: full dashboard in one SQL statement
-- Run by pipeline.py via read_sql_query()
-- ----------------------------------------------------------------
WITH spread AS (
    SELECT
        date,
        fed_funds,
        real_rate,
        spread_10_2,
        inverted,
        taylor_rule,
        taylor_gap,
        hy_spread,
        ig_spread,
        -- 12-month moving average of yield spread
        AVG(spread_10_2)
            OVER (ORDER BY date
                  ROWS BETWEEN 11 PRECEDING AND CURRENT ROW)   AS ma12_spread,
        -- Cumulative months inverted (running total since 2000)
        SUM(inverted)
            OVER (ORDER BY date
                  ROWS UNBOUNDED PRECEDING)                     AS cum_inv_months,
        -- Year-on-year change in HY spread (risk stress signal)
        ROUND(
            hy_spread - LAG(hy_spread, 12) OVER (ORDER BY date),
            0
        )                                                       AS hy_spread_yoy
    FROM fred_macro                 -- table written by pipeline.py
    WHERE date >= '2000-01-01'
)
SELECT * FROM spread ORDER BY date;


-- ----------------------------------------------------------------
-- Inversion episode summary (read by financial_indicators.py)
-- ----------------------------------------------------------------
WITH spread AS (
    SELECT date, spread_10_2, inverted,
           inverted - LAG(inverted, 1, 0)
               OVER (ORDER BY date) AS episode_start
    FROM fred_macro
    WHERE spread_10_2 IS NOT NULL
),
episode_ids AS (
    SELECT date, spread_10_2, inverted,
           SUM(CASE WHEN episode_start = 1 THEN 1 ELSE 0 END)
               OVER (ORDER BY date ROWS UNBOUNDED PRECEDING) AS episode_id
    FROM spread
)
SELECT episode_id,
       MIN(date)                        AS start_month,
       MAX(date)                        AS end_month,
       COUNT(*)                         AS months_inverted,
       ROUND(MIN(spread_10_2), 3)       AS deepest_pp,
       ROUND(MIN(spread_10_2) * 100, 1) AS deepest_bp
FROM   episode_ids
WHERE  inverted = 1
GROUP  BY episode_id
HAVING months_inverted >= 2
ORDER  BY deepest_pp ASC;


-- ----------------------------------------------------------------
-- Taylor Rule gap history (read for policy assessment chart)
-- ----------------------------------------------------------------
SELECT date,
       ROUND(fed_funds, 2)   AS actual,
       ROUND(taylor_rule, 2)  AS implied,
       ROUND(taylor_gap, 2)   AS gap,
       ROUND(
           AVG(taylor_gap)
           OVER (ORDER BY date
                 ROWS BETWEEN 5 PRECEDING AND CURRENT ROW)
       , 2)                   AS ma6_gap
FROM   fred_macro
WHERE  taylor_gap IS NOT NULL
  AND  date >= '2000-01-01'
ORDER  BY date;


-- ----------------------------------------------------------------
-- Credit market stress indicator (IG + HY together)
-- ----------------------------------------------------------------
SELECT date,
       ROUND(ig_spread, 0)              AS ig_bp,
       ROUND(hy_spread, 0)              AS hy_bp,
       ROUND(hy_spread / ig_spread, 2)  AS hy_ig_ratio,  -- measures relative stress
       ROUND(
           AVG(hy_spread)
           OVER (ORDER BY date
                 ROWS BETWEEN 11 PRECEDING AND CURRENT ROW)
       , 0)                             AS ma12_hy
FROM   fred_macro
WHERE  ig_spread IS NOT NULL
  AND  hy_spread IS NOT NULL
  AND  date >= '2000-01-01'
ORDER  BY date;
