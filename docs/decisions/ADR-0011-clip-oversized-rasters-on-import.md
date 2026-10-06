# ADR-0011 — Clip oversized rasters to SP on import, with a provenance manifest

- **Status:** Accepted
- **Date:** 2026-10-05
- **Deciders:** project lead (Lucas)

## Context
The walking skeleton (ADR-0010) needs annual 30 m land cover for São Paulo, to compute sugarcane area per H3 cell (`cane_area_h3`). The project PC holds the MapBiomas national mosaics for 2008–2024 in `Documents/ILUC_NIPE` (ABIOVE project), at about 0.8 GB per year and 13 GB in total.

CLAUDE.md rule 4 says that `data/raw/` holds immutable copies written only by import scripts. Copying 13 GB of Brazil-wide rasters would break the manual Drive backups (ADR-0009), even though the engine uses only SP.

## Decision
Oversized rasters are imported by **clipping them to the SP boundary**, using `engine.ingest.clip_raster`, into `data/raw/<source_id>/` (Option A of 2026-10-05).

- **Pixel rule:** a pixel is kept when its centre lies inside the union of the 645 municipalities of `ibge_malha_municipal_sp_2025`. That is the same centroid rule `engine.supply.raster_h3` uses. The output is cropped to SP's bounding box, with values and grid unchanged.
- **Nodata:** pixels outside SP get an explicit nodata value. For MapBiomas it is **0**, which is the producer's background outside Brazil (checked on the raster: ocean and neighbouring countries are 0). It is not a class in the Collection 10 legend, where "Not Observed" is 27.
- **Provenance:** every output gets a row in `CLIP_MANIFEST.tsv` inside the dataset folder. The row records the origin path, size and sha256, the boundary's sha256, the clip settings and the output sha256. Anyone holding the origin file can reproduce the clip byte for byte.
- **Immutability:** the tool never overwrites. It refuses deny-listed paths, and it writes through a temporary `.partial` file, so an interrupted run leaves no half-written raster.
- **Registry:** the registry entry describes the clipped dataset and points to the national source.

## Consequences
- \+ 17 years of SP land cover in about 0.55 GB instead of 13 GB, with a reproducible link to the national files.
- \+ The same tool serves Collection 11 and other national rasters later.
- − `data/raw/` now holds a derived product (a clip), not a byte copy. The manifest and this ADR make the derivation explicit, and nothing else in the pipeline treats the clip as an original.
- − Anyone who needs pixels outside SP must go back to the national files.

## Alternatives considered
- **Copy the national files into `data/raw/`.** Rejected: 13 GB per backup, of which more than 95 % lies outside SP.
- **Clip into `data/interim/` and leave `data/raw/` empty (Option B).** Rejected: the clips would then depend on files that live only on one PC, outside any registered dataset.
- **Download SP-only rasters from MapBiomas (Earth Engine / web tool).** Possible later, especially for Collection 11. It needs network access and an export step; the local files are already here.
