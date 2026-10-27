# FEMIC TSA 27 Revelstoke Instance

Public [FEMIC](https://github.com/UBC-FRESH/femic) deployment instance and [WS4](https://github.com/UBC-FRESH/ws4) model case for the Revelstoke Timber Supply Area (TSA 27), including a reproducible Timber Supply Review (TSR) evidence base and a caribou policy modelling pipeline.

## What this answers

> What is the impact of caribou habitat constraints on AAC in the Revelstoke TSA?

The instance is designed to separate the effects of:

1. the legal UWR / core no-harvest exclusion,
2. the matrix habitat constraint (max 13% of area <40 years),
3. the LU/BEC mature+old seral constraints, and
4. the historical 80-year immature-habitat deferral.

The TSR evidence and the answers are in [`reports/tsa27-tsr-corpus-analysis.md`](reports/tsa27-tsr-corpus-analysis.md). The implementation plan is in [`notes/plans/tsa27-model-build-plan.md`](notes/plans/tsa27-model-build-plan.md).

## Status

Phase P0 is complete and Phase P1 is complete and Phase P2 (FEMIC compile) is active. `ROADMAP.md` is the plan of record; the GitHub issues carry the live status. The FEMIC instance scaffold, the TSR evidence base, and the model-building plan are in place; the public data and the WS4 dataset are not yet built.

## Evidence base

The TSR corpus covers TSR1 1994, TSR2 1999, TSR3 2005, TSR4 2010, and the September 2022 TSR5 data package. The 1994 PDFs are scanned; the 1999–2022 documents are text-readable. The key findings:

- TSR2/TSR3 modelled caribou as forest-cover/seral constraints; the area stayed in the THLB.
- TSR4 (2010) made caribou a legal spatial reserve netdown (18,909 ha) plus residual mature biodiversity constraints in caribou landscape units.
- The 2022 data package treats the UWR as a legal no-harvest exclusion from the LHLB (62,892 ha net, 29.1% of AFLB) and proposes a core no-harvest + matrix max 13% <40 years sensitivity.
- The models used were FSSIM (1999/2005), FPS-ATLAS (2010), and STSM2022/SELES10 (2022) — not Patchworks or SPADES.

## Quick start

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
python scripts/dashboard.py
```

FEMIC case preflight:

```bash
export FEMIC_EXTERNAL_DATA_ROOT="${FEMIC_EXTERNAL_DATA_ROOT:-../femic/external/femic-public-data/data}"
femic prep validate-case --run-config config/run_profile.tsa27.yaml
```

TSR corpus materialization:

```bash
python scripts/fetch_tsr_corpus.py
femic tsr extract --documents-path metadata/tsr/tsa_documents_with_2022.json \
  --corpus-root data/tsr/corpus \
  --output-path metadata/tsr/tsa_candidate_facts_2022plus.json --tsa 27
```

The raw TSR PDFs and the extracted full text are ignored by git. Only the document metadata, curated tables, and short evidence excerpts are tracked.

## Repository map

| Path | Purpose |
|---|---|
| `AGENTS.md` | Workflow and domain contract |
| `ROADMAP.md` | Phases, tasks, and the issue tracker map |
| `CHANGE_LOG.md` | Dated narrative of changes |
| `reports/tsa27-tsr-corpus-analysis.md` | TSR corpus analysis, Q&A, and the WS4 pipeline appendix |
| `notes/plans/tsa27-model-build-plan.md` | Detailed model-building plan |
| `config/` | FEMIC run profile, TIPSY scaffold, and TSR recipes |
| `metadata/tsr/` | Document inventory, curated netdown tables, cycle timeline, evidence CSV |
| `scripts/` | TSR/public-data fetch and index helpers |
| `scenarios/` | Caribou policy scenarios (to be filled in P4) |
| `docs/` | Documentation site |

## Data policy

- Public repository: code, docs, derived tables, and short evidence excerpts.
- Raw provincial data and TSR PDFs: fetched at runtime into ignored paths, never committed.
- The shared public-data mirror is `femic/external/femic-public-data/data` in a FEMIC checkout; set `FEMIC_EXTERNAL_DATA_ROOT` to its `data` directory.
- Do not commit credentials, personal paths, or unpublished documents.

## Cross-links

- Host: [UBC-FRESH/femic](https://github.com/UBC-FRESH/femic)
- Model: [UBC-FRESH/ws4](https://github.com/UBC-FRESH/ws4)
- Workflow: [UBC-FRESH/ubc-fresh-dev-workflow](https://github.com/UBC-FRESH/ubc-fresh-dev-workflow)
- Submodule target: `femic/external/femic-tsa27-instance`

## License

MIT for the code and documentation in this repository. Source data and TSR documents retain their original government licences and are not redistributed here.
