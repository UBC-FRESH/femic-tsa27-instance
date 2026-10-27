# FEMIC TSA 27 Revelstoke Instance Roadmap

This roadmap is the plan of record and the issue tracker map for the FEMIC TSA 27 Revelstoke
Instance. Keep it in step with the GitHub issues, `CHANGE_LOG.md`, and `notes/`.
`scripts/check_workflow.py` parses the phase headers, status lines, and checkboxes below, so
keep their format.

Every phase starts as `planned` with `Parent issue: TBD`. Activate a phase only after its
parent issue exists and the maintainer approves it.

## Issue Tracker Map

| Phase | Parent issue | Branch | Status |
| --- | --- | --- | --- |
| P0 Bootstrap | #1 | `feature/p0-bootstrap` | complete |
| P1 Data materialization | #8 | `feature/p1-data` | active |
| P2 FEMIC compile | TBD | `feature/p2-compile` | planned |
| P3 WS4 dataset | TBD | `feature/p3-ws4-build` | planned |
| P4 Caribou scenarios | TBD | `feature/p4-caribou` | planned |
| P5 Publish and release | TBD | `feature/p5-release` | planned |

## Lifecycle Map

| Stage | Phases | Exit criteria |
| --- | --- | --- |
| Bootstrap | P0 | Repo public; CI and dashboard green; report and plan reviewed |
| Data | P1 | Input manifest; TSA 27 land base and caribou zone flags reconciled with TSR tables |
| Compile | P2 | FEMIC model-input bundle with manifest and QA |
| Build | P3 | WS4 dataset loads; constraints inspectable; base simulation runs |
| Verify | P4 | Scenario results and attribution validated against TSR evidence |
| Release | P5 | Public release with reproducible commands and limitations |

## Conventions

- A phase is `P<n>`. A task is `P<n>.<m>`. A subtask is a checklist item inside the task's
  issue body. Three levels at most.
- Status values are `planned`, `active`, `pr-open`, `complete`, and `deferred`.
- A phase becomes `complete` only after its pull request merges to `main` and its parent
  issue closes.
- The evidence base for the caribou policy design is
  `reports/tsa27-tsr-corpus-analysis.md`. The implementation detail is
  `notes/plans/tsa27-model-build-plan.md`.

## Phase 0: Bootstrap

Parent issue: #1
Branch: `feature/p0-bootstrap`
Status: complete

Goal: make the public FEMIC + WS4 instance repository reviewable, with the TSR evidence,
the model-building plan, and a green dashboard.

- [x] P0.1 Render the workflow seed and initialize the FEMIC instance with a TSA 27 profile (#2)
- [x] P0.2 Add the TSR corpus analysis report and curated evidence tables (#3)
- [x] P0.3 Add the model-building plan and scenario schema (#4)
- [x] P0.4 Add TSR and public-data fetch scripts plus provenance docs (#5)
- [x] P0.5 Pass the dashboard and open the P0 pull request (#6)

Acceptance criteria:

- The repository is public at `UBC-FRESH/femic-tsa27-instance`.
- `python scripts/dashboard.py` passes on the head commit.
- `femic prep validate-case` passes for TSA 27 with the public-data mirror.
- The report and plan are linked from `README.md` and `docs/index.rst`.

## Phase 1: Data materialization

Parent issue: #8
Branch: `feature/p1-data`
Status: active

Goal: materialize and reconcile the public data needed for the TSA 27 model.

- [x] P1.1 Fetch and verify the public base datasets (#9)
- [ ] P1.2 Build the TSA 27 land-base layer and caribou zone flags (#10)
- [ ] P1.3 Reconcile land-base totals with the TSR4 and 2022 tables (#11)

Acceptance criteria:

- Every input has a source, version, checksum, and retrieval command.
- The land-base reconciliation report explains each material difference from the TSR tables.
- Raw data is not committed to the repository.

## Phase 2: FEMIC compile

Parent issue: TBD
Branch: `feature/p2-compile`
Status: planned

Goal: compile the TSA 27 land base, AUs, and yield curves with FEMIC.

- [ ] P2.1 Build analysis units and strata
- [ ] P2.2 Run VDYP7 natural and TIPSY managed yield curves
- [ ] P2.3 Compile the THLB checkpoint and model-input bundle
- [ ] P2.4 QA the compiled inputs against TSR evidence

Acceptance criteria:

- The model-input bundle has a manifest and provenance.
- The QA report covers area, volume, and curve comparisons.
- The compile is reproducible from the documented commands.

## Phase 3: WS4 dataset

Parent issue: TBD
Branch: `feature/p3-ws4-build`
Status: planned

Goal: compile the fragment-level WS4 dataset and add caribou, LU/BEC, and seral accounts.

- [ ] P3.1 Build the fragment layer with land-base and caribou attributes
- [ ] P3.2 Compile tracks, curves, treatments, features, and products
- [ ] P3.3 Add caribou and seral constraints
- [ ] P3.4 Run the base simulation and reconcile the land base

Acceptance criteria:

- The dataset loads and the constraints are inspectable.
- The base simulation completes with a recorded seed and run ID.
- The land-base reconciliation is within the stated tolerance.

## Phase 4: Caribou scenarios

Parent issue: TBD
Branch: `feature/p4-caribou`
Status: planned

Goal: run the caribou policy scenarios and attribute the AAC effect.

- [ ] P4.1 Implement scenarios S0–S6
- [ ] P4.2 Run the scenarios with fixed seeds
- [ ] P4.3 Compare harvest, AAC, land base, age class, and matrix disturbance
- [ ] P4.4 Write the attribution and uncertainty report

Acceptance criteria:

- The scenario table reports deltas in m³/yr and percent.
- The matrix and core/UWR audits pass.
- The report states which results validate against TSR4 and which are best guesses for TSR5.

## Phase 5: Publish and release

Parent issue: TBD
Branch: `feature/p5-release`
Status: planned

Goal: publish the instance and cross-link it from the FEMIC repository.

- [ ] P5.1 Write the final report, docs, and figures
- [ ] P5.2 Add the instance as a submodule at `femic/external/femic-tsa27-instance`
- [ ] P5.3 Tag and release after review

Acceptance criteria:

- A clean checkout reproduces the documented commands.
- The host repository pins a reviewed instance commit.
- The release notes state the limitations and the unpublished-TSR uncertainty.

## Detailed Next Steps Notes

1. Create the GitHub repository and the Phase 0 parent/child issues. This needs maintainer
   approval; the maintainer's instruction names the owner, visibility, and purpose.
2. Activate Phase 0 by setting its parent issue number and its status to `active`, here and
   in the tracker map.
3. Create `feature/p0-bootstrap` from `main` and work P0.1–P0.5 one task at a time.
4. Stop after P0 and report the evidence. Do not start P1 until the P0 close-out is approved.
