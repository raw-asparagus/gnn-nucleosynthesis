#!/usr/bin/env bash
# Side-by-side install of MESA 24.08.1 (first release with the gh-575
# reverse-rate phase-space fix — the Grichener et al. 2025 Appendix-B bug)
# next to the stock r23.05.1 tree. Step 4 Task 4 decision (user, 2026-07-09):
# run the rate cross-check and kappa screen against 24.08.1 instead of
# patching r23.05.1. Mirrors scripts/install_mesa_full.sh conventions.
#
# Usage: bash scripts/install_mesa_24081.sh [download|unpack|build|all]
set -euo pipefail

MESA24_DIR="${MESA24_DIR:-$HOME/mesa-24.08.1}"
MESASDK_ROOT="${MESASDK_ROOT:-$HOME/mesasdk}"
DL_DIR="${DL_DIR:-$HOME/mesa_downloads}"

# Zenodo record 13353788 (concept 10.5281/zenodo.2602941), version r24.08.1
ZIP_URL="https://zenodo.org/api/records/13353788/files/mesa-24.08.1.zip/content"
ZIP_MD5="75418c76ad48783cdb8a2cfdc8be020f"
ZIP_PATH="$DL_DIR/mesa-24.08.1.zip"

phase_download() {
    mkdir -p "$DL_DIR"
    if [[ -f "$ZIP_PATH" ]] && md5sum "$ZIP_PATH" | grep -q "$ZIP_MD5"; then
        echo "already downloaded + verified: $ZIP_PATH"
        return 0
    fi
    curl -L --fail --retry 3 -C - -o "$ZIP_PATH" "$ZIP_URL"
    echo "verifying md5..."
    md5sum "$ZIP_PATH" | grep -q "$ZIP_MD5" || { echo "MD5 MISMATCH"; exit 1; }
    echo "download verified ($ZIP_MD5)"
}

phase_unpack() {
    [[ -f "$MESA24_DIR/install" ]] && { echo "already unpacked"; return 0; }
    local tmp="$HOME/.mesa24_unpack_tmp"
    rm -rf "$tmp" && mkdir -p "$tmp"
    # unzip preserves executable bits (python zipfile does not)
    unzip -q "$ZIP_PATH" -d "$tmp"
    local top
    top=$(find "$tmp" -mindepth 1 -maxdepth 2 -name install -type f | head -1 | xargs -r dirname)
    [[ -n "$top" ]] || { echo "no install script found"; exit 1; }
    mv "$top" "$MESA24_DIR"
    rm -rf "$tmp"
    chmod +x "$MESA24_DIR/install" 2>/dev/null || true
    echo "unpacked to $MESA24_DIR"
}

phase_build() {
    export MESASDK_ROOT
    export MESA_DIR="$MESA24_DIR"
    set +u
    # returns 1 on this box (csh/X11 prereq warnings; known no-root quirks)
    # shellcheck disable=SC1091
    source "$MESASDK_ROOT/bin/mesasdk_init.sh" || true
    set -u
    command -v gfortran >/dev/null || { echo "mesasdk gfortran not on PATH"; exit 1; }
    export OMP_NUM_THREADS="$(nproc)"
    export LIBRARY_PATH="$HOME/.local/lib${LIBRARY_PATH:+:$LIBRARY_PATH}"
    gfortran --version | head -1
    cd "$MESA_DIR"
    ./install
}

case "${1:-all}" in
    download) phase_download ;;
    unpack) phase_unpack ;;
    build) phase_build ;;
    all) phase_download && phase_unpack && phase_build ;;
    *) echo "usage: $0 [download|unpack|build|all]"; exit 2 ;;
esac
