#!/usr/bin/env bash
# Build an OSRM routing graph for São Paulo (+ neighbours) from the Geofabrik Sudeste extract.
# Source registered as `osm_sudeste` in registry/sources.yaml (Geofabrik page:
# https://download.geofabrik.de/south-america/brazil/sudeste.html ; ~0.8 GB in Jul 2026).
#
# Usage:  bash scripts/routing/setup_osrm.sh                # whole Sudeste
#         BBOX="minlon,minlat,maxlon,maxlat" bash scripts/routing/setup_osrm.sh   # clip first
# Clipping needs osmium-tool (apt install osmium-tool). Choose a bbox that covers SP plus the
# cane supply areas across the MG/PR/MS borders (CLAUDE.md: border effects).
#
# Memory: extraction of a large regional extract can need >8 GB RAM — give Docker Desktop
# 12–16 GB (docs/04). OSRM's README reports ~30 min for a 550 MB extract.
set -euo pipefail
DIR="data/routing"
PBF_URL="https://download.geofabrik.de/south-america/brazil/sudeste-latest.osm.pbf"
IMG="ghcr.io/project-osrm/osrm-backend"
mkdir -p "$DIR"
if [ ! -f "$DIR/sudeste-latest.osm.pbf" ]; then
  curl -L --fail -o "$DIR/sudeste-latest.osm.pbf" "$PBF_URL"
fi
sha256sum "$DIR/sudeste-latest.osm.pbf" | tee "$DIR/sudeste-latest.osm.pbf.sha256"
SRC="$DIR/sudeste-latest.osm.pbf"
if [ -n "${BBOX:-}" ]; then
  osmium extract -b "$BBOX" "$SRC" -o "$DIR/region.osm.pbf" --overwrite
else
  cp "$SRC" "$DIR/region.osm.pbf"
fi
docker run --rm -t -v "$PWD/$DIR:/data" "$IMG" osrm-extract -p /opt/car.lua /data/region.osm.pbf
docker run --rm -t -v "$PWD/$DIR:/data" "$IMG" osrm-partition /data/region.osrm
docker run --rm -t -v "$PWD/$DIR:/data" "$IMG" osrm-customize /data/region.osrm
echo "Graph ready. Start the server: docker compose -f docker-compose.routing.yml up -d"
echo "Record the pbf sha256 and download date in registry/sources.yaml (osm_sudeste)."
