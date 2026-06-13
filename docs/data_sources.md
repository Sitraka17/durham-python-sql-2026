# Economic & Financial Data Sources — a directory

A curated catalogue of where to get real economic and financial data, with
direct links. **Free unless marked.** The course itself uses FRED, the World
Bank and OECD (see [getting_economic_data.md](getting_economic_data.md) for the
*how-to*); this page is your map for dissertations, the capstone, and your
career.

> 💡 **Tip:** prefer sources with a stable **API** and a clear licence — your
> analysis stays reproducible and you can cite exactly what you used.

---

## Macroeconomics & central banks

| Source | What | Link |
|--------|------|------|
| **FRED** (St. Louis Fed) | 800k+ US & global series — the workhorse | https://fred.stlouisfed.org |
| **ALFRED** | "Vintage" FRED data (as-first-released) for real-time analysis | https://alfred.stlouisfed.org |
| US Federal Reserve | Policy, H.15 rates, flow of funds (Z.1) | https://www.federalreserve.gov/data.htm |
| **BEA** | US GDP, NIPA, trade, regional accounts | https://www.bea.gov |
| **BLS** | US inflation (CPI/PPI), employment, wages | https://www.bls.gov |
| European Central Bank | Euro-area data portal | https://data.ecb.europa.eu |
| Bank of England | UK monetary & financial statistics database | https://www.bankofengland.co.uk/boeapps/database |
| Deutsche Bundesbank | German & euro-area time series | https://www.bundesbank.de/en/statistics |
| Bank of Japan | Japanese statistics | https://www.boj.or.jp/en/statistics |

## International organisations

| Source | What | Link |
|--------|------|------|
| **World Bank Open Data** | WDI — ~200 countries, thousands of indicators | https://data.worldbank.org |
| World Bank API | REST/JSON used in this course | https://api.worldbank.org |
| **IMF Data** | IFS, BOP, WEO, fiscal monitor | https://data.imf.org |
| IMF World Economic Outlook | Forecasts & historical macro | https://www.imf.org/en/Publications/WEO |
| **OECD Data** | Cross-country harmonised indicators | https://data.oecd.org |
| OECD.Stat | Full statistical warehouse | https://stats.oecd.org |
| **Eurostat** | Official EU statistics | https://ec.europa.eu/eurostat |
| **BIS** | Cross-border banking, credit, FX, property | https://www.bis.org/statistics |
| UN Comtrade | Bilateral trade flows | https://comtradeplus.un.org |
| UNdata | UN system statistics | https://data.un.org |
| ILOSTAT | Global labour statistics | https://ilostat.ilo.org |
| WTO Stats | Trade & tariffs | https://stats.wto.org |

## United Kingdom

| Source | What | Link |
|--------|------|------|
| **ONS** | UK official statistics (GDP, labour, inflation) | https://www.ons.gov.uk |
| ONS Beta API | Programmatic access | https://developer.ons.gov.uk |
| UK Data Service | Surveys & microdata (academic) | https://ukdataservice.ac.uk |
| data.gov.uk | UK open government data | https://www.data.gov.uk |
| Office for Budget Responsibility | Fiscal forecasts | https://obr.uk |
| HM Treasury | Forecasts comparison, policy | https://www.gov.uk/government/organisations/hm-treasury |

## Markets & finance

| Source | What | Link |
|--------|------|------|
| Yahoo Finance | Equities, FX, indices (use the `yfinance` library) | https://finance.yahoo.com |
| Stooq | Free historical prices (CSV) | https://stooq.com |
| Nasdaq Data Link (ex-Quandl) | Curated financial/economic datasets (free + paid) | https://data.nasdaq.com |
| Alpha Vantage | Free stock/FX/crypto API (key) | https://www.alphavantage.co |
| Tiingo | Prices & fundamentals API (free tier) | https://www.tiingo.com |
| CBOE | VIX and volatility data | https://www.cboe.com |
| **Ken French Data Library** | Factor returns (Fama-French) — essential for finance | https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html |
| WRDS / CRSP / Compustat | Gold-standard academic finance data *(subscription, via Durham)* | https://wrds-www.wharton.upenn.edu |
| LSEG / Refinitiv, Bloomberg | Professional terminals *(subscription)* | https://www.lseg.com · https://www.bloomberg.com |

## Trade, development & long-run history

| Source | What | Link |
|--------|------|------|
| **Our World in Data** | Clean, well-documented global datasets + charts | https://ourworldindata.org |
| Penn World Table | Comparable cross-country output/productivity | https://www.rug.nl/ggdc/productivitytrends/pwt |
| Maddison Project | Long-run GDP back to 1 AD | https://www.rug.nl/ggdc/historicaldevelopment/maddison |
| Gapminder | Development indicators | https://www.gapminder.org/data |
| Economic Policy Uncertainty | EPU indices | https://www.policyuncertainty.com |

## Aggregators & dataset search *(start here when hunting)*

| Source | What | Link |
|--------|------|------|
| **DBnomics** | Aggregates FRED/IMF/OECD/Eurostat/BIS… one API | https://db.nomics.world |
| Google Dataset Search | Search engine for datasets | https://datasetsearch.research.google.com |
| Kaggle Datasets | Community datasets + notebooks | https://www.kaggle.com/datasets |
| Trading Economics | Quick country dashboards | https://tradingeconomics.com |
| data.gov (US) | US open data | https://data.gov |

---

## Citing data properly

In a paper, cite the **source, series ID, access date, and retrieval method**.
Example:

> U.S. inflation: Consumer Price Index for All Urban Consumers (CPIAUCSL),
> U.S. Bureau of Labor Statistics, retrieved from FRED, Federal Reserve Bank of
> St. Louis, https://fred.stlouisfed.org/series/CPIAUCSL (accessed 2026-06-15).

See [writing_scientific_papers.md](writing_scientific_papers.md) for how to
manage these citations automatically.
