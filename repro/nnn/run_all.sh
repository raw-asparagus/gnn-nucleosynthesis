#!/usr/bin/env bash
# Run the patched Grichener et al. 2025 NNN evaluation for every (network, dt).
# Results land in repro/nnn/results/<net>/<dt>/Results/Files/.
set -u
cd "$(dirname "$0")/patched"
Z=/home/ikaros/projects/gnn-nucleosynthesis/data/zenodo/NuclearNeuralNetworks
DB=$Z/python_scripts_for_analysis/CreateFigures/Figure3_density_maps/database_files/approx21_cr60_plus_co56_database.csv
for net in mesa_80 mesa_151; do
  [ "$net" = mesa_80 ] && niso=80 || niso=151
  for dt in 1e-6 1e-5 1e-4 1e-3 1e-2 1e-1 1e0 1e1 1e2; do
    echo "=== $net dt=$dt ==="
    NNN_BASE_DIR=unused \
    NNN_DATABASE_FILE=$DB \
    NNN_ISOTOPES_NUM=$niso \
    NNN_MESA_DIR=../mesa_stub \
    NNN_ZENODO_DIR=$Z \
    NNN_RESULTS_DIR=../results/$net/$dt \
    NNN_NET=$net NNN_DT=$dt \
    uv run python runNNNsOnTestMesa80.py 2>&1 | grep -vE "^Iterating" | tail -2
    rc=$?
    [ $rc -ne 0 ] && echo "FAILED: $net $dt (rc=$rc)"
  done
done
echo ALL_RUNS_DONE
