# Poseidon — Infrastructure Intelligence

A working research desk for global infrastructure, port terminals and finance interview practice.

**Live app:** https://wassimibrahim.github.io/laith/

## What it does

- Collects public RSS/Atom feeds and multilingual news-index headlines every six hours using GitHub Actions.
- Searches 25 configured channels across ports, regional infrastructure, M&A, concessions, energy, digital infrastructure, transport, utilities and capital formation.
- Deduplicates by canonical URL or exact normalized title, preserves first-seen dates and keeps a growing archive.
- Publishes a dated daily Markdown briefing and a dashboard with searchable records, source links and collection health.
- Includes nine primary-source-reviewed starting examples, six guided interview cases and an editable finite-concession terminal acquisition model.
- Explains operating drivers, enterprise and equity value, debt capacity, DSCR, DCF, sponsor IRR, MOIC, sensitivity and downside cases from first principles.
- Saves bookmarks and personal research leads, including LinkedIn links, in **browser-local storage** with JSON import/export. These notes are not uploaded or synchronized.

## Run locally

Requires Python 3.10+ (with zoneinfo) and Node.js 20+. There are no third-party runtime dependencies.

```sh
npm test
npm run dev
```

Open `http://127.0.0.1:4173`. Opening the HTML file directly may block JSON loading.

```sh
npm run collect     # Fetch feeds and write data + daily report
npm run build       # Copy only public app assets into dist/
```

## Continuous collection and GitHub Pages

The workflow `.github/workflows/intelligence.yml` runs on pushes to `main`, manual dispatch, and at **04:17, 10:17, 16:17 and 22:17 UTC**. This is four scheduled collections per day, not a live streaming service. Madrid is UTC+1 in winter and UTC+2 in summer; the first run is therefore 05:17 or 06:17 Madrid time. GitHub schedules can be delayed and may be disabled for inactive public repositories. See [GitHub schedule documentation](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule).

The workflow tests the code, collects feeds, commits public data and reports, builds the app, and deploys it to Pages. Set **Settings → Pages → Source → GitHub Actions**. `GITHUB_TOKEN` needs repository contents write, Pages write and OIDC permissions, already declared in the workflow. No paid API key is required. Branch rules or organization policies can still prevent writes/deployment.

On total source failure the previous archive is retained, current failure health is published, and the workflow ends in failure. Individual feed errors are visible in Sources & coverage. GitHub controls workflow failure notifications through your account settings. This application does not send email or LinkedIn messages.

The Refresh button reloads the **published** data; it does not trigger the collector. To collect immediately, run the workflow from the repository’s Actions tab or run `npm run collect` locally.

## Sources, scope and truth boundaries

`data/sources.json` is the editable source registry. RSS is used for discovery; article bodies are not copied. Google News RSS is an unofficial, best-effort public endpoint and can change or block requests. Public-feed access is not a guarantee of complete indexing. Seven language editions broaden discovery but do not translate headlines. Source region is the **query scope**, not a verified location. Keyword categories and relevance scores are heuristics, not facts or confidence scores.

There is no credible way to guarantee every deal worldwide: private deals, unindexed publications, many company filings, paywalled databases and closed social content will be missed. This build is a public-source intelligence and learning tool, not a replacement for a licensed institutional deal database. It does not bypass access controls or scrape logged-in LinkedIn. LinkedIn references can be saved manually as leads; additional licensed or authorized feeds require an appropriate provider and credentials. [LinkedIn’s stated restrictions](https://www.linkedin.com/help/linkedin/answer/a1341387/prohibition-of-scraping-software?lang=en-us).

`data/curated.json` contains reviewed announcements with original links, source dates, value bases, known facts, analytical interpretations and unanswered diligence questions. A review confirms the cited announcement, not every subsequent closing development. Update these records when new primary evidence changes a transaction’s status. Automatic feeds never silently promote a headline to a confirmed deal, invent consideration, identify banks from association, or treat a project budget as enterprise value.

The nine reviewed examples were researched on 6 October 2026. They include the Luanda expansion, Maasvlakte II, Jeddah, Fujairah, Antwerp, Klaipėda, atNorth, Last Mile and Southampton cranes. Some are historical learning references rather than current-day transactions.

## Financial model conventions

All practice model inputs are hypothetical, **not estimates of undisclosed company figures**. Money is in EUR millions except throughput and EUR per TEU. It assumes a cash-free, debt-free acquisition, entry fees funded by equity, annual end-period cash flows, fixed tariff and margin, volume capped at capacity, straight-line debt principal, and interest on opening debt. Cash tax is floored at zero without tax loss carryforwards. The operating DCF uses unlevered taxes; equity cash flows include the interest tax shield.

There is **no perpetual terminal value**. Sponsor exit value equals the value at exit of the remaining concession cash flows, less remaining debt. No extension, residual proceeds, working-capital recovery, handback cost or exit fee is modeled. MOIC includes additional negative sponsor cash flows as invested capital. IRR is shown only when the implemented bracket search finds a unique bracket; complex nonconventional cash flows need a full root analysis. A negative chart bar is visually floored; exact cash values are in the table.

The scenarios are deliberately simplified. Detailed investment work requires volume contracts, cost behavior, capex timing, depreciation, tax, reserves, concessions, covenants, inflation and funding schedules. The glossary and case explanations make those limits visible.

## Architecture and maintenance

- `scripts/collect.py`: bounded requests, three attempts, four concurrent workers, RSS/Atom parsing, date filters, URL validation, canonicalization, archive merge, health, reports.
- `app/finance.js`: deterministic financial calculations tested against independent identities and known answers.
- `app/cases.js`: six complete guided cases and 18 beginner definitions.
- `app/app.js`: static client app; no service-side secrets or third-party analytics.
- `data/`: public research only. **Do not commit confidential notes or licensed article text.**
- `reports/`: one Markdown report per Madrid calendar day, updated on subsequent runs that day.
- `tests/`: financial reconciliation and feed-parsing regression tests.

To add a source, edit `data/sources.json`, run the collector, inspect its results and source health, and commit. RSS feeds may fail with 403 or change format; do not bypass a block. Use a supported feed or authorized provider instead. Archives grow over time; for larger institutional coverage, migrate the data store to a database, add entity resolution, licensed filings/deal feeds, review workflows and alerting. No such additional backend or AI enrichment is implied by this version.

Google Fonts is the only optional external UI resource; system fonts provide fallback. The app is public on GitHub Pages. Browser-local notes depend on the domain and browser; export them before changing device or domain.
