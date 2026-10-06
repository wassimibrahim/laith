# Validation record

Validated on 6 October 2026.

- 8 Node.js finance tests passed: independent cash-flow bridge, sources/uses, debt amortization, finite-concession exit identity, known IRR solutions, tax-shield reconciliation, scenario direction and debt capacity.
- 9 Python collector tests passed: URL canonicalization, unsafe-scheme rejection, RSS and Atom parsing, unknown/old dates, duplicate merging, non-feed and malformed responses, classification regression, and all-source failure preserving the archive.
- Live local collection: 25 configured channels, 24 responding, 1,124 unique headlines in the first archive. Port Technology returned HTTP 403 and was recorded as failed.
- Browser checks: dashboard, company/asset search, reviewed-evidence filter, source-detail modal, model scenario switching, invalid-input handling, debt repayment display, research-note save/reload/delete.
- Narrow-screen and desktop layouts inspected; narrow-screen document width did not exceed the viewport. Wide financial tables and navigation use their own horizontal scrolling.
- Local notes remained browser-local; no user notes were exported into the repository.

First public deployment and production collection succeeded in GitHub Actions run 37526190534. The live Pages URL is checked separately before handoff. Later data counts are expected to change with each collection.

This is not exhaustive coverage validation, assurance of future feed availability, or independent verification of every discovered headline.
