-- 📖 New here? A plain-English (Feynman-style) explanation of every
-- concept below — the economics, the SQL, the why — is in
-- docs/concepts_explained.md. Read it alongside this file.
-- ----------------------------------------------------------------
-- ================================================================
-- 02_core_sql.sql  |  BLOCK 1  |  Core SQL for Economic Analysis
-- Central question: "What kind of inflation was the 2021-22 surge?"
-- ================================================================
--
-- LEARNING OBJECTIVES
-- By the end of this file you will be able to:
--   1. Filter rows with WHERE (single and multi-condition)
--   2. Aggregate with GROUP BY, and understand what it actually does
--   3. Filter on aggregates with HAVING (and know why WHERE fails here)
--   4. Classify data with CASE WHEN
--   5. Interpret the output economically, not just technically
--
-- HOW TO USE THIS FILE
--   Run each section one at a time in VS Code SQLite Viewer.
--   Read the comment ABOVE each query before running it.
--   Read the >>> NOTICE comment to understand what the output means.
--   Do NOT copy-paste. Typing forces you to read every character.
--
-- ECONOMIC CONTEXT
--   US CPI hit 9.1% in June 2022 -- a 40-year high.
--   UK peaked at 11.1% (October 2022). Eurozone at 10.6%.
--   But was this caused by:
--     (A) Too much demand -- fiscal stimulus driving spending above capacity?
--         If A: raising rates is the right tool (cool demand down).
--     (B) Supply-side shocks -- COVID supply chains, Ukraine/energy?
--         If B: raising rates cannot fix a supply chain.
--              It only reduces demand enough to meet constrained supply
--              -- at the cost of higher unemployment.
--   The data gives you evidence. We will query it.
-- ================================================================


-- ================================================================
-- PART 0: Always look before you query
-- ================================================================

-- What tables exist?
SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name;

-- What columns does indicators have?
PRAGMA table_info(indicators);

-- First 10 rows -- get a feel for the data
SELECT * FROM indicators LIMIT 10;

-- >>> NOTICE:
-- >>> Each row = one country x one year (this is a "panel dataset").
-- >>> country_code is the ISO 3-letter code: USA, GBR, DEU...
-- >>> NULL values appear where countries did not report that series.
-- >>> NULL is not zero. It means "we do not know". This matters when
-- >>> you compute averages -- AVG() ignores NULLs automatically.


-- ================================================================
-- PART 1: WHERE -- ask a precise question
-- ================================================================

-- The simplest useful query: one country, all years
SELECT * FROM indicators WHERE country_code = 'USA';

-- >>> NOTICE: Scroll to 2022. That is where the story starts.
-- >>> Now change 'USA' to 'JPN' (Japan). Notice anything?
-- >>> Japan's inflation stayed well below 3% through 2022-23.
-- >>> That is a puzzle we will return to later.

-- ----------------------------------------------------------------
-- 1a. Filter by year + sort
-- Which economies had inflation above 8% in 2022?
-- These are the countries where central banks HAD to act aggressively.
-- ----------------------------------------------------------------
SELECT country_code,
       ROUND(inflation, 1) AS inflation_pct
FROM   indicators
WHERE  year = 2022
  AND  inflation > 8          -- multi-condition: both must be true
ORDER  BY inflation_pct DESC;

-- >>> NOTICE: Is the list mostly rich or poor countries?
-- >>> Very high inflation was concentrated in countries with
-- >>> high commodity-import dependence and weaker fiscal buffers --
-- >>> not only the US and UK. First hint about cause.

-- ----------------------------------------------------------------
-- 1b. The IN operator -- filter by a list
-- G7 inflation across the full tightening era
-- ----------------------------------------------------------------
SELECT country_code,
       year,
       ROUND(inflation, 2) AS cpi_pct
FROM   indicators
WHERE  country_code IN ('USA', 'GBR', 'DEU', 'FRA',
                        'JPN', 'ITA', 'CAN')
  AND  year BETWEEN 2021 AND 2023
ORDER  BY country_code, year;

-- >>> NOTICE: Germany hit 8.7% in 2022. Japan stayed under 3%.
-- >>> Same global supply shock -- very different inflation outcomes.
-- >>> This heterogeneity is the central empirical puzzle.

-- ----------------------------------------------------------------
-- 1c. IS NULL vs IS NOT NULL -- handling missing data
-- Never use = NULL. Always use IS NULL.
-- ----------------------------------------------------------------

-- How many countries are missing fiscal_balance for 2022?
SELECT COUNT(*) AS missing_fiscal_2022
FROM   indicators
WHERE  year = 2022
  AND  fiscal_balance IS NULL;

-- Only countries with complete data (non-NULL inflation and GDP)
SELECT country_code, year,
       ROUND(gdp_per_capita, 0) AS gdp,
       ROUND(inflation, 2)       AS cpi
FROM   indicators
WHERE  year = 2022
  AND  inflation IS NOT NULL
  AND  gdp_per_capita IS NOT NULL
ORDER  BY gdp DESC;

-- >>> NOTICE: IS NULL and IS NOT NULL are your data-quality checks.
-- >>> Running these before any analysis tells you where you have gaps.


-- ================================================================
-- PART 2: GROUP BY -- collapse rows into summary statistics
-- ================================================================

-- CONCEPT: What GROUP BY actually does
-- Without GROUP BY:   AVG(inflation) gives ONE number for all rows.
-- With GROUP BY year: it gives one number PER YEAR.
-- Think of it as: "fold all rows with the same year into one row,
-- then compute the average within each fold."

-- 2a. World average inflation by year -- the macro view
SELECT year,
       ROUND(AVG(inflation), 2) AS avg_world_inflation,
       COUNT(*)                  AS n_countries_reporting
FROM   indicators
WHERE  inflation IS NOT NULL
GROUP  BY year
ORDER  BY year;

-- >>> NOTICE:
-- >>> (1) The surge from 2021 to 2022 -- how many pp?
-- >>> (2) The count column: fewer countries report in recent years
-- >>>     because statistical agencies have publication lags.
-- >>> (3) The retreat in 2023 -- disinflation happened faster than
-- >>>     most forecasters predicted.

-- 2b. Range of inflation -- measuring dispersion
-- The average can hide enormous differences. The range reveals them.
SELECT year,
       ROUND(AVG(inflation), 2)                AS avg,
       ROUND(MIN(inflation), 2)                AS minimum,
       ROUND(MAX(inflation), 2)                AS maximum,
       ROUND(MAX(inflation) - MIN(inflation), 2) AS range_pp
FROM   indicators
WHERE  inflation IS NOT NULL
  AND  year BETWEEN 2019 AND 2023
GROUP  BY year
ORDER  BY year;

-- >>> NOTICE: The range in 2022 is enormous -- probably 50+ pp.
-- >>> Some countries had near-zero inflation; others had hyperinflation.
-- >>> A "global inflation crisis" was not a uniform global phenomenon.
-- >>> This is your first evidence AGAINST a pure demand-pull story.

-- 2c. GROUP BY multiple columns -- cross-tabs
-- Average GDP per capita by region AND income group in 2022.
-- You get one row per COMBINATION.
SELECT c.region,
       c.income_group,
       ROUND(AVG(i.gdp_per_capita), 0) AS avg_gdp,
       COUNT(*)                         AS n_countries
FROM   indicators i
JOIN   countries  c ON c.country_code = i.country_code
WHERE  i.year = 2022
  AND  i.gdp_per_capita IS NOT NULL
GROUP  BY c.region, c.income_group
ORDER  BY avg_gdp DESC;

-- >>> NOTICE: This is your first JOIN in Block 1 -- you need it here
-- >>> because income_group lives in countries, not indicators.
-- >>> The JOIN "attaches" the dimension data to the fact data.
-- >>> We will cover JOINs in depth in Block 2.


-- ================================================================
-- PART 3: HAVING -- filter on aggregated values
-- ================================================================

-- THE MOST COMMON SQL MISTAKE:
--   SELECT year, AVG(inflation)
--   FROM   indicators
--   WHERE  AVG(inflation) > 5    -- ERROR! WHERE runs BEFORE GROUP BY.
--   GROUP  BY year               -- AVG does not exist yet at WHERE time.
--
-- FIX: Use HAVING. HAVING runs AFTER GROUP BY.
--
-- Rule of thumb:
--   WHERE  filters individual rows (before aggregation)
--   HAVING filters groups        (after aggregation)

-- 3a. Years where world average inflation exceeded 5%
SELECT year,
       ROUND(AVG(inflation), 2) AS avg_world_inflation
FROM   indicators
WHERE  inflation IS NOT NULL     -- row-level filter: OK with WHERE
GROUP  BY year
HAVING avg_world_inflation > 5   -- group-level filter: must use HAVING
ORDER  BY avg_world_inflation DESC;

-- >>> NOTICE: Only a handful of years pass the 5% threshold.
-- >>> This quantifies the historical rarity of the 2022 episode.

-- 3b. Income groups with average 2022 inflation above 6%
-- Combining JOIN + GROUP BY + HAVING in one query.
SELECT c.income_group,
       ROUND(AVG(i.inflation), 2) AS avg_inflation,
       COUNT(*)                    AS n_countries
FROM   indicators i
JOIN   countries  c ON c.country_code = i.country_code
WHERE  i.year = 2022
  AND  i.inflation IS NOT NULL
GROUP  BY c.income_group
HAVING avg_inflation > 6
ORDER  BY avg_inflation DESC;

-- >>> NOTICE: If lower-income groups top this list, it suggests
-- >>> commodity import shocks hit them hardest (food and energy
-- >>> make up a larger share of their consumption basket).
-- >>> That would support the supply-shock narrative.


-- ================================================================
-- PART 4: CASE WHEN -- add classification logic
-- ================================================================

-- CASE WHEN is SQL's if-else. It labels rows based on conditions.
-- The result is a new column -- it does not change the underlying data.
--
-- Syntax:
--   CASE
--       WHEN condition THEN value
--       WHEN condition THEN value
--       ELSE           default_value
--   END AS column_name

-- 4a. Classify 2022 inflation by severity
SELECT i.country_code,
       c.country_name,
       ROUND(i.inflation, 1) AS cpi_2022,
       CASE
           WHEN i.inflation >= 10 THEN 'Severe    (>=10%)'
           WHEN i.inflation >=  6 THEN 'High      (6-10%)'
           WHEN i.inflation >=  3 THEN 'Elevated  (3-6%)'
           WHEN i.inflation >=  0 THEN 'Moderate  (0-3%)'
           ELSE                        'Deflation (<0%)'
       END                   AS severity
FROM   indicators i
JOIN   countries  c ON c.country_code = i.country_code
WHERE  i.year = 2022
  AND  i.inflation IS NOT NULL
ORDER  BY i.inflation DESC;

-- >>> NOTICE: The CASE evaluates conditions TOP TO BOTTOM and
-- >>> uses the FIRST match. So a country with 12% hits "Severe"
-- >>> immediately -- it never reaches the "High" condition.
-- >>> Order your conditions from most to least restrictive.

-- 4b. Summarise the CASE WHEN output with GROUP BY
-- How many countries in each severity tier in 2022?
SELECT CASE
           WHEN inflation >= 10 THEN 'Severe    (>=10%)'
           WHEN inflation >=  6 THEN 'High      (6-10%)'
           WHEN inflation >=  3 THEN 'Elevated  (3-6%)'
           WHEN inflation >=  0 THEN 'Moderate  (0-3%)'
           ELSE                      'Deflation (<0%)'
       END              AS severity,
       COUNT(*)         AS n_countries,
       ROUND(AVG(inflation), 1) AS avg_within_tier
FROM   indicators
WHERE  year = 2022
  AND  inflation IS NOT NULL
GROUP  BY severity
ORDER  BY avg_within_tier DESC;

-- >>> NOTICE: The distribution across tiers tells you about the
-- >>> global structure. Where does the mass of countries sit?

-- 4c. Binary flag -- 0 or 1 -- useful for counting and averaging
-- Was inflation above the 2% target in each year?
-- (This pattern -- a 0/1 flag -- becomes very powerful with window
-- functions in Block 3.)
SELECT country_code,
       year,
       ROUND(inflation, 2)                            AS cpi,
       CASE WHEN inflation > 2 THEN 1 ELSE 0 END     AS above_target
FROM   indicators
WHERE  country_code IN ('USA', 'GBR', 'DEU', 'JPN')
  AND  year BETWEEN 2010 AND 2023
ORDER  BY country_code, year;

-- >>> NOTICE: SUM(above_target) would give you the count of years
-- >>> above target per country. AVG(above_target) would give you
-- >>> the FRACTION of years above target. Try it.


-- ================================================================
-- PART 5: Full query -- putting it all together
-- ================================================================

-- This is the kind of query that appears in a central bank briefing.
-- G20 economies: average inflation during the tightening era,
-- ranked highest first, with severity classification.
--
-- Read it section by section. Notice:
--   - JOIN to get country metadata
--   - WHERE for row filters
--   - GROUP BY to collapse to one row per country
--   - ROUND for readability
--   - CASE WHEN for the severity label
--   - ORDER BY to present results usefully

SELECT i.country_code,
       c.country_name,
       c.region,
       ROUND(AVG(i.inflation), 2)          AS avg_inflation_2021_23,
       ROUND(MAX(i.inflation), 2)          AS peak_inflation,
       CASE
           WHEN AVG(i.inflation) >= 8  THEN 'Severe'
           WHEN AVG(i.inflation) >= 5  THEN 'High'
           WHEN AVG(i.inflation) >= 3  THEN 'Elevated'
           ELSE                             'Moderate'
       END                                 AS tier
FROM   indicators  i
JOIN   countries   c ON c.country_code = i.country_code
WHERE  i.year BETWEEN 2021 AND 2023
  AND  i.inflation IS NOT NULL
  AND  c.g20 = 1              -- G20 members only (flag column = 1)
GROUP  BY i.country_code, c.country_name, c.region
ORDER  BY avg_inflation_2021_23 DESC;

-- >>> ECONOMIC INTERPRETATION:
-- >>> Look at who is at the top. Argentina and Turkey would suggest
-- >>> domestic fiscal/monetary mismanagement, not a global shock.
-- >>> US, UK, and Germany clustering together suggests a common cause.
-- >>> Japan at the bottom (if it appears) is the crucial counter-example:
-- >>> same global supply shock, very different outcome -- why?
-- >>> (Answer: Japan's wage dynamics, energy import structure, and
-- >>> the BOJ's yield curve control policy were all different.)


-- ================================================================
-- EXERCISE (15 minutes) -- do not look at the answer below first
-- ================================================================
--
-- Economic question to answer with SQL:
-- "Did countries with larger pre-pandemic fiscal deficits
--  (2018-2019 average) end up with higher peak inflation in 2022?"
--
-- If yes: supports demand-pull narrative (more stimulus -> more demand)
-- If no:  supports supply-shock narrative (shared external cause)
--
-- Build your query in steps:
--   Step 1: Get average fiscal_balance per country for 2018-2019
--   Step 2: Get inflation for each country in 2022
--   Step 3: Join them
--   Step 4: Classify countries as "deficit" vs "surplus" (CASE WHEN)
--   Step 5: Compare average 2022 inflation between the two groups
--
-- Hint: use a subquery or nested SELECT for steps 1 and 2.
-- ================================================================

-- ANSWER (only read after attempting):
SELECT
    CASE
        WHEN avg_fiscal < 0  THEN 'Pre-pandemic deficit (ran stimulus)'
        ELSE                      'Pre-pandemic surplus (conservative)'
    END                         AS fiscal_group,
    ROUND(AVG(inflation_2022), 2) AS avg_peak_inflation_2022,
    COUNT(*)                      AS n_countries
FROM (
    SELECT f.country_code,
           f.avg_fiscal,
           i2.inflation AS inflation_2022
    FROM (
        SELECT country_code,
               AVG(fiscal_balance) AS avg_fiscal
        FROM   indicators
        WHERE  year BETWEEN 2018 AND 2019
          AND  fiscal_balance IS NOT NULL
        GROUP  BY country_code
    ) f
    JOIN indicators i2
      ON i2.country_code = f.country_code
     AND i2.year = 2022
    WHERE  i2.inflation IS NOT NULL
)
GROUP  BY fiscal_group
ORDER  BY avg_peak_inflation_2022 DESC;

-- >>> DISCUSS WITH YOUR NEIGHBOUR:
-- >>> (1) What does the result show?
-- >>> (2) Is this a causal analysis or a correlation?
-- >>> (3) What confounders could explain the result even if fiscal
-- >>>     policy had NO effect on inflation?
-- >>>     (Hint: Ukraine war hit both deficit and surplus countries.)
