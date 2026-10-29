#!/usr/bin/env python3
"""Fetch public cutblock and fire layers for the 2017-2026 annual snapshots.

The BCGW WFS endpoints cap a single response, so this script pages by ``startIndex``.
It fetches the TSA 27 bounding box once; the snapshot builder filters by year and clips to
the TSA boundary.

Usage:
    python scripts/fetch_annual_snapshot_layers.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/downloads/bc"
BBOX = "-119.3,50.6,-117.3,52.4,EPSG:4326"
LAYERS = {
    "cutblocks_tsa_bbox": (
        "https://openmaps.gov.bc.ca/geo/pub/WHSE_FOREST_VEGETATION."
        "VEG_CONSOLIDATED_CUT_BLOCKS_SP/ows",
        "WHSE_FOREST_VEGETATION.VEG_CONSOLIDATED_CUT_BLOCKS_SP",
    ),
    "fire_perimeters_tsa_bbox": (
        "https://openmaps.gov.bc.ca/geo/pub/WHSE_LAND_AND_NATURAL_RESOURCE."
        "PROT_HISTORICAL_FIRE_POLYS_SP/ows",
        "WHSE_LAND_AND_NATURAL_RESOURCE.PROT_HISTORICAL_FIRE_POLYS_SP",
    ),
}


def fetch_layer(url: str, type_name: str, page_size: int = 5000) -> dict[str, Any]:
    """Fetch every feature in the TSA bounding box.

    Parameters
    ----------
    url : str
        WFS endpoint.
    type_name : str
        WFS type name.
    page_size : int
        Features requested per page.

    Returns
    -------
    dict
        A GeoJSON FeatureCollection with heterogeneous keys.
    """
    features: list[dict[str, object]] = []
    start = 0
    while True:
        params: dict[str, str | int] = {
            "service": "WFS",
            "version": "2.0.0",
            "request": "GetFeature",
            "typeName": type_name,
            "outputFormat": "application/json",
            "bbox": BBOX,
            "count": page_size,
            "startIndex": start,
        }
        response = requests.get(url, params=params, timeout=300)
        response.raise_for_status()
        payload = response.json()
        page = payload.get("features", [])
        features.extend(page)
        print(f"{type_name}: fetched {len(features):,}", flush=True)
        if len(page) < page_size:
            break
        start += page_size
    return {"type": "FeatureCollection", "features": features}


def main() -> None:
    """Fetch the cutblock and fire layers and write GeoJSON."""
    OUT.mkdir(parents=True, exist_ok=True)
    for name, (url, type_name) in LAYERS.items():
        payload = fetch_layer(url, type_name)
        path = OUT / f"{name}.geojson"
        path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
        print(f"wrote {path} ({len(payload['features']):,} features)")


if __name__ == "__main__":
    main()
