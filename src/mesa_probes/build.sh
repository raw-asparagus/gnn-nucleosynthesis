#!/usr/bin/env bash
# Build mesa_probe against the local MESA installation.
# Mirrors the environment setup in scripts/install_mesa_full.sh.
set -euo pipefail

export MESA_DIR="${MESA_DIR:-$HOME/mesa-r23.05.1}"
export MESASDK_ROOT="${MESASDK_ROOT:-$HOME/mesasdk}"

set +u
# mesasdk_init.sh returns 1 on this box (csh + X11 prereq warnings — known
# no-root quirks, see scripts/install_mesa_full.sh) but still sets up the env.
# shellcheck disable=SC1091
source "$MESASDK_ROOT/bin/mesasdk_init.sh" || true
set -u
command -v gfortran >/dev/null || { echo "mesasdk gfortran not on PATH"; exit 1; }

export OMP_NUM_THREADS="$(nproc)"
# no-root libX11 workaround used for the MESA build itself
export LIBRARY_PATH="$HOME/.local/lib${LIBRARY_PATH:+:$LIBRARY_PATH}"

cd "$(dirname "$0")"
make "$@" mesa_probe
echo "built: $(pwd)/mesa_probe"
