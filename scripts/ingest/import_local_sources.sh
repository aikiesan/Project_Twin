#!/usr/bin/env bash
# Copy the São Paulo datasets already held in a local PILAR-2b checkout into data/raw/<source_id>/.
#
#   bash scripts/ingest/import_local_sources.sh /a/Pilar-2b            # copy
#   DRY_RUN=1 bash scripts/ingest/import_local_sources.sh /a/Pilar-2b  # list only
#   WITH_SECOND_CROP=1 bash scripts/ingest/import_local_sources.sh ... # + MapBiomas 2nd-crop rasters (~1.3 GB)
#
# - Read-only on the source: never writes, moves or deletes anything there.
# - Never overwrites: a file already in data/raw/ is skipped (raw data is immutable, CLAUDE.md rule 4).
# - Every copy is logged (origin path, bytes, PILAR-2b commit) to data/interim/import_local_sources_log.tsv,
#   outside data/raw/ so the inventory scan does not pick the log up as a dataset.
# - Out of scope and never copied: TerraClass AMZ, MG layers, silviculture, the locally modified
#   analysis/data/05_biogas_plants_brazil.*, and anything from CP2B_Maps_V3 (Amasa O-D interviews = LGPD).
# Next step: python -m engine.ingest.inventory data/raw ... then register each folder in registry/sources.yaml.
set -euo pipefail

SRC="${1:-}"
if [ -z "$SRC" ] || [ ! -d "$SRC" ]; then
  echo "usage: bash scripts/ingest/import_local_sources.sh <PILAR-2b folder, e.g. /a/Pilar-2b>" >&2
  exit 2
fi
SRC="$(cd "$SRC" && pwd)"
ENGINE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RAW="${RAW_DIR:-$ENGINE_DIR/data/raw}"
LOG="${LOG_FILE:-$ENGINE_DIR/data/interim/import_local_sources_log.tsv}"
DRY_RUN="${DRY_RUN:-0}"
WITH_SECOND_CROP="${WITH_SECOND_CROP:-0}"

FPR="$SRC/00_Fontes_Primarias-20260802T093400Z-1-001"   # Google Drive export of the primary sources
FP0="$FPR/00_Fontes_Primarias"
BK="$SRC/cp2b-workspace/NewLook/backend/data"
CP="$SRC/cp2b-workspace/NewLook/data/canonical_parameters"
AD="$SRC/analysis/data"

ORIGIN_GIT="$(git -C "$SRC" rev-parse --short HEAD 2>/dev/null || echo none)"
if [ "$ORIGIN_GIT" != none ] && [ -n "$(git -C "$SRC" status --porcelain 2>/dev/null)" ]; then
  ORIGIN_GIT="$ORIGIN_GIT+dirty"
fi
STAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
copied=0 skipped=0 missing=0 excluded=0

if [ "$DRY_RUN" != 1 ]; then
  mkdir -p "$RAW" "$(dirname "$LOG")"
  [ -f "$LOG" ] || printf 'imported_at_utc\tsource_id\tdest_relpath\tbytes\torigin_path\torigin_git\n' > "$LOG"
fi

# copy_file <source_id> <file> [dest path relative to data/raw/<source_id>/]
copy_file() {
  local id="$1" src="$2" rel="${3:-$(basename "$2")}"
  local dest="$RAW/$id/$rel"
  if [ ! -f "$src" ]; then
    echo "MISSING   $src"; missing=$((missing + 1)); return 0
  fi
  case "$(basename "$src")" in
    MG_*|*TerraClass*|*AMZ.*)
      echo "excluded  $src (out of scope)"; excluded=$((excluded + 1)); return 0 ;;
  esac
  if [ -e "$dest" ]; then
    echo "skip      $id/$rel (exists)"; skipped=$((skipped + 1)); return 0
  fi
  if [ "$DRY_RUN" = 1 ]; then
    echo "would     $id/$rel"; copied=$((copied + 1)); return 0
  fi
  mkdir -p "$(dirname "$dest")"
  cp -p "$src" "$dest"
  printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$STAMP" "$id" "$rel" "$(wc -c < "$src" | tr -d ' ')" "$src" "$ORIGIN_GIT" >> "$LOG"
  echo "copied    $id/$rel"; copied=$((copied + 1))
}

# copy_dir <source_id> <dir> [prefix inside data/raw/<source_id>/] — keeps sub-folders
copy_dir() {
  local id="$1" dir="$2" prefix="${3:-}" f
  if [ ! -d "$dir" ]; then
    echo "MISSING   $dir/"; missing=$((missing + 1)); return 0
  fi
  while IFS= read -r -d '' f; do
    copy_file "$id" "$f" "${prefix:+$prefix/}${f#"$dir"/}"
  done < <(find "$dir" -type f ! -name 'desktop.ini' ! -name 'Thumbs.db' ! -name '.DS_Store' -print0 | sort -z)
}

# first_match <dir> <glob> — folder names from Google Drive exports carry a timestamp suffix
first_match() {
  local m
  for m in "$1"/$2; do [ -e "$m" ] && { echo "$m"; return 0; }; done
  echo "$1/$2"
}

echo "== from $SRC (git $ORIGIN_GIT) into $RAW"
[ "$DRY_RUN" = 1 ] && echo "== DRY RUN: nothing is written"

# --- boundaries -------------------------------------------------------------------------------
copy_dir ibge_malha_municipal_sp_2025  "$FPR/SP_Municipios_2025"
# --- MapBiomas ---------------------------------------------------------------------------------
copy_dir mapbiomas_col10_municipal     "$FP0/MapBiomas_col10"
copy_dir mapbiomas_agropecuaria_sp_2024 "$BK/mapbiomas"
copy_dir mapbiomas_infra               "$BK/shapefiles/mapbiomas_infra"
if [ "$WITH_SECOND_CROP" = 1 ]; then
  copy_dir mapbiomas_second_crop       "$FP0/MapBiomas_Segunda_Safra"
fi
# --- CP2B project_map layers (SP limits, municipalities 2024, gas, power, roads, ETEs, urban areas)
copy_dir cp2b_project_map              "$BK/shapefiles/project_map_source/data"
# --- crop statistics -----------------------------------------------------------------------------
copy_dir ibge_pam_seade                "$FP0/PAM_1612_1613"  PAM_1612_1613
copy_dir ibge_pam_seade                "$FP0/Agro_PAM_CONAB" Agro_PAM_CONAB
# --- CP2B internal results ------------------------------------------------------------------------
copy_dir cp2b_results_sicar            "$(first_match "$FPR" "CP2B_Results-*")/CP2B_Results"
copy_dir cp2b_gee_exports              "$(first_match "$FPR" "GEE_Exports-*")/GEE_Exports"
# --- PILAR-2b tables (git-tracked there, except the two FDE files) --------------------------------
copy_file pilar2b_fde                  "$SRC/fde_residue_availability.csv"
copy_file pilar2b_fde                  "$BK/FDE_Disponibilidade_Residuos_CP2B.xlsx"
copy_dir pilar2b_canonical_parameters  "$CP"
for f in 00_DATA_DICTIONARY.json 01_master_residue_streams_SP_2023.csv \
         02_municipality_summary_SP_2023.csv 03_conversion_factors.csv 04_state_summary_by_stream.csv; do
  copy_file pilar2b_residue_streams_sp "$AD/$f"
done
for f in 05c_anp_biometano_plants_latest.csv 05d_anp_biometano_production_state_monthly.csv \
         05e_anp_biometano_plant_volume_monthly.csv 05f_anp_fleet_stats.csv; do
  copy_file anp_biomethane_plants      "$AD/$f"
done
copy_dir anp_biomethane_plants         "$AD/sources/anp"   sources
copy_file aneel_biogas_gd              "$AD/05g_aneel_biogas_gd_plants.csv"
copy_file aneel_biogas_gd              "$AD/05h_aneel_biogas_gd_summary.csv"
copy_dir aneel_biogas_gd               "$AD/sources/aneel" sources

echo "== copied=$copied skipped=$skipped missing=$missing excluded=$excluded"
[ "$DRY_RUN" = 1 ] || echo "== log: $LOG"
