# ADR-0006 — OSRM (car profile) for v0 road-network distances

- **Status:** Proposed
- **Context:** CLAUDE.md requires road-network distances for haul costs and Huff allocation. Options: OSRM (fast table service, simple Docker setup, no truck costing in the stock profile), Valhalla (truck costing with weight/axle/height, slower matrices), pgRouting (needs a custom PostGIS image, slow for large matrices), commercial APIs (cost, licensing).
- **Decision:** Use **OSRM with the stock `car.lua` profile** (image `ghcr.io/project-osrm/osrm-backend`, graph from the Geofabrik Sudeste extract) for v0 OD matrices (`engine.siting.routing`, `docker-compose.routing.yml`). Record the pbf sha256 with every matrix.
- **Consequences:** + matrices for hundreds of thousands of pairs in minutes; reproducible; − ignores truck restrictions and speeds (tankers, bulk trucks), so durations are optimistic; distances are usually close to truck routes on the main network. Detour ratios are logged as QA.
- **Revisit when:** haul *time* matters (driver hours, fleet sizing) or Gate 4 sensitivity shows siting depends on route choice → evaluate Valhalla `truck` costing on a sample of pairs and compare (new ADR).
