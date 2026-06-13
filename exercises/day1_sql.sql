-- ================================================================
-- exercises/day1_sql.sql
-- Day 1 Exercise Set -- SQL for Economic Analysis
--
-- HOW TO USE THIS FILE
-- Run each exercise in VS Code SQLite Viewer.
-- Attempt the task BEFORE reading the scaffold.
-- The scaffold shows you the STRUCTURE -- you fill in the ???.
-- Model answers are at the bottom of each exercise.
-- Mark an exercise DONE when you can explain EVERY line.
-- ================================================================


-- ================================================================
-- EXERCISE 1 (Block 1) -- "The G20 Divergence"
-- Difficulty: EASY | Time: 10 min
-- ================================================================
--
-- CONTEXT:
--   The 2022 inflation surge hit G20 economies very differently.
--   Argentina had triple-digit inflation (domestic crisis).
--   Japan had 2-3% inflation (very different monetary regime).
--   Understanding WHY they diverged is a key analytical question.
--
-- TASK:
--   For G20 countries only, compute:
--     - Average inflation in 2021, 2022, and 2023 (three separate columns)
--     - The peak year (which year had the highest inflation?)
--     - A severity label based on 2022 inflation
--   Sort by 2022 inflation descending.
--
-- EXPECTED COLUMNS:
--   country_code | country_name | region | avg_21 | avg_22 | avg_23 | tier_22
--
-- SCAFFOLD (fill in the ???):

SELECT i.country_code,
       c.country_name,
       c.region,
       ROUND(AVG(CASE WHEN i.year = 2021 THEN i.inflation END), 2) AS avg_21,
       ROUND(AVG(CASE WHEN i.year = 2022 THEN i.inflation END), 2) AS avg_22,
       ROUND(AVG(CASE WHEN i.year = 2023 THEN i.inflation END), 2) AS avg_23,
       CASE
           WHEN AVG(CASE WHEN i.year = 2022 THEN i.inflation END) >= 8  THEN 'Severe'
           WHEN AVG(CASE WHEN i.year = 2022 THEN i.inflation END) >= 5  THEN 'High'
           WHEN AVG(CASE WHEN i.year = 2022 THEN i.inflation END) >= 3  THEN 'Elevated'
           ELSE 'Moderate'
       END AS tier_22
FROM   indicators  i
JOIN   countries   c ON c.country_code = i.country_code
WHERE  c.g20 = 1                        -- G20 only
  AND  i.year IN (2021, 2022, 2023)
  AND  i.inflation IS NOT NULL
GROUP  BY i.country_code, c.country_name, c.region
ORDER  BY avg_22 DESC;

-- DISCUSSION QUESTIONS:
-- (1) Which G20 economy had the highest 2022 inflation? Is this
--     consistent with a "common global shock" explanation?
-- (2) Japan is at the bottom. What does this tell you about the
--     role of demand vs supply in the inflation surge?
-- (3) Germany vs France: both in the eurozone, same monetary policy.
--     Did they have different inflation outcomes? Why might that be?


-- ================================================================
-- EXERCISE 2 (Block 1) -- "The Fiscal Stimulus Test"
-- Difficulty: MEDIUM | Time: 20 min
-- ================================================================
--
-- CONTEXT:
--   The US passed ~$5 trillion in fiscal stimulus in 2020-21.
--   The EU was more restrained. Economists debate whether this
--   explains why US inflation peaked higher than EU inflation.
--
-- TASK:
--   Compare average 2020-21 fiscal balance (proxy for stimulus size)
--   to 2022 inflation across all countries.
--   Classify countries as:
--     - "Large deficit" (avg fiscal_balance < -5% of GDP)
--     - "Moderate deficit" (< -2%)
--     - "Near balanced or surplus" (>= -2%)
--   Compute average 2022 inflation within each group.
--   Does more fiscal stimulus predict higher inflation?
--
-- SCAFFOLD:

WITH fiscal_class AS (
    SELECT country_code,
           AVG(fiscal_balance) AS avg_fiscal_2020_21,
           CASE
               WHEN AVG(fiscal_balance) < -5  THEN 'Large deficit (<-5%)'
               WHEN AVG(fiscal_balance) < -2  THEN 'Moderate deficit (-2 to -5%)'
               ELSE                                'Near balanced (>=-2%)'
           END AS fiscal_group
    FROM   indicators
    WHERE  year IN (2020, 2021)
      AND  fiscal_balance IS NOT NULL
    GROUP  BY country_code
),
inflation_2022 AS (
    SELECT country_code,
           inflation AS cpi_2022
    FROM   indicators
    WHERE  year = 2022
      AND  inflation IS NOT NULL
)
SELECT f.fiscal_group,
       ROUND(AVG(i.cpi_2022), 2)           AS avg_inflation_2022,
       ROUND(MIN(i.cpi_2022), 2)           AS min_inflation,
       ROUND(MAX(i.cpi_2022), 2)           AS max_inflation,
       COUNT(*)                             AS n_countries
FROM   fiscal_class f
JOIN   inflation_2022 i ON i.country_code = f.country_code
GROUP  BY f.fiscal_group
ORDER  BY avg_inflation_2022 DESC;

-- DISCUSSION QUESTIONS:
-- (1) Do countries with larger deficits have higher 2022 inflation?
-- (2) If the result is ambiguous (small difference), what does that
--     suggest about the cause of inflation?
-- (3) What is the major confound in this analysis?
--     (Hint: Ukraine/energy shock hit all countries simultaneously.)


-- ================================================================
-- EXERCISE 3 (Block 2) -- "Dollar Dominance: Who Paid the Price?"
-- Difficulty: MEDIUM | Time: 25 min
-- ================================================================
--
-- CONTEXT:
--   When the Fed tightened, the US dollar strengthened ~15% in 2022.
--   Countries with large current account deficits import more than
--   they export, so they need foreign currency (often dollars) to
--   pay for imports. A stronger dollar made this more expensive.
--   Additionally, many EM governments borrow in USD -- their debt
--   burden (in domestic currency) rose as the dollar appreciated.
--
-- TASK:
--   Build a vulnerability index for each country based on:
--     - 2022 inflation (proxy for import price shock transmission)
--     - Worst current account balance in 2020-2022 (structural exposure)
--     - GDP per capita in 2022 (ability to absorb the shock)
--   Rank the 10 most vulnerable countries and show their income group.
--
-- SCAFFOLD:

WITH vulnerability AS (
    SELECT i.country_code,
           c.country_name,
           c.income_group,
           c.region,
           MAX(CASE WHEN i.year = 2022 THEN i.inflation END)
               AS inflation_2022,
           MIN(CASE WHEN i.year BETWEEN 2020 AND 2022 THEN i.current_account END)
               AS worst_ca_balance,
           AVG(CASE WHEN i.year = 2022 THEN i.gdp_per_capita END)
               AS gdp_per_cap_2022
    FROM   indicators  i
    JOIN   countries   c ON c.country_code = i.country_code
    GROUP  BY i.country_code, c.country_name, c.income_group, c.region
)
SELECT country_code,
       country_name,
       income_group,
       region,
       ROUND(inflation_2022, 1)     AS inflation_2022,
       ROUND(worst_ca_balance, 1)   AS worst_ca_pct_gdp,
       ROUND(gdp_per_cap_2022, 0)   AS gdp_per_cap,
       -- Vulnerability score: higher is more exposed
       -- Weights: 40% inflation impact, 30% CA deficit, 30% low income
       ROUND(
           COALESCE(inflation_2022, 0) * 0.40
           + COALESCE(-worst_ca_balance, 0) * 0.30
           + COALESCE(100000.0 / NULLIF(gdp_per_cap_2022, 0), 0) * 0.30
       , 1) AS vulnerability_score
FROM   vulnerability
WHERE  inflation_2022 IS NOT NULL
ORDER  BY vulnerability_score DESC
LIMIT  15;

-- DISCUSSION QUESTIONS:
-- (1) Which income group dominates the top of the vulnerability ranking?
-- (2) Can you find any high-income country in the top 10? If so, why?
-- (3) Is vulnerability_score the best formula? What would you change?
--     (Try changing the weights: 50% CA deficit, 30% inflation, 20% income)


-- ================================================================
-- EXERCISE 4 (Block 3) -- "The Inversion Timeline"
-- Difficulty: HARD | Time: 30 min
-- ================================================================
--
-- CONTEXT:
--   The 2022-24 US yield curve inversion was the longest and
--   second-deepest since records began (1976).
--   Historical record: 6 of 7 inversions preceded recessions.
--   The 2022-24 inversion has not (yet) been followed by a recession.
--
-- TASK:
--   Build the complete inversion history from fred_rates.
--   For each inversion episode:
--     - Start and end month
--     - Duration (months)
--     - Deepest point (basis points)
--     - Average spread during inversion
--   Add a human-readable label for which recession it preceded (if any).
--
-- SCAFFOLD (5 CTEs -- build each one before moving to the next):

WITH

-- CTE 1: compute spread and inversion flag for each month
spread AS (
    SELECT date,
           ROUND(rate_10y - rate_2y, 3)                   AS spread_pp,
           CASE WHEN rate_10y < rate_2y THEN 1 ELSE 0 END AS inverted
    FROM   fred_rates
    WHERE  rate_10y IS NOT NULL
      AND  rate_2y  IS NOT NULL
),

-- CTE 2: detect where each NEW episode begins
-- (inverted = 1 when previously was 0)
transitions AS (
    SELECT date, spread_pp, inverted,
           -- This is 1 at the START of a new inversion episode, 0 otherwise
           inverted - LAG(inverted, 1, 0) OVER (ORDER BY date) AS episode_start
    FROM spread
),

-- CTE 3: assign an episode_id to each month
-- The running SUM of episode_start increments each time a new episode starts.
-- All months within the same episode get the same episode_id.
episode_ids AS (
    SELECT date, spread_pp, inverted,
           SUM(CASE WHEN episode_start = 1 THEN 1 ELSE 0 END)
               OVER (ORDER BY date ROWS UNBOUNDED PRECEDING) AS episode_id
    FROM transitions
),

-- CTE 4: aggregate each episode into one summary row
episode_summary AS (
    SELECT episode_id,
           MIN(date)                        AS start_month,
           MAX(date)                        AS end_month,
           COUNT(*)                         AS months,
           ROUND(MIN(spread_pp) * 100, 1)   AS trough_bp,
           ROUND(AVG(spread_pp) * 100, 1)   AS avg_bp
    FROM   episode_ids
    WHERE  inverted = 1
    GROUP  BY episode_id
    HAVING months >= 2       -- filter out single-month noise
),

-- CTE 5: add a recession label (hardcoded from NBER dates)
-- This demonstrates how to JOIN to a manually specified dataset.
recession_labels AS (
    SELECT 1 AS approx_episode, 'Led to 1980 recession' AS label
    UNION ALL SELECT 2, 'Led to 1981-82 recession'
    UNION ALL SELECT 3, 'Led to 1990-91 recession'
    UNION ALL SELECT 4, '1998 false signal (no recession)'
    UNION ALL SELECT 5, 'Led to 2001 recession'
    UNION ALL SELECT 6, 'Led to 2007-09 GFC'
    UNION ALL SELECT 7, 'No recession yet (2022-24)'
)

SELECT e.*,
       r.label AS recession_context
FROM   episode_summary e
LEFT   JOIN recession_labels r
         ON r.approx_episode = e.episode_id
ORDER  BY e.trough_bp ASC;

-- DISCUSSION QUESTIONS:
-- (1) How does the 2022-24 episode compare to the GFC inversion (2005-07)?
-- (2) The 1998 episode was a "false positive". The yield curve briefly
--     inverted during the LTCM/Russian debt crisis but no recession
--     followed. Does the 2022-24 episode look more like 1998 or 2005?
-- (3) If the median lead time to recession is 14 months, and the
--     inversion started in July 2022, when would you expect a recession?
--     What does the fact that none arrived tell you?


-- ================================================================
-- SELF-CHECK: Can you explain these things to someone else?
-- ================================================================
-- After completing the exercises, can you explain:
--
--   BLOCK 1:
--   [ ] Why WHERE AVG(inflation) > 5 is an error, but HAVING is correct
--   [ ] What GROUP BY actually does to the rows (collapses them)
--   [ ] What CASE WHEN evaluates first (the TOPMOST matching condition)
--
--   BLOCK 2:
--   [ ] The difference between INNER JOIN and LEFT JOIN (what rows appear)
--   [ ] How a CTE is different from a subquery (readability, reusability)
--   [ ] Why we use CTEs for multi-step analyses
--
--   BLOCK 3:
--   [ ] What ROWS BETWEEN 3 PRECEDING AND CURRENT ROW does to the window
--   [ ] Why PARTITION BY country_code matters in a LAG() call
--   [ ] What inverted - LAG(inverted, 1, 0) computes (episode detection)
--   [ ] What ROWS UNBOUNDED PRECEDING does in SUM() (running total)
