-- 📖 New here? A plain-English (Feynman-style) explanation of every
-- concept below — the economics, the SQL, the why — is in
-- docs/concepts_explained.md. Read it alongside this file.
-- ----------------------------------------------------------------
-- ================================================================
-- 04_window_functions.sql  |  BLOCK 3  |  Window Functions
-- Central question: "What did the yield curve signal in 2022?"
-- ================================================================
--
-- LEARNING OBJECTIVES
-- By the end of this file you will:
--   1. Understand what a window function is -- and why it is different
--      from GROUP BY
--   2. Use RANK(), ROW_NUMBER(), DENSE_RANK() to rank within groups
--   3. Use LAG() and LEAD() to access adjacent rows (growth rates!)
--   4. Use AVG() OVER (...) for rolling averages
--   5. Chain CTEs with window functions for multi-step pipelines
--   6. Compute the yield curve spread and detect inversion episodes
--
-- THE FUNDAMENTAL DISTINCTION
-- GROUP BY collapses rows. After a GROUP BY, you have fewer rows
-- than you started with -- one per group.
--
-- Window functions do NOT collapse rows. They add a new column
-- computed "across a window" of related rows, while keeping
-- every original row intact.
--
-- Example:
--   GROUP BY country: 40 rows -> 1 row per country
--   RANK() OVER (PARTITION BY country): 40 rows -> still 40 rows,
--   but each row now has a rank number attached.
-- ================================================================


-- ================================================================
-- PART 1: RANK, ROW_NUMBER, DENSE_RANK
-- ================================================================

-- CONCEPT: OVER (PARTITION BY ... ORDER BY ...)
-- PARTITION BY = "do this separately for each group"
-- ORDER BY     = "sort within each group before computing the rank"
--
-- Without PARTITION BY: rank across the ENTIRE table.
-- With PARTITION BY year: rank WITHIN each year independently.

-- 1a. Rank economies by GDP within each year
-- Every country gets a rank number relative to its peers that year.
SELECT country_code,
       year,
       ROUND(gdp_per_capita, 0)                           AS gdp,
       RANK()       OVER (PARTITION BY year
                          ORDER BY gdp_per_capita DESC)   AS rank_in_year,
       ROW_NUMBER() OVER (PARTITION BY year
                          ORDER BY gdp_per_capita DESC)   AS rownum
FROM   indicators
WHERE  year IN (2000, 2010, 2022)
  AND  gdp_per_capita IS NOT NULL
ORDER  BY year, rank_in_year
LIMIT  30;

-- >>> NOTICE the difference between RANK and ROW_NUMBER:
-- >>> If two countries have the same GDP:
-- >>>   RANK gives them both rank 3, then skips to rank 5 (1,1,3,3,5)
-- >>>   ROW_NUMBER always gives unique numbers (1,2,3,4,5)
-- >>>   DENSE_RANK gives them both 3, but the next is 4 -- no skip (1,1,2,3)
-- >>> For economics: RANK is most natural (tied countries share a rank).

-- 1b. Which G20 country had the highest inflation RANK in each year?
-- Ranking within the G20 group -- not globally
SELECT i.country_code,
       i.year,
       ROUND(i.inflation, 2)                              AS cpi,
       RANK()  OVER (PARTITION BY i.year
                     ORDER BY i.inflation DESC)           AS g20_rank
FROM   indicators i
JOIN   countries  c ON c.country_code = i.country_code
WHERE  c.g20 = 1
  AND  i.inflation IS NOT NULL
  AND  i.year BETWEEN 2020 AND 2023
ORDER  BY i.year, g20_rank;

-- >>> NOTICE: Does the G20 country with rank 1 in 2022 change
-- >>> dramatically vs 2020? That is the inflation surge in one number.


-- ================================================================
-- PART 2: LAG and LEAD -- access rows before and after
-- ================================================================

-- CONCEPT: LAG and LEAD
-- LAG(column, n)  gives you the value of column from n rows EARLIER
-- LEAD(column, n) gives you the value of column from n rows LATER
-- Both respect PARTITION BY and ORDER BY.
--
-- The economic use case: compute growth rates WITHOUT Python.
-- growth_t = (value_t - value_{t-1}) / value_{t-1} * 100
-- In SQL:  LAG(value, 1) gives value_{t-1}.

-- 2a. Year-on-year GDP growth computed entirely in SQL
-- LAG gets the previous year's GDP for the SAME country.
-- PARTITION BY country_code ensures we don't compare across countries.
WITH growth AS (
    SELECT country_code,
           year,
           gdp_per_capita,
           LAG(gdp_per_capita, 1)
               OVER (PARTITION BY country_code
                     ORDER BY year)    AS gdp_prev_year
    FROM indicators
    WHERE gdp_per_capita IS NOT NULL
)
SELECT country_code,
       year,
       ROUND(gdp_per_capita, 0)                                AS gdp,
       ROUND(gdp_prev_year, 0)                                 AS gdp_prev,
       ROUND((gdp_per_capita - gdp_prev_year)
             / gdp_prev_year * 100, 2)                         AS yoy_pct
FROM   growth
WHERE  gdp_prev_year IS NOT NULL   -- first year per country has no lag
  AND  year BETWEEN 2019 AND 2023
  AND  country_code IN ('USA', 'GBR', 'DEU', 'CHN', 'JPN')
ORDER  BY country_code, year;

-- >>> NOTICE:
-- >>> (1) 2020 shows the COVID crash for every country.
-- >>> (2) 2021 shows the rebound -- magnitude differs by country.
-- >>> (3) The difference in 2021 rebound SIZE between US and EU
-- >>>     is one reason US inflation peaked higher.
-- >>> The US rebounded faster (more fiscal stimulus) -> more demand.

-- 2b. LAG with n=12 -- year-on-year on MONTHLY data
-- For the FRED monthly data: LAG(x, 12) = same month last year.
-- This is how CPI inflation is calculated from a price index.
SELECT date,
       ROUND(cpi_index, 2)                              AS cpi_index,
       LAG(cpi_index, 12) OVER (ORDER BY date)          AS cpi_12m_ago,
       ROUND(
           (cpi_index - LAG(cpi_index, 12) OVER (ORDER BY date))
           / LAG(cpi_index, 12) OVER (ORDER BY date) * 100
       , 2)                                              AS cpi_yoy_computed,
       ROUND(cpi_yoy, 2)                                AS cpi_yoy_stored
FROM   fred_rates
WHERE  date >= '2020-01-01'
  AND  cpi_index IS NOT NULL
ORDER  BY date;

-- >>> NOTICE: cpi_yoy_computed and cpi_yoy_stored should be identical.
-- >>> We stored the derived column in fetch_fred.py so you don't have
-- >>> to recompute it every time -- but this shows you it is NOT magic.
-- >>> It is just one LAG call and a division.

-- 2c. LEAD -- look forward
-- What was unemployment 4 quarters later?
-- Useful for: how quickly did labour markets respond to tightening?
SELECT country_code,
       quarter,
       ROUND(unemployment_rate, 2)              AS rate_now,
       ROUND(
           LEAD(unemployment_rate, 4)
           OVER (PARTITION BY country_code
                 ORDER BY quarter)
       , 2)                                     AS rate_4q_later,
       ROUND(
           LEAD(unemployment_rate, 4)
           OVER (PARTITION BY country_code
                 ORDER BY quarter)
           - unemployment_rate
       , 2)                                     AS change_in_4q
FROM   oecd_unemployment
WHERE  country_code IN ('USA', 'GBR', 'DEU')
ORDER  BY country_code, quarter;

-- >>> NOTICE: Positive values in change_in_4q means unemployment ROSE.
-- >>> You can see the COVID shock (2020 Q1 -> 2020 Q3: large positive),
-- >>> the recovery, and then whether the tightening cycle caused a rise.


-- ================================================================
-- PART 3: Moving averages -- smooth out the noise
-- ================================================================

-- CONCEPT: ROWS BETWEEN n PRECEDING AND CURRENT ROW
-- This defines the "window frame" -- which rows are included in
-- the window function calculation for each row.
--
-- ROWS BETWEEN 3 PRECEDING AND CURRENT ROW:
--   Include the current row and the 3 rows before it.
--   For quarterly data: current quarter + 3 prior = 4 quarters = 1 year.
--   This is a 4-quarter moving average.
--
-- ROWS UNBOUNDED PRECEDING AND CURRENT ROW:
--   All rows from the beginning of the partition up to current.
--   Used for running totals and cumulative sums.

-- 3a. 4-quarter moving average unemployment (OECD quarterly)
SELECT country_code,
       quarter,
       ROUND(unemployment_rate, 2)                             AS rate,
       ROUND(
           AVG(unemployment_rate)
           OVER (PARTITION BY country_code
                 ORDER BY quarter
                 ROWS BETWEEN 3 PRECEDING AND CURRENT ROW)
       , 2)                                                    AS ma4,
       -- Deviation from moving average shows cyclical position
       ROUND(unemployment_rate
             - AVG(unemployment_rate)
               OVER (PARTITION BY country_code
                     ORDER BY quarter
                     ROWS BETWEEN 3 PRECEDING AND CURRENT ROW)
       , 2)                                                    AS deviation_from_ma4
FROM   oecd_unemployment
WHERE  country_code IN ('USA', 'GBR', 'DEU')
ORDER  BY country_code, quarter;

-- >>> NOTICE: The moving average smooths out the erratic quarter-to-quarter
-- >>> variation. The deviation column shows you the cyclical component --
-- >>> positive = above recent trend, negative = below.
-- >>> Large positive deviations in 2020 = COVID shock.
-- >>> Large negative deviations in 2021-22 = tight labour market.

-- 3b. Running cumulative count of months with above-mean unemployment
WITH stats AS (
    SELECT country_code,
           quarter,
           unemployment_rate,
           AVG(unemployment_rate)
               OVER (PARTITION BY country_code)         AS country_mean,
           CASE WHEN unemployment_rate >
                     AVG(unemployment_rate)
                     OVER (PARTITION BY country_code)
                THEN 1 ELSE 0 END                       AS above_mean
    FROM oecd_unemployment
),
cumulative AS (
    SELECT *,
           SUM(above_mean)
               OVER (PARTITION BY country_code
                     ORDER BY quarter
                     ROWS UNBOUNDED PRECEDING)          AS cumulative_above_mean_quarters
    FROM stats
)
SELECT country_code, quarter, unemployment_rate,
       ROUND(country_mean, 2), above_mean,
       cumulative_above_mean_quarters
FROM   cumulative
WHERE  country_code = 'USA'
ORDER  BY quarter;

-- >>> NOTICE: cumulative_above_mean_quarters counts how many quarters
-- >>> unemployment was ABOVE its long-run mean, up to each point in time.
-- >>> This is a running total -- the ROWS UNBOUNDED PRECEDING makes it
-- >>> accumulate from the very first row.


-- ================================================================
-- PART 4: The yield curve -- financial analysis with window functions
-- ================================================================

-- ECONOMIC CONTEXT:
-- The 10y-2y Treasury spread is the most-watched recession indicator.
-- When it INVERTS (goes negative), the bond market is saying:
--   "We think interest rates are HIGHER RIGHT NOW than they will be
--    in the long run -- because the economy will slow and force cuts."
-- Every US recession since 1955 was preceded by an inversion,
-- with a median lead time of ~14 months.
-- The 2022-23 inversion reached -109 bp -- deepest since 1981.
-- No recession followed (as of 2026). The debate continues.

-- 4a. Basic spread -- what is the 10y-2y differential today?
SELECT date,
       ROUND(rate_10y, 3)                    AS y10,
       ROUND(rate_2y, 3)                     AS y2,
       ROUND(rate_10y - rate_2y, 3)          AS spread_pp,
       CASE WHEN rate_10y < rate_2y
            THEN 'INVERTED'
            ELSE 'Normal'
       END                                   AS curve_shape
FROM   fred_rates
WHERE  date >= '2021-01-01'
  AND  rate_10y IS NOT NULL
  AND  rate_2y  IS NOT NULL
ORDER  BY date;

-- >>> NOTICE: Find the month where curve_shape changes from Normal
-- >>> to INVERTED. That is July 2022 -- the start of the record inversion.

-- 4b. Add a 12-month moving average to smooth noise
-- Analysts use the MA to filter out short-term rate volatility
-- and see the underlying trend.
SELECT date,
       ROUND(rate_10y - rate_2y, 3)                   AS spread_pp,
       CASE WHEN rate_10y < rate_2y THEN 1 ELSE 0 END AS inverted,
       ROUND(
           AVG(rate_10y - rate_2y)
           OVER (ORDER BY date
                 ROWS BETWEEN 11 PRECEDING AND CURRENT ROW)
       , 3)                                            AS ma12_spread
FROM   fred_rates
WHERE  date >= '2000-01-01'
  AND  rate_10y IS NOT NULL
  AND  rate_2y  IS NOT NULL
ORDER  BY date;

-- >>> NOTICE: The MA12 column is smoother. When the MA also turns negative,
-- >>> the inversion is "confirmed" as persistent, not just a blip.
-- >>> The 2022-23 MA12 turned deeply negative -- a very clear signal.

-- 4c. Detect inversion EPISODES -- when did each one start and end?
-- This is a multi-step CTE chain. Read each step top to bottom.
WITH

-- Step 1: compute the spread and inversion flag for each month
spread AS (
    SELECT date,
           ROUND(rate_10y - rate_2y, 3)                   AS spread_pp,
           CASE WHEN rate_10y < rate_2y THEN 1 ELSE 0 END AS inverted
    FROM fred_rates
    WHERE rate_10y IS NOT NULL AND rate_2y IS NOT NULL
),

-- Step 2: detect when a NEW inversion episode begins
-- LAG(inverted) gives last month's flag. If last=0 and now=1, a new
-- episode is starting. inverted - LAG(...) = 1 - 0 = 1 at the start.
marked AS (
    SELECT date, spread_pp, inverted,
           inverted - LAG(inverted, 1, 0) OVER (ORDER BY date) AS episode_start
    FROM spread
),

-- Step 3: assign each month to an episode_id using a running sum
-- SUM of episode_start counts how many episodes have started SO FAR.
-- Every month within the same episode gets the same episode_id.
episode_ids AS (
    SELECT date, spread_pp, inverted,
           SUM(CASE WHEN episode_start = 1 THEN 1 ELSE 0 END)
               OVER (ORDER BY date ROWS UNBOUNDED PRECEDING) AS episode_id
    FROM marked
)

-- Step 4: aggregate each episode into one summary row
SELECT episode_id,
       MIN(date)                        AS start_month,
       MAX(date)                        AS end_month,
       COUNT(*)                         AS months_inverted,
       ROUND(MIN(spread_pp), 3)         AS deepest_pp,
       ROUND(MIN(spread_pp) * 100, 1)   AS deepest_bp,   -- in basis points
       ROUND(AVG(spread_pp) * 100, 1)   AS avg_bp
FROM   episode_ids
WHERE  inverted = 1
GROUP  BY episode_id
HAVING months_inverted >= 2   -- exclude single-month noise
ORDER  BY deepest_pp ASC;     -- most extreme inversion first

-- >>> NOTICE:
-- >>> (1) How many distinct inversion episodes since 1976?
-- >>> (2) Which is the deepest? (Should be 2022-23 at ~-109 bp)
-- >>> (3) Which is the longest? (Should be 2022-24 at ~26 months)
-- >>> (4) Each prior episode preceded a recession. The 2022-24 did not.
-- >>>     This is the most important empirical puzzle in macro right now.


-- ================================================================
-- EXERCISE (20 minutes)
-- ================================================================
--
-- BUILD THE UNEMPLOYMENT FLAG ANALYSIS step by step.
--
-- Task: For each OECD country, find quarters where unemployment was
--       ABOVE the country's full-sample mean AND rising (higher than
--       the previous quarter). Rank countries by how many such quarters
--       they experienced in the 2022-2024 period.
--
-- This identifies countries where the tightening cycle most visibly
-- hit the labour market.
--
-- Steps:
--   CTE 1: compute each country's long-run mean unemployment
--   CTE 2: add LAG(unemployment, 1) to detect quarter-on-quarter change
--   CTE 3: flag quarters that are BOTH above mean AND rising
--   Final: aggregate by country, filter to 2022-2024, rank by flag count
--
-- Worked solution below. The scaffolded version with ??? blanks to fill in
-- is in exercises/day1_sql.sql -- try that first, then check against this.

WITH
means AS (
    SELECT country_code,
           AVG(unemployment_rate) AS country_mean
    FROM   oecd_unemployment
    GROUP  BY country_code
),
with_lag AS (
    SELECT o.country_code,
           o.quarter,
           o.unemployment_rate,
           m.country_mean,
           LAG(o.unemployment_rate, 1)
               OVER (PARTITION BY o.country_code
                     ORDER BY o.quarter)  AS prev_quarter_rate
    FROM   oecd_unemployment o
    JOIN   means m ON m.country_code = o.country_code
),
flagged AS (
    SELECT *,
           CASE WHEN unemployment_rate > country_mean   -- above long-run mean
                 AND unemployment_rate > prev_quarter_rate -- AND rising
                THEN 1 ELSE 0 END AS stress_flag
    FROM   with_lag
    WHERE  prev_quarter_rate IS NOT NULL
)
SELECT country_code,
       SUM(CASE WHEN quarter >= '2022-Q1'
                 AND quarter <= '2024-Q4'
                THEN stress_flag ELSE 0 END) AS stress_quarters_2022_24,
       ROUND(AVG(unemployment_rate), 2)       AS avg_unemployment,
       ROUND(country_mean, 2)                 AS long_run_mean
FROM   flagged
GROUP  BY country_code, country_mean
ORDER  BY stress_quarters_2022_24 DESC;

-- >>> DISCUSS:
-- >>> Which countries show the most labour market stress in 2022-24?
-- >>> Does the ranking match what you would expect based on the
-- >>> aggressiveness of each country's tightening cycle?
-- >>> (UK tightened a lot; Japan tightened very little.)
