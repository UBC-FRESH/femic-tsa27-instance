# TSA 27 model-input summary

The P2 compile produced a working FEMIC model-input bundle for the Revelstoke TSA.

## Inputs and runs

- Run config: `config/run_profile.tsa27.yaml`
- FEMIC run: `tsa27_p2_compile_final`
- VDYP7: `VDYP7/VDYP7/VDYP7Console.exe` under Wine
- BTC: `TIPSYbtc.exe` under Wine with an Xvfb wrapper
- BTC run: `tsa27_btc5_tsa27`

## Outputs

| Artifact | Value |
|---|---:|
| Stand checkpoint | `data/vri_vclr1p_checkpoint8.feather` |
| Stands | 37,463 |
| THLB stands | 6,439 |
| THLB area | 79,102 ha |
| Model analysis units | 18 |
| Curves | 1,008 |
| Curve points | 6,939 |
| TIPSY error rows | 0 |
| Model-input bundle | `data/model_input_bundle/` |

## Yield-curve coverage

The bundle has 18 untreated and 18 treated base curves, plus species-proportion curves for 27 species. The six strata are `ESSF_BL`, `ESSF_HM`, `ESSF_SE`, `ICH_CW`, `ICH_FDI`, and `ICH_HW`, each with L/M/H site-index levels.

## Provenance

- Manifest: `metadata/model_input_bundle_manifest.yaml`
- TIPSY inputs: `data/03_input-tsa27.csv`
- TIPSY outputs: `data/04_output-tsa27.csv`
- TIPSY parameters: `data/tipsy_params_tsa27.xlsx`
- TIPSY curve table: `data/tipsy_curves_tsa27.csv`
- VDYP logs: `runtime/logs/vdyp_*`
- BTC logs: `vdyp_io/profile_logs/btc_*`

## Limits

- The compiled THLB is 79,102 ha, which is **not** the final TSR THLB (57,908 ha in 2010; 51,454 ha in 2022). The remaining netdowns are P2.4/P3 work.
- The legacy pipeline used its own 18 model AUs, not the 273 P2.1 analysis-unit classes. The P2.1 table is a finer diagnostic; P2.3 uses the model's 18-AU stratification.
- The P1 caribou flags are not yet carried into the checkpoint; P3 will join them to the WS4 fragments.
- The TIPSY catch-all rule in `config/tipsy/tsa27.yaml` is provisional. Replace it with TSR/FSP-specific rules in a later calibration.
