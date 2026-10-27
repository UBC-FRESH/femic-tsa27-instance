# TSA 27 model-input QA

**Status:** P2.4 QA of the FEMIC compile.

## Checks

| Check | Evidence | Status |
|---|---|---|
| Stand checkpoint exists | `data/vri_vclr1p_checkpoint8.feather`: 37,463 stands | pass |
| THLB stands and area | 6,439 stands; 79,102 ha | pass, with a stated limit |
| Model AUs | 18 AUs; every AU has an untreated and a treated curve | pass |
| Curves | 1,008 curves; 6,939 curve points; age range 0–350 | pass |
| TIPSY errors | `data/04_error-tsa27.csv` has 0 data rows | pass |
| VDYP runs | `runtime/logs/vdyp_runs-tsa27-tsa27_p2_compile.jsonl` contains successful runs; warnings are recorded | pass with warnings |
| BTC run | `tsa27_btc5_tsa27` completed; bundle written | pass |
| THLB vs TSR | 79,102 ha vs 57,908 ha (2010) and 51,454 ha (2022) | not comparable yet; explained |
| Caribou flags | P1 flags are not in the legacy checkpoint | deferred to P3 join |

## THLB residual

The compiled THLB is **79,102 ha**, which is **21,194 ha above** the 2010 TSR4 THLB (57,908 ha) and **27,648 ha above** the 2022 TSR5 preliminary THLB (51,454 ha). This is expected: the legacy compile did not apply the full TSR netdown sequence (ownership, operability, low sites, non-merchantable, riparian, WTP, legal OGMA/MOGMA, caribou UWR). The P1 direct UWR clip is available for the P3 fragment join. The residual is **explained and not a QA failure**; it is the main remaining land-base gap.

## Caribou flags

The legacy checkpoint carries the VRI/stand attributes, AU, curves, and THLB fields, but not the P1 caribou flags. P3 will join `caribou_uwr`, `caribou_core`, `caribou_matrix`, `caribou_zone`, and `caribou_immature` to the WS4 fragments by `FEATURE_ID`/`POLYGON_ID` and the UWR geometry.

## Yield-curve notes

- The six model strata are `ESSF_BL`, `ESSF_HM`, `ESSF_SE`, `ICH_CW`, `ICH_FDI`, and `ICH_HW`, each with L/M/H site-index levels.
- The TIPSY rules use a provisional catch-all for species/BEC combinations not covered by the first rule. This is documented in `config/tipsy/tsa27.yaml`.
- VDYP emitted fit-quality warnings for some strata (for example early overshoot). They are recorded in `runtime/logs/vdyp_curve_events-*.jsonl` and do not stop the compile.

## Verdict

The model-input bundle is **usable for the P3 WS4 build**. The THLB and caribou layers must be reconciled/joined before any AAC result is interpreted. The 2022 STSM results remain unpublished; the P2 QA cannot validate against them.
