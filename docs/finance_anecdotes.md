# Stories from the markets — the anecdotes behind the numbers

Every series in this course has a human story behind it: a panicking trading
floor, an economist eating his words, a central banker breaking the economy on
purpose. These are real, and they make the concepts stick. Read the one that
matches each block — then go look for it in the data yourself.

> Each story: **what happened** · **the lesson** · ↪ **where in the course**.

---

## Inflation & the money supply

### "Team Transitory" — the word the Fed had to retire
Through most of 2021, the Fed, the US Treasury and a chorus of economists
insisted the post-COVID inflation spike was **"transitory"** — a temporary blip
from supply chains and base effects. By November 2021, with CPI tearing toward
7%, Chair Jerome Powell stood up and said it was *"probably a good time to retire
that word."* Inflation went on to peak at **9.1%** in June 2022.
**Lesson:** forecasting is humbling; a confident consensus can be confidently
wrong. Always check the data against the narrative.
↪ `sql/02_core_sql.sql`, `cpi_yoy` in `fred_rates`.

### Milton Friedman's revenge — "always and everywhere a monetary phenomenon"
Friedman's most famous line is *"inflation is always and everywhere a monetary
phenomenon."* For decades after the 1980s it looked outdated — money grew, prices
didn't. Then in 2020–21 the US money supply (M2) exploded by **~26%**, the largest
peacetime jump on record, as stimulus cheques landed. A small band of monetarists
warned loudly. Eighteen months later, inflation arrived on cue.
**Lesson:** old theories aren't dead — they're waiting for their conditions.
↪ `m2_yoy` in `fred_rates`; `ml/inflation_forecast.py` (Lasso *keeps* M2 growth).

### Wheelbarrows of cash — Argentina & Turkey
While the West argued over 8% inflation, **Argentina** ran past **100%** in 2023
and **Turkey** near 85% in 2022 — the latter partly because President Erdoğan
insisted, against all orthodoxy, that *high* interest rates *cause* inflation, and
forced the central bank to cut. Argentines learned to spend pesos the day they
got them and trade for "blue dollars" on the street.
**Lesson:** the "common global shock" story collapses at the tails — these were
domestic, monetary, political crises.
↪ The G20 divergence query, `sql/02_core_sql.sql` & exercise 1; the `ARG`/`TUR`
cluster in `ml/country_clustering.py`.

---

## Interest rates & the Fed

### Paul Volcker breaks inflation — on purpose (1979–82)
Inflation hit **14.8%** in 1980. New Fed Chair **Paul Volcker** — 6′7″, chain-
smoking cheap cigars — jacked the federal funds rate to nearly **20%**,
*deliberately* triggering back-to-back recessions and 10.8% unemployment to
crush it. Furious car dealers mailed him the keys of unsold cars; homebuilders
posted him sawn 2×4 planks; farmers blockaded the Fed building with tractors. It
worked: inflation fell to ~3% by 1983.
**Lesson:** the brake pedal is real, and pressing it hurts. Every rate-cycle
since is measured against Volcker's resolve — including 2022.
↪ `fed_funds` history (the 1980–82 spike is in the data); `scripts/concepts.py`.

### The Taylor Rule — a formula that embarrassed the Fed
In 1993 Stanford's **John Taylor** showed that a one-line formula —
react to inflation and the output gap — described the Fed's *actual* behaviour
in the 1980s–90s shockingly well. It became the world's most famous policy rule.
Taylor then spent years arguing the Fed *deviated* from it (too loose in the
2000s, too slow in 2021) — using his own rule as a stick.
**Lesson:** a simple, transparent rule can be both a description and a critique.
↪ `taylor_rule`/`taylor_gap`; `ml/taylor_rule_regression.py` *learns* the rule.

### The rarest trick in central banking — the "soft landing"
Raising rates enough to stop inflation *without* causing a recession is so rare
it has a name. Alan **Greenspan** pulled off the canonical one in **1994–95**
(he doubled rates to 6% and the economy kept growing). Almost every other cycle
ended in recession. The whole question of 2023–24 is whether Powell achieved the
*second* clean soft landing in modern history.
**Lesson:** the base rate matters — soft landings are the exception, not the plan.
↪ The course's central question; `ml/recession_prediction.py`.

---

## The yield curve

### The man who uninvented his own recession indicator
In a 1986 Chicago PhD thesis, **Campbell Harvey** showed that an *inverted* yield
curve (short rates above long rates) had preceded every modern US recession. It
became Wall Street's most-watched crystal ball. So when the curve inverted in
2022 — deeper and **longer than ever recorded** — everyone braced. By 2024,
Harvey himself was publicly suggesting *his own indicator might be giving a false
signal this time*. As of writing, no recession has come.
**Lesson:** even a 50-year-old empirical regularity can break. Models describe
the past; they don't own the future. This is the puzzle the whole course chases.
↪ `sql/04_window_functions.sql` (inversion episodes); `ml/recession_prediction.py`.

### LTCM (1998) — when genius failed
Long-Term Capital Management was run by bond legends and **two Nobel laureates**
(Merton & Scholes). Leveraged ~25-to-1, it bet that spreads would converge. When
Russia defaulted in August 1998, the bets blew up, the yield curve briefly
inverted on panic, and the Fed orchestrated a **$3.6bn** bank bailout to stop the
contagion.
**Lesson:** brilliance + leverage + a tail event = ruin. Markets have fatter
tails than models assume.
↪ The 1998 blip in the inversion history; credit-spread spikes.

---

## Credit, bonds & duration

### Silicon Valley Bank — killed by "safe" government bonds (March 2023)
SVB did nothing exotic: it parked deposits in **long-dated US Treasuries** — the
"safest" asset on earth. But when the Fed hiked 500bp, the *price* of those
long bonds collapsed (bonds fall when rates rise — **duration risk**). Depositors
noticed the unrealised losses, and on **10 March 2023** tried to pull **$42bn in
a single day** — the first **smartphone/Twitter-fuelled bank run**. SVB became the
second-largest US bank failure to that point, in under 48 hours.
**Lesson:** "safe" assets carry interest-rate risk. The tightening cycle didn't
break the economy — but it broke a bank. Risk hides in duration.
↪ Why rates and bond prices move opposite; `rate_10y`, `mortgage_30y` in the data.

### "Whatever it takes" — three words that saved the euro (2012)
At the height of the euro-zone crisis, with Italian and Spanish borrowing costs
exploding, ECB President **Mario Draghi** said: *"Within our mandate, the ECB is
ready to do whatever it takes to preserve the euro. And believe me, it will be
enough."* He hadn't actually spent a cent yet — but spreads collapsed on the
*promise* alone.
**Lesson:** in finance, credible words move markets as much as actions.
Expectations are a policy tool.
↪ Credit spreads (`ig_spread`, `hy_spread`); `scripts/concepts.py` (demo 4).

---

## The UK angle (read this one, Durham!)

### The 49-day Prime Minister vs the bond market (September 2022)
On 23 September 2022, the new Truss government announced **£45bn of unfunded tax
cuts**. UK gilt yields spiked so violently that **pension funds** — which had used
a strategy called **LDI** (liability-driven investing) with leverage — faced
sudden collateral calls. To raise cash they sold gilts, which pushed yields
*higher*, triggering *more* calls: a **doom loop** that came within hours of
collapsing parts of the pension system. The **Bank of England** stepped in with
emergency gilt-buying. Liz Truss resigned after **49 days** — famously outlasted
by a tabloid's livestream of a **lettuce**.
**Lesson:** bond markets discipline governments in real time, and hidden leverage
(LDI) turns a price move into a systemic threat. The same rate dynamics in our US
data played out — with teeth — in the UK gilt market.
↪ `rate_10y` / `spread_10_2` dynamics; a natural capstone extension for Track A.

### The mortgage "golden handcuffs"
By late 2023 the US 30-year mortgage rate hit **7.8%**, up from **3.1%** in 2021.
The twist: housing barely crashed. Why? Anyone with a 3% mortgage refused to sell
and re-buy at 7.5% — so listings dried up and existing-home sales fell to a
~30-year low. Economists call it the **lock-in effect** (or "golden handcuffs").
**Lesson:** policy transmits through behaviour, not just prices. A rate hike can
*freeze* a market instead of cooling it.
↪ `mortgage_spread = mortgage_30y − rate_10y`; `v_credit_dashboard`.

---

## On forecasting humility

### Irving Fisher's worst week (1929)
**Irving Fisher** gave economics the equation at the heart of this course —
`real rate = nominal rate − inflation` — and the theory of debt-deflation. He was
also, on **16 October 1929**, the economist who declared stock prices had reached
*"what looks like a permanently high plateau."* The crash began days later; he
lost his fortune and his public standing.
**Lesson:** the person who hands you a brilliant tool can be catastrophically
wrong about the future. Use the tools; stay humble about predictions. (See also:
"Team Transitory.")
↪ `real_rate` (the Fisher equation); `scripts/concepts.py` (demo 1).

---

## How to use these in your work

- **In class:** each story is a 60-second hook before the maths.
- **In your paper:** open the introduction with the anecdote that frames your
  question (e.g. SVB for a piece on duration risk). It earns the reader's
  attention before a single equation.
- **In an interview:** "the 2022 yield-curve inversion was the longest on record,
  yet Campbell Harvey questioned his own indicator" is exactly the kind of
  informed, current take that lands. Memorise two or three.

*Sources to verify and cite properly (see [data_sources.md](data_sources.md) and
[writing_scientific_papers.md](writing_scientific_papers.md)): FRED for the
series, central-bank speeches/minutes for the quotes, and the financial press for
the events.*
