# Phase close-out report: P8 TSA 27 ALS acquisition request

Phase: P8 TSA 27 ALS acquisition request
Parent issue: #43
Pull request: #45, `feature/p8-als-acquisition-request` into `main`
Evidence head: `77686ba`, the commit that adds the request table, memo, docs, and planning entries
Report commit: the commit that refreshes this report. Its CI run is posted on the pull request.
Date: 2026-11-02
Status: queued for approval. Not merged.

## Recommendation

Approve these actions. The agent carries them out in this order, and reads back each result.

1. Squash-merge pull request #45, and delete the branch `feature/p8-als-acquisition-request`.
2. Close child issue #44 with a closeout comment that cites the merge commit.
3. Close parent issue #43 with a closeout comment that cites the merge commit.
4. Do not create a new model phase. Send the request package to the TSA 27 partner
   channel and wait for a remeasurement/acquisition response.

Settings changes, each with its exact command. Each one runs only after its own approval.

- None.

## 1. Objectives and acceptance

| Criterion | Evidence | Status |
| --- | --- | --- |
| Request table covers 67 plots; 13 high-priority ICH | `tsa27-als-acquisition-request.csv`: 67 rows, priority counts 13/9/45 | met |
| High-priority rows record 2019 year and 18-27 year offset | 13 rows, offsets 18-27 | met |
| Each row has a 2 km EPSG:3005 bbox and area | 19 columns including `request_bbox_*` and `request_bbox_area_ha` | met |
| Memo states the current gap and what remeasurement/acquisition unblocks | `reports/tsa27-als-acquisition-request.md` | met |
| No point cloud downloaded, no plot remeasured, no model change | The change set is one script, tests, CSV, memo, docs, and planning | met |
| Dashboard green | `python scripts/dashboard.py` -> OVERALL: GREEN at `77686ba` | met |

## 2. Workflow compliance

- Parent issue before the branch: issue #43 was created before the branch; child
  issue #44 was created immediately after and linked as a sub-issue.
- Branch from `main`: `feature/p8-als-acquisition-request` was created from
  `origin/main` at `3aacbea`.
- Commit messages that start with task IDs: `77686ba` (`P8.1 ...`) and the report
  commit.
- Gates for each commit: section 3.
- Roadmap and changelog in step: both were changed in `77686ba`; the report commit
  only adds this report.
- Child issues closed with closeout evidence: #44 remains open until the merge is
  approved, per the workflow.
- Approval gates: the maintainer's `go` instruction approved the request package;
  merge, branch deletion, and issue closure wait for approval of this report.
- P7 was corrected from `active` to `complete` in the roadmap.

## 3. Gate evidence

At `77686ba`:

```text
GATE                STATUS   SECONDS
lint                GREEN       0.08
format              GREEN       0.07
types               GREEN       0.42
tests               GREEN      23.36
validator           GREEN       0.27
docs                GREEN       0.62

OVERALL: GREEN. Every gate passed.
```

Request result:

```text
67 plots: 13 high, 9 medium, 45 secondary
high-priority request union: 13,475.4 ha
all-plot request union: 60,367.9 ha
high-priority offsets: 18-27 years
```

## 4. CI evidence

| Run ID | Head commit | Conclusion | Notes |
| --- | --- | --- | --- |
| 41408964069 | `d793320` | success | Quality gates, Green dashboard summary, and Pre-commit parity passed. The only later change is this CI-table refresh. |

## 5. Deviations

| Deviation | Cause | Remedy |
| --- | --- | --- |
| The request is a package, not an acquisition | No partner or LidarBC commitment exists | The memo says no point cloud was requested, downloaded, or processed |
| The 2 km bbox is an acquisition footprint | It is not a density or quality guarantee | Recorded as a limit in the memo |
| Remeasuring old plots does not reconstruct the 2019 state | The plots are 1992-2001; the point clouds are 2019 | The memo recommends a 2026 point cloud plus 2026 remeasurement as the cleaner pairing |

## 6. Next phase

Recommended default: **no new model phase**.

Send the request package to the TSA 27 partner channel. The next technical step is a
time-matched remeasurement/point-cloud pilot only after the data arrive.

Reason: the P7 no-go is a data gap, not a model gap.

## 7. Decision

- [ ] Approve as written.
- [ ] Approve with the changes stated here: <changes>.
