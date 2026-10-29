# TSA 27 Figure 4 recovery — annual scaled volume 2009–2021

**Status:** recovered and validated against Table 19. Figure values are approximate; Table 19 is authoritative.

## Source

- Document: *Revelstoke TSA Timber Supply Review Data Package*, September 2022.
- File: `data/tsr/corpus/tsa/tsa_27/TSR_2022/Data_Package/27ts_dp_2022.pdf`
- Page: 45, Figure 4, “Revelstoke TSA Annual Scaled Volume 2009 - 2021 (HBS)”.
- Supporting table: page 46, Table 19, “Volume harvested in the Revelstoke TSA from 2009 to 2021”.

The figure caption says “1995 to 2019”, but the chart title, labels, and data are 2009–2021. The caption is a document error.

## Recovery method

`figrecover` 0.1.0a1 was used on a 300 dpi render of page 45:

1. Render page 45 at 300 dpi.
2. Crop the plot to pixel box `(660, 1250, 2130, 2110)`.
3. Calibrate the plot frame: x `2009–2021`, y `0–300,000`.
4. Digitize the blue bars (`#4471C4`) in bar mode.
5. Digitize the black dashed AAC line in line mode.

Artifacts are under `runtime/document_ingestion/tsa27-dp2022-fig4/`.

## Recovered values and validation

| Year | Figure volume (m³) | Table 19 volume (m³) | Figure minus table (m³) | AAC (m³) | Harvest / AAC |
|---:|---:|---:|---:|---:|---:|
| 2009 | 196,364 | 196,891 | −527 | 230,000 | 86% |
| 2010 | 145,455 | 146,057 | −602 | 230,000 | 64% |
| 2011 | 196,727 | 197,163 | −436 | 225,000 | 88% |
| 2012 | 214,182 | 214,580 | −398 | 225,000 | 95% |
| 2013 | 271,636 | 272,294 | −658 | 225,000 | 121% |
| 2014 | 236,727 | 237,225 | −498 | 225,000 | 105% |
| 2015 | 172,727 | 173,142 | −415 | 225,000 | 77% |
| 2016 | 215,273 | 215,721 | −448 | 225,000 | 96% |
| 2017 | 166,545 | 167,131 | −586 | 225,000 | 74% |
| 2018 | 208,727 | 209,355 | −628 | 225,000 | 93% |
| 2019 | 110,545 | 110,977 | −432 | 225,000 | 49% |
| 2020 | 105,455 | 105,994 | −539 | 225,000 | 47% |
| 2021 | 68,000 | 68,608 | −608 | 225,000 | 30% |

The mean absolute figure-recovery error is **521 m³/yr**, about 0.3% of the annual values. The recovered total is **2,308,363 m³** versus the Table 19 total of **2,315,138 m³**.

## What the series says

- The AAC was **230,000 m³/yr** in 2009–2010 and **225,000 m³/yr** from 2011 onward.
- The ratio did not decline smoothly after 2017: 2018 rebounded to **93%** of AAC.
- The collapse is concentrated in **2019–2021**: 49%, 47%, and 30% of AAC.
- Since 2011 the average realized harvest is **197,219 m³/yr**, about **80%** of AAC. That is the figure in the data package text.
- The declining ratio is therefore mostly **undercut relative to a fixed AAC**, not an AAC decline. Figure 4 alone cannot attribute the undercut to caribou, markets, mill capacity, wildfire, or operations.

The figure’s dashed AAC line is drawn at about 225,000 m³/yr across the whole plot, including 2009–2010 when the AAC was 230,000. Table 19 is the correct AAC series.

The provisional 2022–2026 points change the story after 2021: harvest rebounds to 123,835 m³ in 2022, falls to 95,521 m³ in 2023, then rises to 130,930 m³ in 2024 and 187,750 m³ in 2025. The 2026 value is 107,110 m³ for January–September only. That pattern is consistent with a COVID/operational shock in 2020–2021 followed by an incomplete recovery, not a permanent step down caused by caribou policy. The 2023 dip and the 2025 strength still need an operational explanation.

## Provisional 2022–2026 HBS points

The 2022 data package ends at 2021. The public HBS **Mark Monthly Scaling History** report was queried for TSA 27, product “Logs”, all billing types, by date of scale. The report’s preview returns one month at a time, so the annual values below are sums of monthly previews:

| Year | Months | Scaled volume (m³) | AAC (m³) | Harvest / AAC | Status |
|---:|---:|---:|---:|---:|---|
| 2022 | 12 | 123,835 | 225,000 | 55% | provisional |
| 2023 | 12 | 95,521 | 225,000 | 42% | provisional |
| 2024 | 12 | 130,930 | 225,000 | 58% | provisional |
| 2025 | 12 | 187,750 | 225,000 | 83% | provisional |
| 2026 | 9 (Jan–Sep) | 107,110 | 225,000 | 48% YTD | provisional, year-to-date |

These are **not yet reconciled to the Table 19 methodology**. As a check, the same HBS query for 2021 returns 72,542 m³ under all billing types, versus 68,608 m³ in Table 19 (about 5.7% high); the difference is likely date-of-scale versus calendar-harvest basis and/or billing-type scope. The 2026 value is January–September only; October 2026 had no preview total when queried. Do not place the 2026 point on a calendar-year chart without labelling it YTD.

The apparent story after 2021 is a partial recovery: 2022 is above 2021, 2023 falls again, then 2024–2025 rise strongly, with 2025 at 83% of AAC.

## Related files

- `runtime/document_ingestion/tsa27-dp2022-fig4/figure4_recovered.csv` — raw recovered values.
- `runtime/document_ingestion/tsa27-dp2022-fig4/figure4_validated.csv` — recovered versus Table 19.
- `runtime/document_ingestion/tsa27-dp2022-fig4/figure4_harvest_raw.csv` — figrecover bar output.
- `runtime/document_ingestion/tsa27-dp2022-fig4/figure4_aac_raw.csv` — figrecover line output.
- `runtime/document_ingestion/tsa27-dp2022-fig4/hbs_monthly/hbs_monthly_scaled_volume_all_billing.csv` — monthly HBS preview totals.
- `runtime/document_ingestion/tsa27-dp2022-fig4/hbs_annual_scaled_volume_2022_2026.csv` — provisional annual 2022–2026 series.
- `runtime/document_ingestion/tsa27-dp2022-fig4/tsa27_scaled_volume_2009_2026.csv` — complete chart series with published/provisional status.
- `runtime/document_ingestion/tsa27-dp2022-fig4/manifest.json` — render, crop, calibration, and validation metadata.
