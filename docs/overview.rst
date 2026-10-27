Overview
========

This repository is a public FEMIC deployment instance and WS4 model case for the Revelstoke
Timber Supply Area (TSA 27) in British Columbia.

The project answers one question:

    What is the impact of caribou habitat constraints on AAC in the Revelstoke TSA?

It does so by separating four policy layers:

1. the legal UWR / core no-harvest exclusion,
2. the matrix habitat constraint (maximum 13% of area younger than 40 years),
3. the LU/BEC mature and old seral constraints, and
4. the historical 80-year immature-habitat deferral.

The evidence base is a 19-document Timber Supply Review corpus: TSR1 1994, TSR2 1999, TSR3
2005, TSR4 2010, and the September 2022 TSR5 data package. The analysis is in
``reports/tsa27-tsr-corpus-analysis.md``; the implementation plan is in
``notes/plans/tsa27-model-build-plan.md``.

The instance is standalone: it installs, validates, and documents itself without a parent
checkout. The FEMIC repository links it as a submodule at
``external/femic-tsa27-instance``.
