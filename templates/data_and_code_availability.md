# "Data & Code Availability" — paste into your paper

Journals (and good practice) require a statement saying where your data and code
live so others can reproduce your work. Pick the version that matches your
document, replace the `ANGLE-BRACKET` placeholders, and paste it in.

---

## LaTeX (drop near the end, before References)

```latex
\section*{Data and Code Availability}
All data used in this paper are publicly available at no cost.
US monetary, rate and inflation series were retrieved from FRED
(Federal Reserve Bank of St.\ Louis, \url{https://fred.stlouisfed.org});
cross-country indicators from the World Bank
(\url{https://data.worldbank.org}) and the OECD
(\url{https://data.oecd.org}). Data were accessed on ACCESS-DATE.
All code to reproduce the analysis, figures and tables is available at
\url{https://github.com/YOUR-USERNAME/durham-python-sql-2026} and runs
zero-install via GitHub Codespaces; random seeds are fixed for exact
reproducibility.
```

## Plain text / Markdown (for a Word doc, blog, or README)

> **Data and code availability.** All data used in this paper are publicly
> available at no cost. US monetary, rate and inflation series were retrieved
> from FRED (Federal Reserve Bank of St. Louis, https://fred.stlouisfed.org);
> cross-country indicators from the World Bank (https://data.worldbank.org) and
> the OECD (https://data.oecd.org). Data were accessed on `ACCESS-DATE`. All
> code to reproduce the analysis, figures and tables is available at
> `https://github.com/YOUR-USERNAME/durham-python-sql-2026` and runs zero-install
> via GitHub Codespaces; random seeds are fixed for exact reproducibility.

---

### Per-series citation (when you cite a specific series in the text)

```
Consumer Price Index for All Urban Consumers (CPIAUCSL), U.S. Bureau of Labor
Statistics, retrieved from FRED, Federal Reserve Bank of St. Louis,
https://fred.stlouisfed.org/series/CPIAUCSL (accessed ACCESS-DATE).
```

> 💡 Generate clean BibTeX for the *papers* you cite from a DOI/arXiv ID with
> [latexci.com](https://latexci.com/), and turn your `outputs/*.csv` result
> tables into LaTeX with the same tool. See
> [../docs/writing_scientific_papers.md](../docs/writing_scientific_papers.md).
