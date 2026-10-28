# Phase close-out report: P5 Publish and release

Phase: P5 Publish and release
Parent issue: #31
Pull request: #35, merged as `7dcaa40`
Tag: `v0.1.0`
Release: https://github.com/UBC-FRESH/femic-tsa27-instance/releases/tag/v0.1.0
Docs: https://ubc-fresh.github.io/femic-tsa27-instance/
Date: 2026-10-28
Status: complete.

## Recommendation

The phase is complete. The next modelling step is a multi-rotation WS4 AAC optimization, not another release task.

## Acceptance

| Criterion | Evidence | Status |
| --- | --- | --- |
| Final report states model, results, limitations | `reports/tsa27-final-report.md` | met |
| FEMIC submodule link | FEMIC PR #444 merged as `059fba5`; `external/femic-tsa27-instance` pinned at `b241595` | met |
| Tag and release exist | `v0.1.0`; release URL | met |
| Docs site live | `https://ubc-fresh.github.io/femic-tsa27-instance/` returns 200 | met |
| Dashboard green | local green; CI run `40611147348` | met |

## Deviations

- The submodule pins `b241595` (P4 merge), not the P5 release commit. Bump it to `7dcaa40` in a follow-up if desired.
- The published result is first-period capacity, not AAC.
- Matrix 13% and the historical deferral are mapped but not enforced.

## Next

A multi-rotation WS4 optimization with the full TSR netdown sequence is the AAC follow-on. It should produce the actual caribou/AAC attribution.
