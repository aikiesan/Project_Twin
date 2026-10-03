# ADR-0002 — H3 resolution 8 as analysis grid

- **Status:** Proposed
- **Context:** MapBiomas cane is 30 m (~275 M pixels/yr for SP). We need a grid to join supply, costs, constraints and routing, small enough for catchment detail and large enough for compute.
- **Decision:** Use **H3 resolution 8** (~0.74 km² per cell; verify in h3 docs) for analysis; res 7 (~5 km²) for statewide overviews and web display.
- **Consequences:** + hierarchical aggregation, equal-ish areas, fast joins (h3-pg); − hexagon boundaries don't match municipalities (handle with area-weighted allocation + municipal rescaling).
- **Alternatives:** regular 1 km grid (fine but less tooling); municipality level (too coarse for catchments).
