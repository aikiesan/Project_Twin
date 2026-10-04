"""Export Sentinel-2 NDVI/B11/B8A time series per unit (parcel or H3 cell) from Earth Engine.

Feeds ``engine.supply.harvest_detect.detect_panel``. Untested in CI (needs an authenticated
Earth Engine account: ``pip install earthengine-api && earthengine authenticate``).

Usage (example)::

    python scripts/gee/export_s2_timeseries.py \
        --units-asset projects/<your-project>/assets/cane_h3_res8_catchment_X \
        --start 2023-04-01 --end 2024-04-01 --unit-id-prop h3_index \
        --drive-folder engine_s2 --description s2_ts_catchmentX_2023

Choices to confirm before production use (log them in the run notes):
- Collection ``COPERNICUS/S2_SR_HARMONIZED`` (L2A surface reflectance, harmonised baseline).
- Cloud mask from the Scene Classification Layer (SCL). ``--scl-mask`` lists SCL classes to drop;
  the default below follows the ESA SCL legend (3 cloud shadow, 8/9 cloud medium/high
  probability, 10 thin cirrus) — verify against the current ESA product spec.
- Scale 20 m (native for B8A/B11; B4/B8 are resampled).
"""

from __future__ import annotations

import argparse


def build_collection(ee, region, start: str, end: str, scl_mask: list[int]):
    """Masked S2 L2A collection with NDVI, B11 and B8A bands (reflectance scaled 0–1)."""

    def prep(img):
        scl = img.select("SCL")
        bad = scl.eq(scl_mask[0])
        for c in scl_mask[1:]:
            bad = bad.Or(scl.eq(c))
        refl = img.select(["B4", "B8", "B8A", "B11"]).divide(10000)
        ndvi = refl.normalizedDifference(["B8", "B4"]).rename("ndvi")
        out = ndvi.addBands(refl.select(["B11", "B8A"], ["b11", "b8a"]))
        return out.updateMask(bad.Not()).copyProperties(img, ["system:time_start"])

    return (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(region)
        .filterDate(start, end)
        .map(prep)
    )


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--units-asset", required=True, help="FeatureCollection asset of units")
    ap.add_argument("--unit-id-prop", required=True, help="property holding the unit id")
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--scale", type=float, default=20.0)
    ap.add_argument("--scl-mask", type=int, nargs="+", default=[3, 8, 9, 10])
    ap.add_argument("--drive-folder", required=True)
    ap.add_argument("--description", required=True)
    ap.add_argument("--project", help="Earth Engine cloud project id")
    args = ap.parse_args(argv)

    import ee  # imported lazily so the engine does not depend on earthengine-api

    ee.Initialize(project=args.project) if args.project else ee.Initialize()
    units = ee.FeatureCollection(args.units_asset)
    col = build_collection(ee, units.geometry(), args.start, args.end, args.scl_mask)

    def per_image(img):
        date = ee.Date(img.get("system:time_start")).format("YYYY-MM-dd")
        stats = img.reduceRegions(collection=units, reducer=ee.Reducer.mean(), scale=args.scale)
        return stats.map(
            lambda f: ee.Feature(
                None,
                {
                    "unit_id": f.get(args.unit_id_prop),
                    "date": date,
                    "ndvi": f.get("ndvi"),
                    "b11": f.get("b11"),
                    "b8a": f.get("b8a"),
                },
            )
        )

    table = col.map(per_image).flatten().filter(ee.Filter.notNull(["ndvi"]))
    task = ee.batch.Export.table.toDrive(
        collection=table,
        description=args.description,
        folder=args.drive_folder,
        fileFormat="CSV",
        selectors=["unit_id", "date", "ndvi", "b11", "b8a"],
    )
    task.start()
    print(f"Started EE export task {task.id} -> Drive/{args.drive_folder}/{args.description}.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
