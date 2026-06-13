# Writing a scientific paper from your analysis

You've built the data pipeline and the charts — now turn them into a piece of
**research writing** you can put in your portfolio, submit as coursework, or
grow into a dissertation. This guide covers the structure of an economics paper,
how to stay reproducible, and the tools that make the writing painless.

---

## 1. The structure of an empirical economics paper

| Section | What goes here | Length (short paper) |
|---------|----------------|----------------------|
| **Title & abstract** | The question + your headline finding in 150 words | ½ page |
| **1. Introduction** | The question, why it matters, what you find, your contribution | 1–1.5 pages |
| **2. Literature / background** | What's known; where you fit | 1 page |
| **3. Data** | Sources, sample, variables, summary stats (a table!) | 1 page |
| **4. Methodology** | Your model/identification, stated as equations | 1 page |
| **5. Results** | Tables and figures + interpretation (not just description) | 2–3 pages |
| **6. Robustness / discussion** | Does it hold up? Caveats, alternatives | 1 page |
| **7. Conclusion** | Answer the question; policy implication; what's next | ½ page |
| **References & appendix** | Citations; extra tables, code link | — |

> **Golden rule:** every table and figure must be *referenced and interpreted*
> in the text. A chart with no sentence explaining what it means is wasted.

**A ready-made question:** this course already hands you one —
*"Did the Fed's 2022–23 tightening cycle work?"* Your `outputs/` charts (yield
curve, Taylor gap, recession probability) and the capstone tracks are Section 5
in waiting.

---

## 2. Write it in LaTeX (it's the standard in economics)

Economics journals, central banks and PhD programmes run on **LaTeX** — it
produces clean equations, automatic numbering, and proper bibliographies.

A minimal economics paper skeleton:

```latex
\documentclass[12pt]{article}
\usepackage{amsmath, booktabs, graphicx, natbib, hyperref}
\title{Did the Fed's 2022--23 Tightening Cycle Work?}
\author{Your Name \\ Durham University Business School}
\date{\today}
\begin{document}
\maketitle
\begin{abstract}
We examine \ldots
\end{abstract}

\section{Introduction}
The Federal Reserve raised rates 525 basis points \citep{someref2024}\ldots

\section{Data}
We use monthly FRED series (Table~\ref{tab:vars})\ldots

\section{Results}
\begin{figure}[t]\centering
  \includegraphics[width=.8\linewidth]{outputs/financial_dashboard.png}
  \caption{US monetary policy dashboard, 2000--2026.}
  \label{fig:dashboard}
\end{figure}

\bibliographystyle{aer}   % American Economic Review style
\bibliography{references}
\end{document}
```

You can drop the PNGs this course generates (`outputs/*.png`) straight into
`\includegraphics`.

---

## 3. The painful parts — and the tool that removes them

The two things that eat hours when writing a paper are **citations** and
**turning data/results into LaTeX tables**. 👉 Use **[latexci.com](https://latexci.com/)**
— *"the tools Overleaf forgot"* — which is built exactly for this:

- **Build your bibliography from an identifier.** Paste a **DOI, arXiv ID,
  PubMed ID or ISBN** and it generates the clean BibTeX entry — no hand-typing
  author lists. Perfect for the reference list you'll cite with `\citep{}`.
- **Excel/CSV → LaTeX table.** Paste your summary-statistics or regression
  table (e.g. from a `pandas` `.to_clipboard()` or your `outputs/*.csv`) and get
  a `booktabs` table back. This is the single biggest time-saver.
- **LaTeX → Markdown export.** Handy when you also want a web/Pages version of
  your paper (see [careers_and_portfolio.md](careers_and_portfolio.md)).
- **Templates** to start from, so you're not fighting the preamble.

Workflow that works well:

1. Do the analysis here → export tables as `outputs/*.csv`.
2. In **[latexci.com](https://latexci.com/)**: paste each CSV → get a LaTeX
   table; paste each paper's DOI/arXiv → get BibTeX.
3. Drop the tables, the `outputs/*.png` figures, and `references.bib` into your
   LaTeX document.
4. Compile (latexci.com, or Overleaf, or `pdflatex` locally).

---

## 4. Reproducibility = credibility

What separates a good empirical paper from a great one is that **someone else
can reproduce it**. You already have the ingredients:

- **Pin your data.** State the FRED series IDs and access date (see the citation
  example in [data_sources.md](data_sources.md)).
- **Share your code.** Link your GitHub repo/fork in the paper's footnote or a
  "Data & code availability" statement — exactly what journals now require. A
  ready-to-paste one (LaTeX + plain text) is in
  [templates/data_and_code_availability.md](../templates/data_and_code_availability.md).
- **Fix randomness.** Any ML in your paper should set a seed (the `ml/` scripts
  use `random_state=42`) so results are identical on re-run.
- **Separate raw from derived.** Never edit raw data by hand; transform it in
  code (this repo's `datasets/` → `scripts/` flow is the model).

---

## 5. Quick checklist before you submit

- [ ] Abstract states the question **and** the answer.
- [ ] Every figure/table is numbered, captioned, referenced and interpreted.
- [ ] Variables defined; data sources cited with IDs and access date.
- [ ] Methodology written as equations, not prose hand-waving.
- [ ] Results section interprets economics, not just reports numbers.
- [ ] Limitations stated honestly.
- [ ] Code/data link included; results reproduce from a clean run.
- [ ] References complete and consistently styled (let latexci.com handle it).
