# TSA 27 (Revelstoke) — TSR corpus analysis and WS4 model design

**Prepared:** 2026-10-27 **Scope:** BC Timber Supply Review (TSR) documents for the Revelstoke Timber Supply Area (TSA 27), plus a proposed FEMIC → WS4 model-building pipeline. **Evidence basis:** the 19-document TSR corpus described in §2 (18 documents from the BC TSR FTP catalogue, 1994–2010, plus the September 2022 TSR data package). The answers in §5 are drawn **only** from that corpus. The appendices are design proposals, not TSR findings.

---

## 1. Questions

**Q1. What TSR cycles exist for TSA 27, and which is the latest?** What documents are available, what is the latest completed analysis/AAC, and what is the status of the current cycle?

**Q2. Are caribou constraints documented in the TSR process, and how do they change over time?** For each cycle, what caribou objective, legal instrument, spatial layer, and modelling treatment is documented?

**Q3. In the latest completed TSR (TSR4, 2010), is caribou “just one of many THLB netdown steps”, or is the expression of caribou habitat constraint more complex?** Where does caribou sit in the land-base accounting, and does the model also apply seral, deferral, or spatial constraints?

**Q4. In the current 2022 TSR data package, how is caribou intended to be modelled?** Is it still a netdown, or has the treatment changed? What is the proposed sensitivity?

**Q5. Which forest-estate models were used — Patchworks, SPADES, or something else?** For each cycle, which model is named in the documents?

**Q6. What quantitative harvest/AAC effects are documented?** What do the TSR analyses and sensitivities say about the magnitude of the caribou effect?

**Q7. What does the TSR record imply for a WS4 model that must answer “what is the impact of caribou constraints on AAC in the Revelstoke TSA”?** Which policy layers must be represented, and which counterfactuals are defensible?

---

## 2. Corpus and method

### 2.1 Documents

| Cycle | Documents | Status |
|---|---:|---|
| TSR1 1994 | 5 | Scanned PDFs; no text layer (not machine-searchable) |
| TSR2 1999 | 6 | Text-readable; includes rationale, data package, analysis report |
| TSR3 2005 | 4 | Text-readable; includes rationale, data package, analysis report |
| TSR4 2010 | 3 | Text-readable; includes TSR4 data package, analysis report, AAC rationale |
| TSR5 2022 | 1 | Text-readable; **data package only** — base case and AAC not yet published |

The 2022 package is published on the `www2.gov.bc.ca` TSR asset path, not in the FTP TSA folder. The FTP folder still contains only the four older cycles.

### 2.2 Resolution and indexing

The corpus was resolved and materialized with FEMIC:

- `femic tsr index` — catalogue resolution (the full-catalogue crawl timed out on the BC FTP directory listings; the canonical inventory already in the FEMIC checkout was used and the live Revelstoke folder was checked directly).
- `femic tsr fetch --tsa 27` — 18/18 FTP documents downloaded, 0 failures.
- The 2022 data package was downloaded separately and added to the instance corpus.
- `femic tsr extract --tsa 27` — **1,970 candidate facts** from 19 documents, 0 failures.
- `femic tsr facts-report` — review CSVs for `thlb_reference` (1,139 rows) and `source_layer_candidate` (96 rows).
- A local SQLite/FTS5 index was built over the facts and page text for querying.

### 2.3 Limits

- The 1994 cycle is image-only; it could not be decompiled. The 1999–2022 cycles carry the caribou policy narrative.
- The 2022 document is a **pre-analysis data package**, not a completed base case. It gives assumptions and proposed sensitivities, not results.
- The FEMIC THLB recipe builder did not reconstruct the multi-column TSR netdown tables; the netdown sequences in §3 were transcribed directly from the PDF tables.
- Page numbers below are **PDF pages**, not printed page numbers.

---

## 3. What the TSR documents say

### 3.1 TSR2 — 1999: caribou as forest-cover constraints

Sources: AAC Rationale (`27ts99ra.pdf`) p36; Public Discussion Paper (`27ts98pdp.pdf`) p5; Timber Supply Analysis Report (`27ts98ar.pdf`) p111.

- Caribou zone: **32,979 ha = 48.7% of the THLB**.
- Forest-cover requirements: at least **40%** of the operable area older than **140 years**, **10%** older than **250 years**, and no more than **25%** in stands less than 2 m tall.
- Model: **FSSIM v2.2** (BC Forest Service Simulator), described in the rationale as “spatially implicit” and contrasted with ATLAS (spatially explicit).
- Sensitivity: removing all caribou guidelines allowed the current AAC to be maintained for eight decades before declining to a long-term level of **172,000 m³/yr**, **8.2% higher** than the base case. The rationale rejects this as a management option because it would put caribou and biodiversity at high risk.

Caribou was **not a land-base netdown** in TSR2; the area stayed in the THLB and the constraint operated through seral percentages.

### 3.2 TSR3 — 2005: LU/BEC seral constraints + immature deferral

Sources: AAC Rationale (`27ts05ra.pdf`) p40; Timber Supply Analysis Report (`27ts04ar.pdf`) pp41, 43, 143.

- Caribou habitat: **72,210 ha** of productive Crown forest, **35,050 ha of THLB** (**45% of the THLB**, down from 49% in 1998).
- Below the caribou line: minimum **40%** of the forested area in age class 8+ (**≥140 years**), and at least **one quarter of those older stands** in age class 9+ (**>250 years**).
- Above the caribou line: minimum **70%** in age class 8+ (**≥140 years**).
- Objectives applied **by landscape unit and BEC zone**, on slopes <80%.
- Immature caribou patches: **no harvesting for the first 80 years**, then grouped with like habitat and the same cover requirements applied.
- Intermediate caribou habitat: old/mature seral objectives from the intermediate biodiversity emphasis option; a sensitivity showed a **1.8% decrease** in long-term timber supply.
- Model: **FSSIM v4.2**.
- Operational expression: increased **patch/group selection** in the caribou zone to retain wildlife trees and patches (p143).

Again, caribou was a **constraint on harvest**, not a netdown; the area remained in the THLB.

### 3.3 TSR4 — 2010: legal spatial reserves (netdown) + residual biodiversity constraints

Sources: TSR4 Data Package (`Revelstoke_TSR4_Data_Package_23_Nov_09.pdf`) pp13, 23, 25; TSR4 Analysis Report (`Revelstoke_TSR4_Analysis_Report_23_Feb_10.pdf`) pp6, 24, 33, 42, 57, 60, 76; AAC Rationale (`27ts11ra.pdf`) pp9–10, 20–21, 26.

- Legal instrument: GAR Order **U-3-005**, in effect 2009, amended 2010. It established spatially explicit caribou reserves combining:
- **status quo** reserves previously required under the Revelstoke Higher Level Plan (14,794 ha of the reserve area),
- **incremental** “no harvest” reserves recommended by the Species at Risk Coordination Office (4,077 ha), and
- inoperable areas that also function as caribou habitat.
- Land-base treatment: **100% removal from the THLB**; **66,098 ha** productive forest, **18,909 ha effective netdown** (3.6% of the TSA; 8.0% of the CFLB).
- The TSR4 analysis says the caribou reserves tie up **~7.76 million m³** and that the netdown elements that reduced the THLB “were dominantly concentrated in mature and old stands” (pp33, 42).
- THLB: **57,908 ha**, down **20,110 ha (25.8%)** from TSR3's 78,018 ha. Caribou is the largest driver; the incremental reserves alone account for 4,077 ha. The “status quo” portion is 14,794 ha; the effective TSR3→TSR4 comparison is 63,224 → 57,908 ha (−5,316 ha, −8.4%) (p42).
- Residual interaction: mature+old biodiversity requirements under the HLPO still applied in the caribou landscape units north of Revelstoke. The sensitivity “No Mature Biodiversity in Caribou LU's” removed them and raised:
- short-term harvest **+4.0%** to 215,500 m³/yr,
- mid-term low **+4.0%** to 141,400 m³/yr,
- long-term level **+2.5%** to 246,500 m³/yr, with **no THLB change** (p57).
- Incremental-reserve sensitivity: adding the 4,076 ha back to the THLB (57,908 → 61,984 ha, +7%) raised initial harvest **+8.4%** to 224,500 m³/yr, mid-term **+8.4%** to 147,300 m³/yr, and the long-term level **+2.2%** to 244,800 m³/yr one decade later (p60).
- Model: **FPS-ATLAS v6.0.2.0** (Forest Planning Studio, John Nelson, UBC), a spatially explicit **simulation** model with harvest-priority queues and clique constraints.
- AAC outcome: base case initial 207,100 m³/yr, mid-term low 135,900 m³/yr, long-term 240,500 m³/yr; the Chief Forester set the AAC at **225,000 m³/yr** effective 28 July 2011.

### 3.4 TSR5 — 2022: legal UWR exclusion + core/matrix recovery sensitivity

Source: *Revelstoke TSA Data Package*, September 2022 (`27ts_dp_2022.pdf`), 88 pp.

- **Status:** current TSR data package; pre-analysis. The base case and AAC results are not yet published in this document.
- **Model:** **STSM2022**, implemented in **SELES10** (Spatially Explicit Landscape Event Simulator), a 1-hectare raster spatial model (p75).
- **Caribou overlap:** “Revelstoke TSA is almost entirely overlapped by caribou habitat. This is the most overlap of any TSA in the province” (p60, Figure 11).
- **Six herds** (Table 27, p61):
- Central Rockies — 3 (2008) — extirpated
- Columbia North — 184 (2021) — increasing
- Columbia South — 4 (2020) — decreasing
- Frisby Boulder — 6 (2020) — decreasing
- Groundhog — 34 (2021) — stable
- Monashee — 1 (2016) — extirpated
- **Legal protection:** UWR **u-3-005** was established under the GAR on 9 December 2009 (the TSR4 documents say it was in effect 12 February 2009; treat the exact date as a documentary inconsistency), with boundary amendments in **2010, 2014, and 2020**. It prohibits timber harvesting and road construction (with narrow exceptions) and restricts mineral exploration and guided adventure tourism. It protects about **34% of the herd habitat** within the TSA (p61).
- **Base-case land-base treatment:** all UWR areas are removed from the **LHLB** — a legal no-harvest exclusion, not merely a THLB netdown. Table 12 (p33) shows **116,820 ha gross** caribou UWR, all excluded from the LHLB; Table 14 (p35) shows **62,892 ha net removed**, **29.1% of the AFLB**. Table 14's THLB is **51,454 ha** (preliminary, as of July 2022).
- **Proposed caribou-recovery sensitivity:** all “core” caribou habitat (high and low elevation) set to **no harvest**, and all “matrix” habitat given a forest-cover constraint of **maximum 13% of total area less than 40 years old** (intended to approximate <35% disturbance from forestry and low wolf densities). Core and matrix locations follow the provincial caribou recovery program definition (pp61, 77). This is **not** in the base case; it is a sensitivity testing the more aggressive recovery direction.
- **Harvest context:** current AAC 225,000 m³/yr (since 2011). Realized harvest has generally been below AAC. The package reports both “approximately 80% … 179,000 m³/yr” (p11) and a **197,219 m³/yr** average realized since 2011 (pp45–46); the 197,219 figure is used as the base-case initial rate (p75). The two statements are internally inconsistent; the base-case modelling input is 197,219 m³/yr.

### 3.5 THLB netdown sequences

#### TSR4 2010 (Table 3, Data Package p13)

Cumulative sequence; each row is applied after the rows above it.

| Order | Element | Total (ha) | Effective netdown (ha) | % TSA | % CFLB |
|---:|---|---:|---:|---:|---:|
| 1 | Total area | 833,444 | | | |
| 2 | Less TFLs | 283,006 | | | |
| 3 | Less private land, woodlots | 23,433 | | | |
| 4 | **Total TSA area** | **527,005** | | **100.0** | |
| 5 | Non-forest / non-productive | 286,995 | 286,995 | 54.5 | |
| 6 | Non-commercial brush | 108 | 108 | 0.0 | |
| 7 | Unclassified roads/trails/landings | 9,806 | 3,777 | 0.7 | |
| 8 | **CFLB** | **236,126** | | **44.8** | **100.0** |
| 9 | Parks and reserves | 31,094 | 19,310 | 3.7 | 8.2 |
| 10 | Specific geographic areas | 635 | 635 | 0.1 | 0.3 |
| 11 | Inoperable / inaccessible | 144,715 | 127,252 | 24.1 | 53.9 |
| 12 | Unstable terrain | 57,892 | 2,265 | 0.4 | 1.0 |
| 13 | Environmentally sensitive areas | 23,772 | 944 | 0.2 | 0.4 |
| 14 | Non-merchantable | 2,764 | 1,923 | 0.4 | 0.8 |
| 15 | Low sites | 46,539 | 4,197 | 0.8 | 1.8 |
| 16 | Riparian management areas | 3,129 | 1,616 | 0.3 | 0.7 |
| 17 | Community watersheds | 4,449 | 255 | 0.0 | 0.1 |
| 18 | Drinking water intakes | 59 | 25 | 0.0 | 0.0 |
| 19 | Wildlife habitat areas | 6 | 4 | 0.0 | 0.0 |
| 20 | Permanent sample plots | 264 | 179 | 0.0 | 0.1 |
| 21 | Backlog NSR | 412 | 300 | 0.1 | 0.1 |
| 22 | Cultural heritage | 0 | 0 | 0.0 | 0.0 |
| **23** | **Mountain Caribou Reserves (GAR U-3-005)** | **66,098** | **18,909** | **3.6** | **8.0** |
| 24 | Existing wildlife tree patches | 690 | 404 | 0.1 | 0.2 |
| 25 | **THLB** | | **57,908** | **11.0** | **24.5** |
| 26 | Temporary spatial OGMA/MOGMA | 84,405 | 5,549 | 1.1 | 2.4 |
| 27 | **Effective THLB** | | **52,358** | **9.9** | **22.2** |
| 28 | Future wildlife tree patches | | 215 | 0.0 | 0.1 |
| 29 | Future roads/trails/landings | | 1,100 | 0.2 | 0.5 |
| 30 | **Long-term THLB** | | **51,044** | **9.7** | **21.6** |

#### 2022 TSR5 (Table 14, Data Package p35) — preliminary

Different accounting framework (gross → AFLB → LHLB → THLB); several rows are TBD, and the gross overlays are not additive.

| Step | Gross (ha) | Net removed (ha) | % gross | % AFLB |
|---|---:|---:|---:|---:|
| Gross land base | 758,502 | | | |
| Land not administered for timber supply | 243,648 | 243,325 | 32.13 | |
| Non-forested / non-productive | 407,469 | 294,490 | 53.72 | |
| Roads, pipelines, transmission lines, railways | 11,977 | 4,544 | 1.58 | |
| **AFLB** | **216,217** | | **28.85** | |
| Parks and protected areas | 26,817 | 15,596 | 3.54 | 7.13 |
| **Caribou UWR (no harvest)** | **116,820** | **62,892** | **15.4** | **29.1** |
| WHA (no harvest) | 9 | 3 | 0.0 | 0.0 |
| Protected archaeological sites | 18 | 0 | 0.0 | 0.0 |
| Crown conservation lands | 54 | 11 | 0.01 | 0.01 |
| **LHLB** | **137,726** | | **18.16** | |
| Inoperable areas | 632,867 (overlay) | | 83.44 | 29.78 |
| Low productivity sites | 498,198 (overlay) | | 65.68 | 1.21 |
| Non-merchantable profiles | 85,200 (overlay) | | 11.23 | 6.31 |
| Riparian areas | 23,335 (overlay) | | 3.08 | 1.52 |
| Wildlife tree retention areas | 53,854 (overlay) | | 7.1 | 1.8 |
| **THLB** | **51,454** | | **6.78** | |
| Future reductions / roads | TBD | TBD | TBD | TBD |

### 3.6 Models named in the corpus

| Cycle | Model | Evidence |
|---|---|---|
| TSR2 1999 | **FSSIM v2.2** (BC Forest Service Simulator; spatially implicit) | `27ts98ar.pdf` p111; `27ts99ra.pdf` pp31–32 |
| TSR3 2005 | **FSSIM v4.2** | `27ts04ar.pdf` p43 |
| TSR4 2010 | **FPS-ATLAS v6.0.2.0** (Forest Planning Studio, UBC; spatially explicit simulation) | Analysis Report p27; Rationale p9 |
| TSR5 2022 | **STSM2022 / SELES10** (1-ha raster spatial model) | Data Package p75 |

Full-text search over the 19-document corpus (887 text pages):

- “Patchworks”: **0**
- “SPADES”: **0**
- “FPS-ATLAS”: **5 pages**
- “FSSIM”: **17 pages**
- “STSM2022” / “SELES10”: **1 page each**

### 3.7 Documented quantitative effects

| Scenario | THLB | Short-term | Mid-term | Long-term |
|---|---|---|---|---|
| TSR4 base case (2010) | 57,908 ha | 207,100 m³/yr | 135,900 m³/yr | 240,500 m³/yr |
| TSR4 add back incremental caribou reserves | 61,984 ha (+4,076, +7%) | 224,500 (+8.4%) | 147,300 (+8.4%) | 244,800 (+2.2%, one decade later) |
| TSR4 remove mature+old biodiversity in caribou LUs | unchanged | 215,500 (+4.0%) | 141,400 (+4.0%) | 246,500 (+2.5%) |
| TSR2 remove all caribou guidelines (1999 analog) | — | — | — | 172,000 (+8.2%) |

These are model outputs, not AAC determinations. The 2011 AAC was 225,000 m³/yr.

---

## 4. What is uncertain or inconsistent in the record

1. **1994 is scanned.** No text layer; not decompiled.
2. **The 2022 package is pre-analysis.** It has no base-case or sensitivity results.
3. **TSR4 draft vs final.** The TSR4 data package draft says the THLB dropped 25,660 ha (32.9%); the final analysis report says 20,110 ha (25.8%). Table 3's own numbers imply 20,110. Use the analysis report.
4. **2011 rationale typo.** It says the “current” THLB is 78,018 ha and 20,110 ha smaller than 2004; 78,018 is the TSR3 THLB; TSR4 is 57,908.
5. **UWR date inconsistency.** TSR4 documents say 12 February 2009; the 2022 package says 9 December 2009. The amendment history (2010/2014/2020) is the reliable anchor.
6. **2022 text/table discrepancy.** Text says “approximately 116,830 ha” of caribou UWR (p33); Tables 12 and 14 say 116,820. Use 116,820.
7. **2022 harvest-average inconsistency.** “~80% / 179,000 m³/yr” (p11) vs 197,219 m³/yr (pp45–46, p75). The base-case input is 197,219.
8. **2010 vs 2022 caribou footprints are not directly comparable.** 2010 is against CFLB; 2022 is against AFLB; the UWR boundary was amended in 2010/2014/2020.

---

## 5. Answers (TSR-only)

**A1. What cycles exist, and which is latest?** TSR1 1994, TSR2 1999, TSR3 2005, TSR4 2010, and a 2022 data package for the current cycle (referred to here as TSR5). TSR4 2010 is the latest **completed** analysis and AAC determination (2011, AAC 225,000 m³/yr). The 2022 package is the latest **published data package**; its analysis/base case is still in progress.

**A2. Are caribou constraints documented, and how do they change?** Yes, in every text-readable cycle. TSR2 (1999) and TSR3 (2005) modelled caribou as forest-cover/seral constraints inside FSSIM; the area stayed in the THLB. TSR4 (2010) converted the caribou habitat into legal spatial reserves removed from the THLB, while retaining mature/old biodiversity constraints in the caribou landscape units. The 2022 package treats the UWR as a legal no-harvest exclusion from the LHLB and proposes a core/matrix recovery sensitivity.

**A3. In TSR4, is caribou just a netdown step?** In the formal land-base table, yes — it is one row (66,098 ha productive / 18,909 ha net). But it is the largest single driver of the TSR3→TSR4 THLB reduction (−20,110 ha, −25.8%), it removes mature/old stands disproportionately (~7.76 million m³), and the model still carries mature/old biodiversity constraints in the caribou LUs. Removing those constraints alone raises short/mid-term harvest by 4.0% and the long-term level by 2.5%. So the TSR4 expression is **netdown + residual seral constraint**, not a single land-base subtraction.

**A4. How is caribou intended to be modelled in 2022?** The UWR is a legal no-harvest exclusion from the LHLB: 116,820 ha gross, 62,892 ha net, 29.1% of the AFLB. The base case uses that exclusion. The proposed recovery sensitivity adds a **core no-harvest + matrix max 13% <40 years** constraint. The model is STSM2022/SELES10 at 1-ha resolution. No 2022 results are published yet.

**A5. Patchworks or SPADES?** Neither. The Revelstoke TSRs used **FSSIM** (1999, 2005), **FPS-ATLAS** (2010), and **STSM2022/SELES10** (2022). “Patchworks” and “SPADES” appear zero times in the 19-document corpus.

**A6. What quantitative effects are documented?** The defensible numbers are the TSR4 sensitivities: +8.4% short/mid and +2.2% long-term from adding back the incremental caribou reserves (4,076 ha, +7% THLB); +4.0% short/mid and +2.5% long-term from removing mature+old biodiversity constraints in caribou LUs (no THLB change); and the TSR2 analog of +8.2% long-term if all caribou guidelines are removed. The 2022 package has no results yet.

**A7. What does this imply for WS4?** Caribou cannot be represented as a single static acreage. A WS4 model must be able to toggle: (a) the UWR/core no-harvest exclusion (2020 boundary; 62,892 ha net in 2022, 18,909 ha net in 2010); (b) the matrix habitat constraint (max 13% <40 years) for the current policy direction; (c) the LU/BEC mature+old seral constraints; and (d) the 80-year immature-habitat deferral for the TSR2/TSR3 counterfactual. The TSR4 sensitivities are the best available quantitative validation targets until the TSR5 analysis is published.

---

## Appendix A — Proposed FEMIC → WS4 model-building pipeline

### A.1 Purpose and question

The model must answer: **“What is the impact of caribou habitat constraints on AAC in the Revelstoke TSA?”** It must separate the effect of:

1. the legal UWR no-harvest exclusion,
2. the core/matrix recovery constraint (if testing current policy direction),
3. the LU/BEC mature+old seral constraints, and
4. the 80-year immature-habitat deferral (historical counterfactual).

The pipeline is deliberately layered so each policy can be switched without rebuilding the underlying inventory/yield data.

### A.2 Raw input data sources

| Input | Source | Use |
|---|---|---|
| TSA boundary | BCGW `WHSE_ADMIN_BOUNDARIES.FADM_TSA_SV` (or `FADM_TSA.gdb`) | Clip the case; identify TSA 27 |
| VRI 2025 | BCGW `WHSE_FOREST_VEGETATION.VEG_COMP_LYR_R1_POLY`; `VEG_COMP_VDYP7_INPUT_POLY_AND_LAYER_2025.gdb` | Stand attributes, species, age, site index |
| Site productivity | `Site_Prod_BC.gdb` | Site index / productivity |
| BEC v12 | BCGW `WHSE_FOREST_VEGETATION.BEC_BIOGEOCLIMATIC_POLY` | LU/BEC strata and seral constraints |
| TSA/TSR documents | BC TSR FTP + www2 2022 data package | Policy intent, netdown logic, sensitivities |
| Caribou UWR | BCGW `WHSE_WILDLIFE_MANAGEMENT.WCP_UNGULATE_WINTER_RANGE_SP`, UWR u-3-005 | No-harvest exclusion |
| Caribou core/matrix | Provincial caribou recovery program habitat layers (via the caribou recovery team) | 2022 sensitivity |
| Caribou herd ranges | BC caribou herd locations (provincial caribou recovery team) | Reporting/overlap; not a direct constraint unless using herd-specific zones |
| Landscape units | BCGW `WHSE_FOREST_VEGETATION.FADM_LANDSCAPE_UNIT_SV` (or equivalent) | LU/BEC seral accounting |
| OGMA/MOGMA | BCGW / FSP spatial layers | Old/mature reserves |
| Roads / operability | BCGW road layers, TSR operability line | Harvest priority and operability |
| Cutblocks/disturbance | BCGW `WHSE_FOREST_VEGETATION.VEG_CONSOLIDATED_CUT_BLOCKS_SP` | Current depletion |
| Parks/protected areas | BCGW `WHSE_TANTALIS.TA_PARK_ECORES_PA_SVW` | Land-base exclusions |

The public instance should not vendor raw provincial data. It should provide a fetch script and a manifest, and use the shared `femic-public-data` mirror where available.

### A.3 Pre-processing (FEMIC)

1. **Instance init** — `femic instance init` with a TSA 27 run profile and TIPSY scaffold.
2. **Data preflight** — `femic prep validate-case` with `FEMIC_EXTERNAL_DATA_ROOT` pointing at the public-data mirror.
3. **TSR evidence** — `femic tsr index/fetch/extract/facts-report` for TSA 27; store the candidate facts, review CSVs, and the curated netdown tables.
4. **TSA clip and land base** — clip VRI/site index/BEC to TSA 27; apply the TSR4/2022 land-base sequence (parks, inoperable, unstable/ESA, non-merchantable, low sites, riparian, community watersheds, WHA, PSP, backlog, cultural, caribou UWR, WTP, OGMA/MOGMA).
5. **Analysis units / strata** — build AU/strata from leading species, BEC, site index, and managed/natural status; run VDYP7 for natural stands and TIPSY for managed stands.
6. **Yield curves** — compile natural and managed curves; record the source (TSR/FSP/TIPSY) and the curve version.
7. **Fragments** — build the WS4 fragment layer from the VRI/stand polygons, with attributes: area, AU, age, site index, species, THLB flag, caribou zone flags (UWR/core/matrix), LU/BEC, OGMA/MOGMA, operability, road distance.
8. **Compile** — write the WS4 dataset (tracks, curves, treatments, features/products) plus a manifest and provenance.

### A.4 WS4 model structure

- **Fragments** are the decision units; **blocks** are a runtime aggregate.
- **Tracks** carry the stand/AU, age, site index, and eligibility.
- **Curves** carry natural and managed volume/merchandise by age.
- **Treatments** carry harvest and silviculture eligibility; operability is the intersection of fragment eligibility within a block.
- **Features/products** carry habitat and volume accounts:
- `caribou_uwr_ha`, `caribou_core_ha`, `caribou_matrix_ha`
- `age_lt_40_ha` (matrix)
- `old_seral_ha`, `mature_old_seral_ha` by LU/BEC
- `harvested_volume`, `area_by_age_class`
- **Constraints** are expressed as accounts/targets over fragments/blocks by zone and period.

### A.5 How to model caribou policies in WS4 to match STSM

The 2022 STSM design is the best available guide, but it is not yet published as results. The proposed implementation is:

**1. UWR / core no-harvest exclusion (base case + core sensitivity)**

- Spatially join UWR u-3-005 (2020 amendment) and the provincial core habitat layer to the fragment layer.
- Mark fragments as `caribou_uwr = 1` / `caribou_core = 1`.
- Remove them from the harvestable land base (or set harvest eligibility to zero) for the entire horizon. This matches STSM's “no harvest” treatment.
- Report the excluded area and volume separately so the netdown can be reconciled with the TSR table (116,820 ha gross / 62,892 ha net in 2022; 66,098 / 18,909 in 2010).
- For the core sensitivity, add the core habitat to the same exclusion set; for the base case, only the legal UWR is excluded.

**2. Matrix habitat constraint (max 13% <40 years)**

- Spatially join the provincial matrix habitat layer to fragments.
- Create an account `matrix_area_lt_40` and `matrix_area_total` by matrix zone (and by LU if the layer nests).
- At each period, constrain `matrix_area_lt_40 / matrix_area_total <= 0.13`.
- Use the harvested/stand-age state at the period midpoint, matching STSM's age-class accounting. If WS4 evaluates constraints at period boundaries, use the same age definition (stand age <40 at the evaluation year) and document the choice.
- This is a **cover constraint**, not a land-base removal; matrix fragments remain eligible.

**3. LU/BEC mature+old seral constraints**

- Create accounts `old_seral_ha` and `mature_old_seral_ha` by LU/BEC (or NDT/BEC/BEO if the TSR target is defined that way).
- Apply the RHLPO targets used in the base case: 40% ≥140 years and 25% of those ≥250 years below the caribou line; 70% ≥140 years above; plus the mature+old biodiversity targets in the caribou LUs (the TSR4 sensitivity removes these).
- If the 2022 TSR changes the target basis (BEC v12, old-growth deferrals), version the target table and keep the 2010/2022 variants separate.

**4. Immature-habitat deferral (historical counterfactual)**

- For the TSR2/TSR3 counterfactual, mark immature caribou habitat and set harvest eligibility to zero for the first 80 years; after year 80, release it and apply the relevant seral constraints.
- This is a time-varying eligibility rule, not a static exclusion.

**5. Harvest priority and spatial behaviour**

- STSM 2022 uses a stand preference function based on highest volume/ha, lowest cycle time, and closest distance to existing/projected road. WS4 should emulate this in the base-case scenario (or document a deliberate difference).
- STSM applies adjacency/green-up and patch-size constraints; WS4 should use its spatial adjacency and green-up features with the same parameters where documented.
- STSM is a simulation (priority queue), not an optimizer. For comparability, run WS4 in simulation mode first; use optimization only for policy exploration, clearly labelled.

**6. Scenario matrix**

| Scenario | UWR | Core | Matrix 13% <40 yr | Mature/old seral | Immature deferral |
|---|---|---|---|---|---|
| S0 TSR4 base (2010) | yes (2010 boundary) | no | no | yes | no |
| S1 TSR4 + incremental reserves back | partial | no | no | yes | no |
| S2 TSR4 no mature biodiversity in caribou LUs | yes | no | no | no (caribou LUs) | no |
| S3 TSR5 base (2022) | yes (2020 boundary) | no | no | yes | no |
| S4 TSR5 recovery sensitivity | yes | yes | yes | yes | no |
| S5 TSR3-style historical | zone | no | no | yes | yes (80 yr) |
| S6 no caribou constraints | no | no | no | as base | no |

**7. Validation**

- Reconcile the WS4 land base against the TSR tables (gross/AFLB/LHLB/THLB; caribou netdown; OGMA/MOGMA; WTP).
- Compare harvest flow against the TSR4 base case and sensitivities; report the deltas in the same units (m³/yr, %).
- Check the matrix constraint: report the percentage <40 years by period and zone; it must not exceed 13% in S4.
- Check the core/UWR exclusion: no harvest in those fragments in any period.
- Check the age-class distribution and old/mature seral targets by LU/BEC.
- Record the WS4 version, dataset manifest, scenario config, seed, and run ID.

### A.6 Outputs

- `dataset/` — compiled WS4 dataset + manifest.
- `scenarios/` — one YAML/CSV per scenario.
- `runs/` — simulation/optimization outputs, logs, and summaries.
- `reports/` — land-base reconciliation, harvest-flow comparison, caribou-constraint attribution, and sensitivity tables.
- `docs/` — data provenance, assumptions, and limitations.

### A.7 Risks and unknowns

- The 2022 STSM base case and core/matrix results are unpublished; the WS4 implementation is a best guess from the data package, not a replication.
- UWR/core/matrix layers may have different vintages and boundary versions; record the version used and test sensitivity to the 2010 vs 2020 boundary.
- The TSR4 and 2022 land-base bases differ (CFLB vs AFLB); reconciliation must harmonize them.
- Provincial data licensing and redistribution: do not vendor raw data in the public repo; use the fetch script and the shared mirror.
- The 1994 TSR is not machine-readable; any claim about TSR1 is limited to the 1999 retrospective.

---

## Appendix B — Detailed model-building plan

The plan is organized as phases in the public instance repository. Each phase is one parent issue and one feature branch; each task is one child issue. The repo follows the `ubc-fresh-dev-workflow` contract and the `femic` / `ws4` project rules.

### P0 — Bootstrap the public instance repository

- **P0.1** Render the UBC-FRESH workflow seed and initialize the FEMIC instance (`femic instance init`), with TSA 27 run profile and TIPSY scaffold.
- **P0.2** Add the TSR corpus evidence: document inventory, facts, curated netdown tables, evidence CSV, and the TSR analysis report (sanitized; no raw PDFs in git).
- **P0.3** Add the WS4 model-building plan, scenario definitions, and data-source manifest.
- **P0.4** Add fetch/validation scripts for the public data and TSR corpus; add CI checks.
- **P0.5** Add docs (README, data provenance, assumptions, limitations) and the green dashboard.

**Exit:** repo is public, CI green, docs build, `femic prep validate-case` passes with the public-data mirror, and the report/plan are reviewed.

### P1 — Materialize public inputs

- Fetch/verify VRI 2025, TSA boundary, site productivity, BEC v12, UWR/core/matrix, LU, OGMA/MOGMA, roads, cutblocks.
- Clip to TSA 27; build the land-base layer and the caribou zone flags.
- Record checksums, versions, and provenance.

**Exit:** a reproducible input manifest; land-base totals reconcile with the TSR tables within a stated tolerance.

### P2 — Compile FEMIC model inputs

- Build AUs/strata; run VDYP7 natural and TIPSY managed curves.
- Compile the THLB/land-base checkpoint and the yield tables.
- Validate against TSR4/2022 published areas and curves.

**Exit:** FEMIC model-input bundle with a manifest and QA report.

### P3 — Build the WS4 dataset

- Build fragments with caribou/LU/BEC/OGMA attributes.
- Compile tracks, curves, treatments, features/products.
- Write the dataset manifest and a land-base reconciliation report.

**Exit:** WS4 dataset loads; accounts and constraints are inspectable; base-case simulation runs.

### P4 — Caribou policy scenarios and AAC analysis

- Implement S0–S6 scenarios (Appendix A.5).
- Run simulation (and optimization where useful) with fixed seeds.
- Compare harvest flow, AAC, land base, age-class, and matrix disturbance.
- Attribute the AAC effect to UWR, core/matrix, seral, and deferral.

**Exit:** scenario table with deltas, validation against TSR4/2022 evidence, and a written uncertainty assessment.

### P5 — Publish and release

- Write the final report, docs, and figures.
- Add the instance as a submodule under `femic/external/femic-tsa27-instance`.
- Tag a release after review; archive the dataset manifest and run IDs.

**Exit:** public release with reproducible commands, evidence, and limitations.

---

## Appendix C — Repository layout (proposed)

```
femic-tsa27-instance/
├── AGENTS.md                     # workflow + domain contract
├── ROADMAP.md                    # phases P0–P5
├── CHANGE_LOG.md
├── README.md
├── config/
│   ├── run_profile.tsa27.yaml
│   ├── tipsy/tsa27.yaml
│   └── tsr/                      # source-layer and THLB recipes
├── data/
│   ├── downloads/                # ignored; fetch scripts write here
│   └── tsr/corpus/               # ignored; public TSR PDFs fetched here
├── docs/
│   ├── index.rst
│   ├── data-provenance.rst
│   ├── assumptions.rst
│   └── limitations.rst
├── metadata/
│   ├── tsr/                      # inventory, facts, curated tables
│   └── data_manifest.yaml
├── notes/
│   ├── adr/
│   ├── plans/tsa27-model-build-plan.md
│   └── reports/
├── reports/
│   └── tsa27-tsr-corpus-analysis.md
├── scenarios/
│   └── s0..s6.yaml
├── scripts/
│   ├── fetch_public_data.sh
│   ├── fetch_tsr_corpus.sh
│   ├── build_facts_index.py
│   └── search_tsr.py
└── tests/
```
