# TSA 27 mill capacity context

**Status:** public-data baseline plus dated operating-status screen, 29 October 2026.
**Not a current throughput or curtailment series.**

## National design-capacity dataset

The CLEWS/CFS national Mills DB provides design capacities in m3/year for the local mills:

| Facility code | Ownership | Location | Design capacity |
|---|---|---|---:|
| BC-SAW418 | Downie Timber Ltd. and Selkirk Cedar | Revelstoke | 471,528 m³/yr |
| BC-SAW416 | Eagle River Industries Inc. | Malakwa | 235,764 m³/yr |

Total local design capacity is **707,292 m³/yr**, about **3.1× the 225,000 m³/yr AAC**. That
means mill capacity is not the binding constraint at the TSA aggregate scale under these
figures. The binding constraints are more likely access, cost, product mix, operating status,
and demand allocation.

Source: `config/operational/mills_design_capacity.csv`; national Mills DB via CLEWS. Capacity
is design capacity, not current throughput, and should be paired with dated curtailments.

## 2019 baseline

The BC Major Primary Timber Processing Facilities 2019 report lists the following lumber
mills in or near TSA 27:

| Mill | Location | 2019 capacity (MMBF) |
|---|---|---:|
| Gorman Brothers / Downie Timber | Revelstoke | 117.0 |
| Joe Kozek Sawmills | Revelstoke | 9.6 |
| Greenslide Cattle | Revelstoke | 1.0 |
| Take to Heart Specialty Wood | Revelstoke | 0.7 |
| Alan Hyde Sawmill | Sicamous | 7.2 |

Total listed local lumber capacity is about **135.5 MMBF**. This is a 2019 nameplate
capacity, not current throughput, and not a log-demand figure. MMBF is lumber output; it
cannot be converted to log volume without a documented recovery factor by mill and product.

Source: `config/operational/mills_2019.csv`; BC Major Primary Timber Processing Facilities
2019, pages 40–43.

## Operating-status check

The national design table is not a current operating list. The BC Major Primary Timber
Processing Facilities reports for 2019, 2022, and 2023 list Gorman Brothers / Downie Timber in
Revelstoke, but do **not** list Eagle River Industries in Malakwa as an operating major mill.

| Mill | Design capacity | Public status | Evidence |
|---|---:|---|---|
| Downie Timber / Selkirk Cedar | 471,528 m³/yr | Active | Gorman Group hosted a federal tour at the Revelstoke facility in August 2025; current supplier listing |
| Eagle River Industries | 235,764 m³/yr | Unverified / not listed | Absent from the 2019, 2022, and 2023 BC mill-list reports; no current company listing found |

This does not prove Eagle River is permanently closed. It does mean the model should not
assume its design capacity is operating. The public baseline is now split:

| Capacity case | m³/yr | Multiple of AAC |
|---|---:|---:|
| Both design mills | 707,292 | 3.14× |
| Downie only | 471,528 | 2.10× |
| Eagle River only | 235,764 | 1.05× |

Even the smaller design mill is above the 225,000 m³/yr AAC, and Downie alone is about 2.1×.
At TSA aggregate scale, mill **volume** capacity is not binding in any single-mill case. The
remaining mill constraints are product acceptance, grade/species mix, sawmill recovery, and
current operating shifts.

Provincial reporting and industry announcements document more than 30 BC sawmill closures
since 2017, with further closures and curtailments through 2025–2026. That is provincial
context, not a TSA 27-specific curtailment series. No dated Downie curtailment or closure
notice was found for 2024–2026; absence of a notice is not proof of full operation.

The status register is `config/operational/mill_status.csv`. The known-event register is
`config/operational/mill_curtailments.csv`:

| Mill | Date | Event | Evidence |
|---|---|---|---|
| Downie/Selkirk | 2019-09-03 | 8-shift curtailment | Revelstoke Mountaineer, 2019-08-19 |
| Downie/Selkirk | 2024–2026 | No public notice found | Public news and company listing search |
| Eagle River | 2023-12-31 | Not listed | BC major-mill reports 2019/2022/2023 |

This is not a complete curtailment series. It records what the public record supports and
what remains unknown.

## What this means for the model

The existing pilot uses two **notional** mills with equal demand. That is not a capacity
model. To make mill capacity binding we need:

1. a current mill list with product acceptance and capacity;
2. a documented conversion from product output to log demand;
3. dated closures, curtailments, and restart dates;
4. destination-specific prices and haul eligibility.

Until then, the screen's 45% positive-margin share is an **economic-accessibility** result,
not a mill-constrained result.

## One-mill pilot check

The 45-block FHOPS pilot was re-solved with Revelstoke as the only destination:

| Case | Volume | Net objective | Road-related cost |
|---|---:|---:|---:|
| Two mills | 65,206 m³ | 0.678M | 0.137M |
| Revelstoke only | 66,439 m³ | 0.748M | 0.142M |

The one-mill case is slightly larger and more profitable because it avoids the long Malakwa
haul. That is consistent with design capacity: Downie alone is 2.10× AAC, so mill volume is
not binding in the pilot.

## Next

- Verify Eagle River's closure date and any restart from a current Ministry or company source.
- Obtain product-level capacity and log-input conversion.
- Build a dated curtailment table for Downie/Selkirk from public notices.
- Re-run the FHOPS facility demand with the one-mill and two-mill cases.

## Files

- `config/operational/mill_status.csv`
- `config/operational/mills_2019.csv`
- `config/operational/mill_curtailments.csv`
- `reports/tsa27-operational-screen.md`
- `reports/tsa27-operational-pilot.md`
