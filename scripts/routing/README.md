# Routing (road-network distances)

CLAUDE.md requires **road-network** distances for logistics. v0 uses OSRM with the stock car
profile (fast, simple); truck-specific costing (Valhalla `truck`) needs an ADR before adoption.

1. `bash scripts/routing/setup_osrm.sh` — downloads the Geofabrik Sudeste extract (registry id
   `osm_sudeste`), optionally clips it (`BBOX=...`), builds the MLD graph in `data/routing/`.
2. `docker compose -f docker-compose.routing.yml up -d` — serves `http://localhost:5000`.
3. In Python:

```python
from engine.siting.routing import od_matrix, detour_ratio
dist_km, dur_h = od_matrix(cell_centroids_latlon, mill_latlon, max_table_size=10_000)
ratio = detour_ratio(dist_km, cell_centroids_latlon, mill_latlon)   # QA: flag <1 or >>2
```

The matrix feeds Huff allocation (`engine.supply.huff`) and the siting MILP transport costs
(`engine.siting.facility_milp`). Store matrices in `data/interim/od/` (Parquet) with the pbf
sha256 in the run log so distances are reproducible.

Limits/caveats
- Snapping: points far from roads (cell centroids in large fields) snap to the nearest road;
  check `detour_ratio` and OSRM `snapping` distances for outliers.
- `max-table-size` in `docker-compose.routing.yml` must match `od_matrix(max_table_size=...)`.
- SP statewide H3 res-8 cells with cane × all mills is large: compute per mill within a
  buffer (e.g. the Huff `d_max`) rather than the full matrix.
- Fallback detour factor (`road_detour_factor_*`, ESD): its denominator may be the EPSG:5880
  straight line rather than the great circle. `python scripts/routing/polyconic_vs_great_circle.py`
  (with `PYTHONPATH=src`) estimates the gap in SP (docs/21 Q24).
