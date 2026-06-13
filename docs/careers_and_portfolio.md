# Careers & building your portfolio

The skills in this course — Python, SQL, real macro/financial data, a bit of ML,
and the ability to write it up — are exactly what economics and finance
employers screen for. This guide shows **where you could work** and how to
**turn your coursework into a public portfolio** that gets you noticed.

---

## Part 1 — Where Durham economics & finance graduates work

Links go to each institution's main site (look for **Careers / Graduate /
Internships / Analyst programmes**). This is a map, not a ranking.

### Central banks & monetary authorities
| Institution | Link |
|-------------|------|
| Bank of England | https://www.bankofengland.co.uk |
| US Federal Reserve (Board) | https://www.federalreserve.gov |
| Federal Reserve Bank of New York | https://www.newyorkfed.org |
| European Central Bank | https://www.ecb.europa.eu |
| Deutsche Bundesbank | https://www.bundesbank.de |
| Banque de France | https://www.banque-france.fr |
| Swiss National Bank | https://www.snb.ch |

### International & development institutions
| Institution | Link |
|-------------|------|
| International Monetary Fund (IMF) | https://www.imf.org |
| World Bank Group | https://www.worldbank.org |
| OECD | https://www.oecd.org |
| Bank for International Settlements (BIS) | https://www.bis.org |
| European Commission / Eurostat (EU Careers / EPSO) | https://eu-careers.europa.eu |
| European Bank for Reconstruction & Development | https://www.ebrd.com |
| European Investment Bank | https://www.eib.org |
| United Nations | https://careers.un.org |
| Asian Development Bank | https://www.adb.org |

### UK public sector & regulators
| Institution | Link |
|-------------|------|
| Government Economic Service (GES) | https://www.gov.uk/government/organisations/government-economic-service |
| HM Treasury | https://www.gov.uk/government/organisations/hm-treasury |
| Office for Budget Responsibility | https://obr.uk |
| Financial Conduct Authority | https://www.fca.org.uk |
| UK Debt Management Office | https://www.dmo.gov.uk |

### Investment banks
| Institution | Link |
|-------------|------|
| Goldman Sachs | https://www.goldmansachs.com/careers |
| J.P. Morgan | https://careers.jpmorgan.com |
| Morgan Stanley | https://www.morganstanley.com/careers |
| Bank of America | https://campus.bankofamerica.com |
| Citi | https://jobs.citi.com |
| Barclays | https://home.barclays/careers |
| UBS | https://www.ubs.com/careers |
| HSBC | https://www.hsbc.com/careers |
| BNP Paribas | https://group.bnpparibas/en/careers |

### Asset & investment management
| Institution | Link |
|-------------|------|
| BlackRock | https://careers.blackrock.com |
| Vanguard | https://www.vanguardjobs.com |
| Fidelity | https://www.fidelity.com |
| PIMCO | https://www.pimco.com |
| State Street | https://www.statestreet.com |
| Schroders | https://www.schroders.com |
| Legal & General Investment Management | https://www.lgim.com |
| abrdn | https://www.abrdn.com |

### Hedge funds & quantitative / trading
| Institution | Link |
|-------------|------|
| Bridgewater Associates | https://www.bridgewater.com |
| Citadel / Citadel Securities | https://www.citadel.com |
| Two Sigma | https://www.twosigma.com |
| AQR Capital | https://www.aqr.com |
| Man Group | https://www.man.com |
| D. E. Shaw | https://www.deshaw.com |
| Point72 | https://point72.com |
| Jane Street | https://www.janestreet.com |
| Marshall Wace | https://www.mwam.com |

### Economic consulting & professional services
| Institution | Link |
|-------------|------|
| Oxford Economics | https://www.oxfordeconomics.com |
| Frontier Economics | https://www.frontier-economics.com |
| NERA Economic Consulting | https://www.nera.com |
| Charles River Associates (CRA) | https://www.crai.com |
| Cornerstone Research | https://www.cornerstone.com |
| Analysis Group | https://www.analysisgroup.com |
| Oliver Wyman | https://www.oliverwyman.com |
| McKinsey · BCG · Bain | https://www.mckinsey.com · https://www.bcg.com · https://www.bain.com |
| Deloitte / PwC / EY / KPMG (economics) | https://www2.deloitte.com · https://www.pwc.com · https://www.ey.com · https://home.kpmg |

### Think tanks & research institutes
| Institution | Link |
|-------------|------|
| Institute for Fiscal Studies (IFS) | https://ifs.org.uk |
| National Institute of Economic & Social Research (NIESR) | https://www.niesr.ac.uk |
| Resolution Foundation | https://www.resolutionfoundation.org |
| Bruegel | https://www.bruegel.org |
| Brookings Institution | https://www.brookings.edu |
| Peterson Institute (PIIE) | https://www.piie.com |
| Centre for Economic Policy Research (CEPR) | https://cepr.org |
| National Bureau of Economic Research (NBER) | https://www.nber.org |

### Financial data, ratings & fintech
| Institution | Link |
|-------------|------|
| Bloomberg | https://careers.bloomberg.com |
| LSEG (London Stock Exchange Group / Refinitiv) | https://www.lseg.com/careers |
| S&P Global | https://www.spglobal.com |
| Moody's | https://www.moodys.com |
| MSCI | https://www.msci.com |
| FactSet | https://www.factset.com |

---

## Part 2 — Build your portfolio on GitHub Pages (free, ~20 min)

A recruiter googling your name should find **evidence you can do the work**.
GitHub Pages hosts a free website straight from a repository — no servers, no
cost. Here's the simplest path.

### A. Your profile is your storefront
1. Make sure your [GitHub](https://github.com) profile has a real name, photo
   and a one-line bio.
2. Create a **profile README**: make a new repository named **exactly your
   username** (e.g. `jane-doe/jane-doe`), add a `README.md` — it shows on your
   profile page. Put a short intro + links to your projects.

### B. Publish a portfolio website (`username.github.io`)

> ⚡ **Shortcut:** don't start from a blank page — this repo ships a ready
> homepage at **[`templates/portfolio/`](../templates/portfolio/)** (`index.md` +
> `_config.yml`). Copy those two files into your site repo and just replace the
> placeholders. The manual steps below explain what's happening.

1. Create a new repository named **`<your-username>.github.io`** (all lowercase).
2. Add a file `index.md` (Markdown is fine — GitHub renders it as a web page):
   ```markdown
   # Jane Doe — Economics & Data

   MSc Economics, Durham University Business School.
   Python · SQL · applied macro/finance.

   ## Projects
   - **Did the Fed's tightening cycle work?** — built an end-to-end data
     pipeline (FRED/World Bank), SQL analysis and a recession-prediction model.
     [Repo](https://github.com/<you>/durham-python-sql-2026) ·
     [Write-up](papers/fed-tightening.html)
   ```
3. In the repo: **Settings → Pages → Build and deployment → Source: "Deploy from
   a branch" → `main` / root → Save.**
4. Wait ~1 minute. Your site is live at **`https://<your-username>.github.io`**.
5. (Optional) Pick a theme: **Settings → Pages → Theme chooser**, or use a
   ready-made template like [academicpages](https://academicpages.github.io).

### C. Turn THIS course into your first portfolio piece
1. **Fork** this repo (top-right *Fork* button) so it lives under your account.
2. Open it in Codespaces, run the analysis, and **commit your own capstone**
   (pick Track A/B/C and extend it — your charts, your interpretation).
3. Write it up as a short paper (see
   [writing_scientific_papers.md](writing_scientific_papers.md)); export it to
   the web with latexci.com's LaTeX→Markdown and drop it on your Pages site.
4. Embed a result so it's visible at a glance, e.g. in your `index.md`:
   ```markdown
   ![Recession probability model](https://raw.githubusercontent.com/<you>/durham-python-sql-2026/main/outputs/ml_recession_probability.png)
   ```
   *(commit the PNG to your fork first, or link an image you host.)*

### D. What makes a portfolio land interviews
- **A clear README per project**: the question, what you did, the result, how to
  run it. Recruiters skim — lead with the finding.
- **Show the economics, not just the code.** One good chart with a paragraph of
  interpretation beats 500 lines of undocumented script.
- **Reproducible.** "Open in Codespaces and click run" is a powerful signal.
- **Link it everywhere**: CV, LinkedIn, email signature, the profile README.
- **Keep it honest.** Be ready to explain every line in an interview — the same
  rule as the course exercises.

> You finish this course with a working repo, real charts, an ML model and (if
> you write it up) a paper. That is already a portfolio. Host it, link it, and
> you're ahead of most applicants.
