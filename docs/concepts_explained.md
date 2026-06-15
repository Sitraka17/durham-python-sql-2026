# Every concept, in plain English (the Feynman guide)

> **The Feynman technique:** if you can't explain it simply, you don't
> understand it yet. This guide explains *every* idea in the course as if to a
> smart friend who has never coded — an analogy first, then the precise version,
> then **exactly where you meet it** in the repo. Read the relevant section
> before (or alongside) each block.

**How each entry is laid out:**
> 🧠 **In one line** · 🍎 **Analogy** · ⚙️ **What it really does** · 💻 **Tiny example** · 📂 **Where in the course**

> 💡 **Concepts stick when they have a story.** Pair this guide with
> [finance_anecdotes.md](finance_anecdotes.md) — a real market tale for each idea
> (Volcker, SVB, the 2022 UK gilt crisis, the yield-curve indicator its own
> inventor came to doubt) — and with [why_we_code_this.md](why_we_code_this.md),
> which explains *why* the code is built this way and how each habit pays off in
> a real job.

**Contents**
1. [The thinking — the economics](#1-the-thinking--the-economics)
2. [SQL — asking the database questions](#2-sql--asking-the-database-questions)
3. [Python — wrangling and visualising](#3-python--wrangling-and-visualising)
4. [Machine learning — letting the data find the pattern](#4-machine-learning)
5. [How a whole analysis fits together](#5-how-a-whole-analysis-fits-together)

---

## 1. The thinking — the economics

You can't analyse what you can't picture. Here's the mental model behind the
whole course before a single line of code.

### The Fed's job and the "tightening cycle"
🧠 The central bank moves one interest rate to steer the whole economy.
🍎 Think of the economy as a car and the interest rate as the **brake pedal**.
When inflation (speeding) is too high, the Fed presses the brake (raises rates)
to slow spending. Press too hard and the car stalls (recession); too soft and
it keeps speeding (inflation persists).
⚙️ In 2022–23 the Fed pressed the brake harder than at any time since 1979:
+525 basis points (5.25 percentage points) in 16 months. The course asks: did
the car slow smoothly (a "soft landing") or did something break?
📂 The whole repo. The headline numbers live in `datasets/fred_rates_static.csv`.

### Inflation, and "real" vs "nominal"
🧠 Inflation is how fast prices rise; the *real* interest rate is the rate
*after* subtracting inflation.
🍎 If your savings earn 5% but prices rise 9%, you're getting **poorer** — your
money buys less next year. The "real" rate is −4%, even though the "nominal"
number (5%) looks positive.
⚙️ **Fisher equation:** `real_rate ≈ nominal_rate − inflation`. A negative real
rate means policy is still *loose* even if the headline rate looks high.
💻 `real_rate = fed_funds − cpi_yoy`
📂 `scripts/concepts.py` (demo 1), the `v_real_rates` view, `sql/05_financial_analysis.sql`.

### The Taylor Rule (what *should* the rate be?)
🧠 A simple formula for the "right" interest rate given inflation and the economy.
🍎 Like a thermostat rule: "for every degree above target temperature, turn the
heating down by 1.5 notches." The Taylor rule does that for inflation.
⚙️ `rate = r* + inflation + 0.5(inflation − target) + 0.5(output gap)`. If actual
rates sit far *below* the rule, the Fed is "behind the curve" (too slow).
📂 `scripts/concepts.py` (demo 2), `ml/taylor_rule_regression.py` (we *learn* the
rule from data), the `taylor_gap` column.

### The yield curve (the economy's crystal ball)
🧠 Compare the interest rate on a 10-year loan vs a 2-year loan to the government.
🍎 Normally longer loans pay more (you wait longer for your money, like a longer
fixed-term savings account paying more). When the **short** rate is *higher*
than the long rate — an "inverted" curve — markets are betting rates (and the
economy) will fall. Historically that has preceded most recessions.
⚙️ `spread = rate_10y − rate_2y`. Negative = inverted. In 2022–24 it inverted
deeply and for a record length — yet (so far) no recession. That's the puzzle.
📂 `sql/04_window_functions.sql`, `scripts/pipeline.py`, `ml/recession_prediction.py`.

### Credit spreads (the market's fear gauge)
🧠 The extra interest a risky company pays over the government.
🍎 A shaky borrower pays a higher rate than a rock-solid one — the gap is the
lender's "fear premium." When fear spikes (2008, 2020), spreads blow out.
⚙️ Measured in **basis points** (1bp = 0.01%). "HY" = high-yield (risky), "IG" =
investment-grade (safe). The HY/IG ratio rises in risk-off episodes.
📂 `scripts/concepts.py` (demo 4), `v_credit_dashboard`.

---

## 2. SQL — asking the database questions

SQL is a language for asking a table questions. You describe **what** you want;
the database figures out **how** to get it.
🍎 Big idea: a SQL query is a sentence — `SELECT` (what to show) `FROM` (which
table) `WHERE` (which rows) `GROUP BY` (how to bucket) `ORDER BY` (how to sort).

### SELECT … WHERE
🧠 Pick columns; keep only rows that pass a test.
🍎 A spreadsheet filter: "show me only the rows where year = 2022."
💻 `SELECT country_code, inflation FROM indicators WHERE year = 2022;`
📂 `sql/02_core_sql.sql`.

### GROUP BY + aggregates (and why HAVING ≠ WHERE)
🧠 Collapse many rows into one-per-group and compute a summary (AVG, SUM, COUNT).
🍎 Sorting exam papers into piles by class, then computing each class's average.
`WHERE` filters *individual papers before* piling; `HAVING` filters *whole piles
after* averaging.
💻 `SELECT region, AVG(inflation) FROM indicators GROUP BY region HAVING AVG(inflation) > 5;`
⚙️ Rule of thumb: can't use an aggregate (`AVG(...)`) in `WHERE` — it doesn't
exist until after grouping. Use `HAVING` for that.
📂 `sql/02_core_sql.sql`, exercise 1 in `exercises/day1_sql.sql`.

### CASE WHEN (if/else inside SQL)
🧠 Label or bucket a row based on conditions.
🍎 A sorting hat: "if inflation ≥ 8 → 'Severe', else if ≥ 5 → 'High', else …".
The **first** matching line wins, top to bottom.
💻 `CASE WHEN inflation >= 8 THEN 'Severe' ELSE 'Moderate' END`
📂 `sql/02_core_sql.sql`, exercises 1–2.

### JOINs (gluing tables together)
🧠 Combine two tables by a shared key (e.g. `country_code`).
🍎 Two address books — one has phone numbers, one has emails. A JOIN matches them
by name so you get both in one row. **INNER JOIN** keeps only names in *both*;
**LEFT JOIN** keeps *everyone* from the left book, leaving blanks where the right
has no match.
💻 `SELECT i.*, c.country_name FROM indicators i JOIN countries c ON c.country_code = i.country_code;`
📂 `sql/03_joins_ctes.sql`.

### CTEs — `WITH` (naming a sub-result)
🧠 Compute an intermediate table, give it a name, then use it.
🍎 A recipe step: "first make the sauce (call it `sauce`), then use `sauce` in
the main dish." It makes long queries readable instead of deeply nested.
💻 `WITH big AS (SELECT * FROM indicators WHERE gdp_per_capita > 50000) SELECT region, COUNT(*) FROM big GROUP BY region;`
📂 `sql/03_joins_ctes.sql`, every multi-step exercise.

### Window functions (the superpower)
🧠 Compute across a *window* of related rows **without collapsing them** — every
row survives, but each gets a value calculated from its neighbours.
🍎 GROUP BY puts everyone in a pile and gives you one number per pile. A window
function lets each person keep their seat but still know "the class average,"
"my rank," or "the person before me." Nobody disappears.

The ones you'll use:

- **`LAG(x, n)`** — "the value `n` rows ago."
  🍎 Looking over your shoulder at last month's number. 💻 `LAG(inflation, 12)` =
  the value a year earlier → lets you compute year-on-year change.
- **`RANK()`** — "what position is this row within its group?"
  🍎 Leaderboard position. 💻 `RANK() OVER (PARTITION BY year ORDER BY gdp DESC)`.
- **Moving average** — `AVG(x) OVER (ORDER BY date ROWS BETWEEN 11 PRECEDING AND CURRENT ROW)`.
  🍎 A smoothing of bumpy data: each month becomes the average of itself + the
  previous 11 → a 12-month trend line that ignores monthly noise.
- **Running total** — `SUM(x) OVER (ORDER BY date ROWS UNBOUNDED PRECEDING)`.
  🍎 A bank-balance that adds up every transaction from the start to now.

⚙️ `PARTITION BY` = "restart the calculation for each group" (e.g. per country).
`ORDER BY` inside `OVER()` = "in what order do the neighbours line up."
📂 `sql/04_window_functions.sql` (the whole file), exercise 4, `ml/` targets.

---

## 3. Python — wrangling and visualising

Python here is mostly **pandas**: a spreadsheet you control with code.

### The DataFrame
🧠 A table in memory — rows and named columns — that you can filter, transform
and plot.
🍎 Excel, but every action is a written instruction you can re-run exactly. No
more "which cells did I click?".
💻 `df = pd.read_csv("fred_rates_static.csv"); df.head()`
📂 every Python file.

### `read_sql_query` — SQL *inside* Python
🧠 Run a SQL query against the database and get the answer back as a DataFrame.
🍎 The hand-off: SQL is great at *selecting/aggregating* stored data; Python is
great at *transforming and plotting*. This is the bridge between them.
💻 `df = pd.read_sql_query("SELECT * FROM v_yield_curve", engine)`
📂 `scripts/pipeline.py`, `scripts/financial_indicators.py`, exercise 3.

### Method chaining (`.assign`, `.query`, `.sort_values`)
🧠 Apply a sequence of transformations in one readable flow.
🍎 An assembly line: the DataFrame moves down the belt, each `.step()` adds or
changes something. You read it top-to-bottom like a story.
💻
```python
(df
 .assign(date=lambda x: pd.to_datetime(x["date"]))
 .query("date >= '2022-01-01'")
 .assign(real_rate=lambda x: x["fed_funds"] - x["cpi_yoy"]))
```
📂 `notebooks/block4_python_apis.py`, `exercises/day2_python.py`.

### `groupby().transform()` (window functions, the pandas way)
🧠 Compute a group statistic and *broadcast it back to every row* (rows survive).
🍎 Exactly the SQL window-function idea: "give each month its decade's average
without throwing months away." `transform` keeps the shape; `agg` collapses it.
💻 `df["decade_mean"] = df.groupby("decade")["real_rate"].transform("mean")`
📂 `exercises/day2_python.py` (exercise 2).

### `pct_change` (growth rates)
🧠 Percentage change vs `n` periods ago.
🍎 "How much more expensive than a year ago?" `pct_change(12)` on monthly data =
year-on-year inflation/growth.
💻 `df["m2_yoy"] = df["m2"].pct_change(12) * 100`
📂 `datasets/download.py`, `scripts/fetch_fred.py`.

### Plotting (matplotlib)
🧠 Turn numbers into a picture so the economics jumps out.
🍎 A chart is an argument: a well-labelled line saying "look, the curve inverted
*here* and the model panicked *there*." Always title, label axes, and interpret.
💻 `ax.plot(df["date"], df["spread_10_2"]); ax.axhline(0)`
⚙️ In Codespaces there's no screen, so charts **save to `outputs/*.png`** instead
of popping up. That's expected.
📂 every plotting script.

### The ETL pipeline (Extract → Transform → Load → Query → Visualise)
🧠 The standard shape of a data workflow.
🍎 A kitchen: **Extract** = buy ingredients (fetch data); **Transform** = prep
them (clean/derive); **Load** = stock the fridge (write to the DB); **Query** =
follow the recipe (SQL); **Visualise** = plate the dish (chart). Each step is
separate so you can fix one without redoing the rest.
📂 `scripts/pipeline.py` is literally these five functions.

---

## 4. Machine learning

ML = letting the computer *find* the pattern from examples, instead of you
writing the rule by hand.

### Supervised vs unsupervised
🧠 Supervised = you have the right answers to learn from (labels). Unsupervised =
you don't; the algorithm finds structure itself.
🍎 Supervised = flashcards with answers on the back (recession / no recession).
Unsupervised = handed a pile of photos and asked to sort them into groups you
weren't told exist.
📂 Supervised: `recession_prediction.py`, `taylor_rule_regression.py`,
`inflation_forecast.py`. Unsupervised: `country_clustering.py`.

### Classification vs regression
🧠 Classification predicts a **category** (yes/no); regression predicts a
**number**.
🍎 "Will it rain tomorrow?" (classification) vs "How many millimetres?" (regression).
📂 Recession = classification (logistic regression). Inflation = regression.

### Train / test split (and why you never shuffle time)
🧠 Learn on one slice of data, then check on a slice the model has **never seen**.
🍎 You revise with past exam papers (train) but you're graded on a *new* paper
(test). If you'd memorised the answer key (trained on the test set) your "score"
would be a lie. For **time series**, the test set must be the *future* — you
can't use 2024 to predict 2015. That's why we use a walk-forward split, never a
random shuffle.
📂 `ml/recession_prediction.py` (TimeSeriesSplit), all ML scripts.

### Overfitting (memorising vs understanding)
🧠 A model that fits the training data *too* perfectly often fails on new data.
🍎 A student who memorises past papers word-for-word but can't answer a slightly
different question. Signs: brilliant on train, poor on test.
📂 `ml/inflation_forecast.py` — plain OLS overfits; that's the lesson.

### Regularisation: Ridge & Lasso
🧠 Penalise the model for using big/too-many coefficients, so it stays simple.
🍎 A packing limit for a suitcase. **Ridge** makes you pack everything *lighter*
(shrinks all coefficients). **Lasso** makes you *leave some items out entirely*
(sets coefficients to exactly zero = automatic variable selection — it *chooses*
which indicators matter).
📂 `ml/inflation_forecast.py`.

### Logistic regression
🧠 Regression that outputs a **probability** between 0 and 1 instead of any number.
🍎 An S-shaped dial: as the yield curve inverts more, the "recession" dial slides
toward 1. The economist's old friend the **logit/probit** — same thing.
📂 `ml/recession_prediction.py`.

### k-means clustering + PCA
🧠 k-means groups similar rows into `k` clusters; PCA squashes many columns into 2
so you can *see* them.
🍎 k-means = seating guests at `k` tables so each table is full of similar people.
PCA = taking a 6-dimensional object and drawing its most informative 2D shadow on
the wall so you can look at it.
📂 `ml/country_clustering.py`.

### ROC-AUC, accuracy, and why we don't trust accuracy here
🧠 Accuracy = % correct. ROC-AUC = how well the model *ranks* risky vs safe,
across all thresholds.
🍎 Recessions are rare (~15% of months). A lazy model that always says "no
recession" is ~85% accurate and **useless**. AUC isn't fooled by rare events —
that's why we report it.
📂 `ml/recession_prediction.py`.

---

## 5. How a whole analysis fits together

The course is one pipeline you can read end to end:

```
FRED / World Bank / OECD          ← raw data (datasets/)
        │  download.py
        ▼
   *_static.csv                   ← tidy CSVs
        │  setup_db.py
        ▼
     macro.db  + 4 views          ← the database (db/)
        │
   ┌────┴───────────────┐
   ▼                    ▼
 sql/*.sql          scripts/*.py        ← ask questions / transform
   │                    │  pipeline.py, financial_indicators.py
   └────────┬───────────┘
            ▼
        outputs/*.png              ← charts that answer the question
            │
            ▼
   ml/*.py  → predictions          ← let the data find the pattern
            │
            ▼
   your paper + portfolio          ← docs/writing_scientific_papers.md
```

Every box is a file you can open, run, and explain. If you can narrate this
diagram out loud — what each arrow does and *why* — you've understood the course.
That's the Feynman test. ✅
