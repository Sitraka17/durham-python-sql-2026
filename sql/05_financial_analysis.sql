-- 📖 New here? A plain-English (Feynman-style) explanation of every
-- concept below — the economics, the SQL, the why — is in
-- docs/concepts_explained.md. Read it alongside this file.
-- ----------------------------------------------------------------
-- ================================================================
-- 05_financial_analysis.sql
-- Block 3 & 4 Finance Spotlight
--
-- Fisher equation, Taylor Rule, credit spreads, M2 velocity.
-- All queries run against fred_rates (and the views created by
-- setup_db.py).
--
-- These are the queries used by macro analysts and central bank
-- economists every morning.
-- ================================================================


-- ----------------------------------------------------------------
-- SECTION 1: Fisher equation — real interest rate
--
-- r_real ≈ i_nominal - π_expected
-- We use realised CPI YoY as the proxy for π_expected (ex-post).
-- ----------------------------------------------------------------

-- Monthly real rate since 2000
SELECT date,
       ROUND(fed_funds, 2)     AS nominal_rate,
       ROUND(cpi_yoy, 2)       AS cpi_inflation,
       ROUND(real_rate, 2)     AS real_rate,
       CASE
           WHEN real_rate < -3 THEN 'Highly accommodative (r < -3%)'
           WHEN real_rate <  0 THEN 'Accommodative (r < 0%)'
           WHEN real_rate <  2 THEN 'Mildly restrictive (0-2%)'
           ELSE 'Restrictive (r > 2%)'
       END                     AS policy_stance
FROM   fred_rates
WHERE  date >= '2000-01-01'
  AND  cpi_yoy IS NOT NULL
ORDER  BY date;

-- Key dates: when did the real rate turn positive?
-- (This marks the inflection from accommodation to restriction)
SELECT date,
       ROUND(fed_funds, 2)  AS nominal,
       ROUND(cpi_yoy, 2)    AS cpi,
       ROUND(real_rate, 2)  AS real
FROM   fred_rates
WHERE  real_rate IS NOT NULL
  AND  date >= '2022-01-01'
  AND  date <= '2024-12-01'
ORDER  BY date;


-- ----------------------------------------------------------------
-- SECTION 2: Taylor Rule — the benchmark for "right" policy
--
-- i* = π + r* + 0.5(π - π*) + 0.5 * ỹ
--
-- r* (neutral real rate) = 0.5%
-- π* (inflation target)  = 2.0%
-- ỹ (output gap proxy)   = -2 * (UNRATE - NAIRU), Okun coefficient 2
-- NAIRU                  = 4.0%
-- ----------------------------------------------------------------

-- Full Taylor Rule history vs actual FFR
SELECT date,
       ROUND(fed_funds, 2)   AS actual_rate,
       ROUND(cpi_yoy, 2)     AS cpi_inflation,
       ROUND(unemployment, 1) AS unemployment,
       ROUND(taylor_rule, 2)  AS taylor_implied,
       ROUND(taylor_gap, 2)   AS taylor_gap,
       CASE
           WHEN taylor_gap > 5  THEN 'Severely behind curve'
           WHEN taylor_gap > 2  THEN 'Behind curve'
           WHEN taylor_gap > -2 THEN 'Broadly appropriate'
           ELSE 'Ahead of curve / over-tightened'
       END                    AS policy_assessment
FROM   fred_rates
WHERE  date >= '2000-01-01'
  AND  taylor_rule IS NOT NULL
ORDER  BY date;

-- Worst "behind the curve" months (highest Taylor gap)
-- These are the months the Fed was most behind the curve
SELECT date,
       ROUND(fed_funds, 2)   AS actual,
       ROUND(taylor_rule, 2)  AS implied,
       ROUND(taylor_gap, 2)   AS gap
FROM   fred_rates
WHERE  taylor_gap IS NOT NULL
ORDER  BY taylor_gap DESC
LIMIT  20;

-- 6-month moving average of Taylor gap
-- Smoothed view of cumulative behind-the-curve period
SELECT date,
       ROUND(fed_funds, 2)  AS actual,
       ROUND(taylor_gap, 2) AS taylor_gap,
       ROUND(
           AVG(taylor_gap)
           OVER (ORDER BY date
                 ROWS BETWEEN 5 PRECEDING AND CURRENT ROW)
       , 2)                 AS ma6_taylor_gap
FROM   fred_rates
WHERE  date >= '2018-01-01'
  AND  taylor_gap IS NOT NULL
ORDER  BY date;


-- ----------------------------------------------------------------
-- SECTION 3: Yield curve — full analytical pipeline
-- (Uses the v_yield_curve view created by setup_db.py)
-- ----------------------------------------------------------------

-- 3a. All inversion months ranked by depth
SELECT date,
       ROUND(spread_10_2 * 100, 1) AS spread_bp,
       ROUND(ma12_spread, 3)        AS ma12_spread_pp
FROM   v_yield_curve
WHERE  inverted = 1
ORDER  BY spread_10_2 ASC
LIMIT  30;

-- 3b. Inversion episodes with depth and duration
WITH spread AS (
    SELECT date, spread_10_2, inverted,
           inverted - LAG(inverted, 1, 0)
               OVER (ORDER BY date) AS episode_start
    FROM v_yield_curve
),
episode_ids AS (
    SELECT date, spread_10_2, inverted,
           SUM(CASE WHEN episode_start = 1 THEN 1 ELSE 0 END)
               OVER (ORDER BY date
                    ROWS UNBOUNDED PRECEDING) AS episode_id
    FROM spread
)
SELECT episode_id,
       MIN(date)                        AS start_month,
       MAX(date)                        AS end_month,
       COUNT(*)                         AS months_inverted,
       ROUND(MIN(spread_10_2) * 100, 1) AS trough_bp,
       ROUND(AVG(spread_10_2) * 100, 1) AS avg_spread_bp
FROM   episode_ids
WHERE  inverted = 1
GROUP  BY episode_id
HAVING months_inverted >= 2
ORDER  BY trough_bp ASC;

-- 3c. Full dashboard: spread + real rate + Taylor gap on one timeline
SELECT v.date,
       ROUND(v.spread_10_2, 3)   AS spread_10_2,
       ROUND(v.ma12_spread, 3)   AS ma12_spread,
       v.inverted,
       ROUND(f.real_rate, 2)     AS real_rate,
       ROUND(f.taylor_gap, 2)    AS taylor_gap
FROM   v_yield_curve v
JOIN   fred_rates    f ON f.date = v.date
WHERE  v.date >= '2000-01-01'
ORDER  BY v.date;


-- ----------------------------------------------------------------
-- SECTION 4: Credit spreads — IG, HY, and the tightening paradox
--
-- The anomaly: IG and HY spreads TIGHTENED in 2023 even as
-- the Fed delivered the fastest rate hikes in 40 years.
-- ----------------------------------------------------------------

-- Credit spread history with 12-month moving average
SELECT date,
       ROUND(fed_funds, 2)  AS policy_rate,
       ROUND(ig_spread, 0)  AS ig_spread_bp,
       ROUND(hy_spread, 0)  AS hy_spread_bp,
       ROUND(
           AVG(hy_spread)
           OVER (ORDER BY date
                 ROWS BETWEEN 11 PRECEDING AND CURRENT ROW)
       , 0)                 AS ma12_hy_spread,
       ROUND(
           hy_spread - LAG(hy_spread, 12) OVER (ORDER BY date)
       , 0)                 AS hy_spread_yoy_change
FROM   fred_rates
WHERE  date >= '2000-01-01'
  AND  hy_spread IS NOT NULL
ORDER  BY date;

-- Peak HY spread months (risk-off episodes)
-- Compare GFC (2008-09), COVID (2020), and tightening cycle (2022-23)
SELECT date,
       ROUND(hy_spread, 0)   AS hy_spread_bp,
       ROUND(ig_spread, 0)   AS ig_spread_bp,
       ROUND(fed_funds, 2)   AS policy_rate,
       ROUND(real_rate, 2)   AS real_rate
FROM   fred_rates
WHERE  hy_spread IS NOT NULL
ORDER  BY hy_spread DESC
LIMIT  25;

-- ----------------------------------------------------------------
-- SECTION 5: Mortgage market — where tightening actually bit
-- ----------------------------------------------------------------

-- Mortgage rate vs 10-year Treasury: the spread tells you the story
SELECT date,
       ROUND(rate_10y, 2)        AS treasury_10y,
       ROUND(mortgage_30y, 2)    AS mortgage_30y,
       ROUND(mortgage_spread, 2) AS mortgage_spread_pp,
       ROUND(
           AVG(mortgage_spread)
           OVER (ORDER BY date
                 ROWS BETWEEN 11 PRECEDING AND CURRENT ROW)
       , 2)                      AS ma12_mortgage_spread
FROM   fred_rates
WHERE  mortgage_30y IS NOT NULL
  AND  date >= '2000-01-01'
ORDER  BY date;

-- Peak mortgage rate months
-- October 2023: 7.79% — highest since November 2000
SELECT date,
       ROUND(mortgage_30y, 2)    AS mortgage_rate,
       ROUND(rate_10y, 2)        AS treasury_10y,
       ROUND(mortgage_spread, 2) AS spread_pp
FROM   fred_rates
WHERE  mortgage_30y IS NOT NULL
ORDER  BY mortgage_30y DESC
LIMIT  20;

-- ----------------------------------------------------------------
-- SECTION 6: M2 money supply — the quantity theory test
--
-- MV = PY  =>  ΔM + ΔV = ΔP + ΔY
-- M2 grew 26% in 2020-21. Did it predict the inflation surge?
-- M2 FELL year-on-year in 2023 — first time since early 20th century.
-- ----------------------------------------------------------------

SELECT date,
       ROUND(m2 / 1000, 1)   AS m2_trillions,
       ROUND(m2_yoy, 2)       AS m2_yoy_pct,
       ROUND(cpi_yoy, 2)      AS cpi_yoy_pct,
       ROUND(real_rate, 2)    AS real_rate
FROM   fred_rates
WHERE  date >= '2015-01-01'
  AND  m2_yoy IS NOT NULL
ORDER  BY date;

-- M2 annual growth vs CPI: the monetarist relationship
-- Friedman: inflation is "always and everywhere a monetary phenomenon"
WITH money AS (
    SELECT date, m2_yoy, cpi_yoy,
           LAG(m2_yoy, 18)
               OVER (ORDER BY date)  AS m2_yoy_18m_lag
    FROM fred_rates
    WHERE m2_yoy IS NOT NULL AND cpi_yoy IS NOT NULL
)
SELECT date,
       ROUND(m2_yoy, 2)          AS m2_growth,
       ROUND(m2_yoy_18m_lag, 2)  AS m2_growth_18m_ago,
       ROUND(cpi_yoy, 2)         AS cpi_now
FROM   money
WHERE  m2_yoy_18m_lag IS NOT NULL
  AND  date >= '2000-01-01'
ORDER  BY date;
