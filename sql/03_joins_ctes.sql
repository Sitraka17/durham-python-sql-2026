-- 📖 New here? A plain-English (Feynman-style) explanation of every
-- concept below — the economics, the SQL, the why — is in
-- docs/concepts_explained.md. Read it alongside this file.
-- ----------------------------------------------------------------
-- ================================================================
-- 03_joins_ctes.sql
-- Block 2 — JOINs, Subqueries, Common Table Expressions
--
-- Central question: How did the tightening cycle propagate globally?
--   Did lower-income economies bear a disproportionate burden?
--   Did countries with dollar-denominated debt suffer more?
--
-- ================================================================


-- ----------------------------------------------------------------
-- SECTION 1: JOIN basics — enriching facts with dimensions
-- ----------------------------------------------------------------

-- INNER JOIN: only countries that appear in BOTH tables
-- Attach country name and region to economic indicators
SELECT c.country_name,
       c.region,
       c.income_group,
       i.year,
       ROUND(i.gdp_per_capita, 0) AS gdp_usd,
       ROUND(i.inflation, 2)      AS cpi_pct
FROM   indicators i
INNER  JOIN countries c ON c.country_code = i.country_code
WHERE  i.year = 2022
ORDER  BY i.inflation DESC
LIMIT  20;


-- LEFT JOIN: keep ALL countries from the left table,
-- even if they have no indicator data for 2022.
-- NULL rows reveal data gaps.
SELECT c.country_name,
       c.income_group,
       ROUND(i.gdp_per_capita, 0) AS gdp_2022,
       ROUND(i.inflation, 2)      AS inflation_2022
FROM   countries c
LEFT   JOIN indicators i
    ON c.country_code = i.country_code
   AND i.year = 2022
ORDER  BY i.inflation DESC NULLS LAST;


-- ----------------------------------------------------------------
-- SECTION 2: Multi-table JOIN (3 tables)
-- ----------------------------------------------------------------

-- Compare 2019 (pre-pandemic) vs 2022 (peak tightening) for each country
SELECT c.country_name,
       c.region,
       c.income_group,
       ROUND(pre.gdp_per_capita, 0)            AS gdp_2019,
       ROUND(post.gdp_per_capita, 0)           AS gdp_2022,
       ROUND(post.inflation, 1)                AS inflation_2022,
       ROUND((post.gdp_per_capita
              - pre.gdp_per_capita)
             / pre.gdp_per_capita * 100, 1)   AS gdp_change_pct
FROM   countries c
JOIN   indicators pre  ON pre.country_code  = c.country_code
                       AND pre.year = 2019
JOIN   indicators post ON post.country_code = c.country_code
                       AND post.year = 2022
ORDER  BY inflation_2022 DESC;


-- ----------------------------------------------------------------
-- SECTION 3: Subqueries
-- ----------------------------------------------------------------

-- Countries above world average GDP in 2022
SELECT country_code,
       ROUND(gdp_per_capita, 0) AS gdp
FROM   indicators
WHERE  year = 2022
  AND  gdp_per_capita > (
           SELECT AVG(gdp_per_capita)
           FROM   indicators
           WHERE  year = 2022
             AND  gdp_per_capita IS NOT NULL
       )
ORDER  BY gdp DESC;


-- ----------------------------------------------------------------
-- SECTION 4: Common Table Expressions (CTEs)
-- Same logic as the subquery above — but readable
-- ----------------------------------------------------------------

WITH world_avg AS (
    SELECT AVG(gdp_per_capita) AS avg_gdp
    FROM   indicators
    WHERE  year = 2022
      AND  gdp_per_capita IS NOT NULL
)
SELECT i.country_code,
       ROUND(i.gdp_per_capita, 0)                          AS gdp,
       ROUND(i.gdp_per_capita - w.avg_gdp, 0)             AS above_world_avg
FROM   indicators  i
CROSS  JOIN world_avg w
WHERE  i.year = 2022
  AND  i.gdp_per_capita > w.avg_gdp
ORDER  BY above_world_avg DESC;


-- ----------------------------------------------------------------
-- SECTION 5: Chained CTEs — multi-step analysis
-- ----------------------------------------------------------------

-- Dollar dominance question:
-- Which income groups bore the highest inflation burden in 2022,
-- relative to their pre-pandemic 2018-2019 baseline?

WITH baseline AS (
    -- Step 1: average inflation per country, 2018-2019 (pre-pandemic)
    SELECT country_code,
           AVG(inflation) AS avg_pre
    FROM   indicators
    WHERE  year BETWEEN 2018 AND 2019
      AND  inflation IS NOT NULL
    GROUP  BY country_code
),
peak AS (
    -- Step 2: inflation at peak tightening year (2022)
    SELECT country_code,
           inflation AS inf_2022
    FROM   indicators
    WHERE  year = 2022
      AND  inflation IS NOT NULL
),
excess AS (
    -- Step 3: compute the EXCESS inflation above baseline
    SELECT b.country_code,
           b.avg_pre,
           p.inf_2022,
           ROUND(p.inf_2022 - b.avg_pre, 2) AS excess_inflation
    FROM   baseline b
    JOIN   peak     p ON p.country_code = b.country_code
)
-- Step 4: aggregate by income group to test the dollar-dominance hypothesis
SELECT   c.income_group,
         ROUND(AVG(e.excess_inflation), 2)   AS avg_excess_inflation,
         ROUND(AVG(e.inf_2022), 2)           AS avg_peak_inflation,
         COUNT(*)                             AS n_countries
FROM     excess    e
JOIN     countries c ON c.country_code = e.country_code
GROUP BY c.income_group
ORDER BY avg_excess_inflation DESC;


-- ================================================================
-- EXERCISE: Post-2015 regional improvement analysis
--
-- Question: Which regions improved most in GDP per capita
--           after the 2015 SDG era, relative to the 2000-2014 baseline?
--           Is improvement correlated with income group?
--
-- Template: write three CTEs (pre_2015, post_2015, delta)
--           then aggregate by region.
-- ================================================================

WITH pre AS (
    SELECT country_code,
           AVG(gdp_per_capita) AS avg_pre
    FROM   indicators
    WHERE  year BETWEEN 2000 AND 2014
      AND  gdp_per_capita IS NOT NULL
    GROUP  BY country_code
),
post AS (
    SELECT country_code,
           AVG(gdp_per_capita) AS avg_post
    FROM   indicators
    WHERE  year BETWEEN 2015 AND 2023
      AND  gdp_per_capita IS NOT NULL
    GROUP  BY country_code
),
delta AS (
    SELECT pre.country_code,
           ROUND(post.avg_post - pre.avg_pre, 0)     AS abs_improvement,
           ROUND((post.avg_post - pre.avg_pre)
                 / pre.avg_pre * 100, 1)             AS pct_improvement
    FROM   pre
    JOIN   post ON pre.country_code = post.country_code
)
SELECT   c.region,
         c.income_group,
         ROUND(AVG(d.pct_improvement), 1) AS avg_pct_improvement,
         COUNT(*)                          AS n_countries
FROM     delta     d
JOIN     countries c ON c.country_code = d.country_code
GROUP BY c.region, c.income_group
ORDER BY avg_pct_improvement DESC;
