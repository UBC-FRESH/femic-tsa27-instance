# Phase close-out report: P0 Bootstrap the public instance

Phase: P0 Bootstrap
Parent issue: #1
Pull request: #7, `feature/p0-bootstrap` into `main`
Evidence head: `59a130b`, the head covered by CI run `40567318540`
Report commit: the commit that adds this report; its CI run is posted on pull request #7
Date: 2026-10-27
Status: queued for approval. Not merged.

## Recommendation

Approve these actions. The agent carries them out in this order, and reads back each result.

1. Squash-merge pull request #7, and delete the branch `feature/p0-bootstrap`.
2. Close parent issue #1 with a closeout comment that cites the merge commit.
3. Launch P1 Data materialization: create its branch, set the phase statuses in `ROADMAP.md`, create its child issues as sub-issues, and start P1.1.

Settings changes, each with its exact command. Each one runs only after its own approval.

- None in P0. GitHub Pages is not enabled, so the Docs deploy workflow on `main` fails with `Creating Pages deployment failed: Not Found`. The docs **build** gate is green. Recommend enabling Pages at the P5 release with the exact command below, after approval:
  `gh api --method POST repos/UBC-FRESH/femic-tsa27-instance/pages -f build_type=workflow`

## 1. Objectives and acceptance

| Criterion | Evidence | Status |
| --- | --- | --- |
| The repository is public at `UBC-FRESH/femic-tsa27-instance` | Repository URL; `gh repo view` reports public | met |
| `python scripts/dashboard.py` passes on the head commit | Local run on `59a130b`: lint, format, types, tests (154 passed, 100% coverage), validator, docs all green; CI run `40567318540` | met |
| `femic prep validate-case` passes for TSA 27 with the public-data mirror | `Case preflight passed; targets=[27]` | met |
| The report and plan are linked from `README.md` and `docs/index.rst` | README lines 12–14; docs toctree `overview`/`model-design` | met |
| The TSR corpus fetch script has tests and regenerates the facts | `python scripts/fetch_tsr_corpus.py` downloaded 19/19; `femic tsr extract` produced 1,970 facts, 0 failures; `tests/test_fetch_tsr_corpus.py` passes in the full suite | met |
| No raw PDFs or provincial data in git | `git status` clean; `data/tsr/corpus` and `metadata/tsr/tsa_candidate_facts_2022plus.json` are ignored | met |

## 2. Workflow compliance

- Parent issue before the branch: parent #1 created 2026-10-27T19:10:54Z; `feature/p0-bootstrap` created after the initial commit. The initial content landed on `main` before the branch (deviation 1).
- Branch from `main`: merge-base `eb496c5`; branch commits `49b3881` and `59a130b`.
- Commit messages that start with task IDs: `P0.1 initialize the TSA 27 instance repository` (`eb496c5`), `P0.5 activate P0 and record the bootstrap evidence` (`49b3881`), `P0.5 queue the phase review` (`59a130b`), plus the report commit.
- Gates for each commit: section 3.
- Roadmap and changelog in step: `49b3881` and `59a130b` update `ROADMAP.md`, `CHANGE_LOG.md`, and `README.md`.
- Child issues closed with closeout evidence: #2–#6 closed with the commit and verification comments.
- Approval gates: the public repository was created with the maintainer's explicit instruction (owner `UBC-FRESH`, visibility public, purpose named). No tag, release, settings change, or external account was created beyond that. Pages enablement is recommended for P5 with its exact command.

## 3. Gate evidence

| Commit | Gates run | Result |
| --- | --- | --- |
| `eb496c5` | lint, format, types, tests, validator, docs | green |
| `49b3881` | lint, format, types, tests, validator, docs | green |
| `59a130b` | lint, format, types, tests, validator, docs | green |

The local dashboard is `python scripts/dashboard.py`. It reported `OVERALL: GREEN. Every gate passed.` on each head.

## 4. CI evidence

| Run ID | Head commit | Conclusion | Notes |
| --- | --- | --- | --- |
| `40567318540` | `59a130b` | success | Quality gates, Pre-commit parity, and Green dashboard summary all pass |
| `40567208884` | `49b3881` | success | Previous phase head |
| `40566705711` | `eb496c5` | success | Initial `main` push |
| `40566705439` | `eb496c5` | failure | `Docs` deploy failed because GitHub Pages is not enabled (`Creating Pages deployment failed: Not Found`); the docs build itself is green. Deferred to P5. |

## 5. Deviations

| Deviation | Cause | Remedy |
| --- | --- | --- |
| The bootstrap content landed in the initial `main` commit before `feature/p0-bootstrap` existed. | The seed, instance scaffold, report, and plan were prepared before the GitHub repository and phase branch were created. | Disclosed here. Pull request #7 carries the P0 activation, roadmap, changelog, and verification updates. No reviewed branch was rewritten. Future phases create the parent issue and branch before the first content commit. |
| The Docs deploy workflow is red on `main`. | GitHub Pages is not enabled for the new repository. | The docs build gate is green. Pages enablement is recommended for P5 with the exact command in the Recommendation. |

## 6. Next phase

**P1 — Data materialization.**

Goal: materialize and reconcile the public data needed for the TSA 27 model.

Tasks:

- P1.1 Fetch and verify the public base datasets (VRI 2025, TSA boundary, site productivity, BEC v12, LU, UWR/core/matrix, OGMA/MOGMA, roads, cutblocks).
- P1.2 Build the TSA 27 land-base layer and the caribou zone flags.
- P1.3 Reconcile land-base totals with the TSR4 Table 3 and 2022 Table 14.

Acceptance criteria:

- Every input has a source URL, version/date, checksum, and retrieval command.
- The land-base reconciliation report explains each material difference from the TSR tables.
- Raw data remains out of git.

Recommended default: activate P1 and start P1.1 after this report is approved.

## 7. Decision

- [ ] Approve as written.
- [ ] Approve with the changes stated here: <changes>.
