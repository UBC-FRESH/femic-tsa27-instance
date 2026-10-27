# Change Log

Newest entries last. Each milestone gets a dated entry that matches the roadmap status and the GitHub issue comments.

## 2026-10-27

- Created FEMIC TSA 27 Revelstoke Instance from the UBC-FRESH dev workflow seed. The agent contract, roadmap, docs skeleton, and validator came from the seed. Every phase is planned, and no parent issues exist yet.

### P0 bootstrap — 2026-10-27

- Created the public repository `UBC-FRESH/femic-tsa27-instance` and activated Phase P0 with parent issue #1 and child issues #2–#6.
- Added the TSR corpus analysis (`reports/tsa27-tsr-corpus-analysis.md`) with the 19-document inventory, the 2010 and 2022 THLB netdown tables, the cycle timeline, and the caribou evidence excerpts.
- Added the detailed model-building plan (`notes/plans/tsa27-model-build-plan.md`) and the S0–S6 caribou scenario schema.
- Added `scripts/fetch_tsr_corpus.py` with unit tests and the raw-data ignore rules; raw TSR PDFs and provincial data remain out of git.
- Added the data provenance and limitations docs and the TSA 27 run profile/TIPSY scaffold.
- Verification: `python scripts/dashboard.py` is green (lint, format, types, tests at 100% coverage, validator, docs). `femic prep validate-case --run-config config/run_profile.tsa27.yaml` passes with the public-data mirror.
