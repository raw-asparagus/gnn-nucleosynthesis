#!/usr/bin/env bash
# MESA + bbq install scaffold — CHECKS ONLY by default; downloads NOTHING
# without --proceed.
#
# Pins:
#   MESA release r23.05.1  (the release used by Grichener et al. 2025 / NNN)
#   bbq  = R. Farmer's single-zone burner wrapping MESA's net module
#          (separate clone; builds against an existing MESA_DIR)
#
# MESA does NOT support arbitrary system Fortran toolchains. The supported
# route is the MESA SDK (http://user.astro.wisc.edu/~townsend/static.php?ref=mesasdk),
# which bundles pinned gfortran + libs. Use the SDK version recommended for
# r23.05.1 (see the MESA release notes; for 23.05.1 that is mesasdk 23.7.3 or
# the closest release listed on the SDK page). A bare system gfortran may
# compile MESA but is not a supported configuration — record any deviation.
#
# Disk budget: MESA source + build ~ 15 GB; SDK ~ 2 GB; bbq is small.
# Runtime env (put in shell profile once installed):
#   export MESASDK_ROOT=$HOME/mesasdk
#   source "$MESASDK_ROOT/bin/mesasdk_init.sh"
#   export MESA_DIR=$HOME/mesa-r23.05.1
#   export OMP_NUM_THREADS=<physical cores>
set -euo pipefail

MESA_VERSION="r23.05.1"
MESA_DIR_DEFAULT="${HOME}/mesa-${MESA_VERSION}"
MESASDK_ROOT_DEFAULT="${HOME}/mesasdk"
BBQ_REPO="https://github.com/rjfarmer/bbq"

echo "== MESA/bbq install scaffold (${MESA_VERSION}) =="
echo
echo "-- Toolchain / machine checks --"

if command -v gfortran >/dev/null 2>&1; then
    echo "gfortran : $(gfortran --version | head -1)"
else
    echo "gfortran : NOT FOUND (the MESA SDK ships its own; a system gfortran"
    echo "           is still useful for quick sanity builds)"
fi

echo "cores    : $(nproc)"
echo "RAM      : $(free -h | awk '/^Mem:/{print $2 " total, " $7 " available"}')"
echo "disk     : $(df -h "$HOME" | awk 'NR==2{print $4 " free on " $6}')  (need ~17 GB for SDK+MESA)"
if command -v nvidia-smi >/dev/null 2>&1; then
    echo "GPU      : $(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null || echo 'nvidia-smi present, query failed')"
else
    echo "GPU      : none visible (irrelevant for MESA/bbq — CPU/OpenMP only)"
fi
echo

if [[ "${1:-}" != "--proceed" ]]; then
    cat <<EOF
-- This is a scaffold: no downloads were performed. --

Next steps (manual, in order):
 1. Download the MESA SDK for your platform (version matching ${MESA_VERSION};
    see the SDK page + MESA release notes) and unpack to ${MESASDK_ROOT_DEFAULT}.
 2. Download MESA ${MESA_VERSION} (Zenodo mirror linked from
    https://docs.mesastar.org, release ${MESA_VERSION}) and unpack to
    ${MESA_DIR_DEFAULT}.
 3. export MESASDK_ROOT=${MESASDK_ROOT_DEFAULT}
    source \$MESASDK_ROOT/bin/mesasdk_init.sh
    export MESA_DIR=${MESA_DIR_DEFAULT}
    export OMP_NUM_THREADS=\$(nproc)
 4. cd \$MESA_DIR && ./install          # ~30-60 min; runs the test suite
 5. git clone ${BBQ_REPO} && follow its README to build against \$MESA_DIR.
 6. Record installed versions + any deviations in RESULTS.md / STEP1_REPORT.md.

Re-run with --proceed only after the SDK and MESA tarballs are in place;
--proceed still refuses to download anything, it only verifies MESA_DIR/
MESASDK_ROOT and prints the build commands.
EOF
    exit 0
fi

echo "-- --proceed: verifying environment (still no downloads) --"
: "${MESASDK_ROOT:?set MESASDK_ROOT (e.g. ${MESASDK_ROOT_DEFAULT})}"
: "${MESA_DIR:?set MESA_DIR (e.g. ${MESA_DIR_DEFAULT})}"
[[ -f "${MESASDK_ROOT}/bin/mesasdk_init.sh" ]] || { echo "ERROR: no mesasdk_init.sh under ${MESASDK_ROOT}"; exit 1; }
[[ -f "${MESA_DIR}/install" ]] || { echo "ERROR: no install script under ${MESA_DIR} — wrong tree?"; exit 1; }
echo "OK: SDK and MESA trees found. Build with:"
echo "  source ${MESASDK_ROOT}/bin/mesasdk_init.sh && cd ${MESA_DIR} && ./install"
