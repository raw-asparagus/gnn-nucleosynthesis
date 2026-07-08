#!/usr/bin/env bash
# Full MESA + bbq installer — downloads, builds, and smoke-tests.
#
# Companion to scripts/install_mesa.sh (which stays checks-only). This one
# actually fetches the MESA SDK and MESA r23.05.1 (the release used by
# Grichener et al. 2025 / NNN), builds MESA with the SDK toolchain, then
# clones and builds bbq against it.
#
# Designed to run unattended in the background:
#   bash scripts/install_mesa_full.sh
# Progress is machine-readable in scripts/mesa_install_logs/STATUS
# (one line: PHASE=<name> STATE=running|done|failed TS=<iso8601>), with
# per-phase logs in scripts/mesa_install_logs/NN_<phase>.log. Phases that
# completed are skipped on re-run (marker files), so the script is resumable.
#
# Download sources:
#   SDK : mesasdk-x86_64-linux-23.7.3.tar.gz from Townsend's SDK page
#         (23.7.3 is the SDK release contemporaneous with r23.05.1; the
#         SDK page's listed md5 is checked when it can be scraped).
#   MESA: Zenodo — the record id below is a best guess and is NEVER trusted:
#         the record metadata must name r23.05.1 or we fall back to the
#         Zenodo search API; the file md5 comes from the API response.
set -uo pipefail

MESA_VERSION="r23.05.1"
SDK_VERSION="23.7.3"
SDK_TARBALL="mesasdk-x86_64-linux-${SDK_VERSION}.tar.gz"
SDK_URL="http://user.astro.wisc.edu/~townsend/resource/download/mesasdk/${SDK_TARBALL}"
SDK_PAGE="http://user.astro.wisc.edu/~townsend/static.php?ref=mesasdk"
ZENODO_RECORD_GUESS="7983526"
BBQ_REPO="https://github.com/rjfarmer/bbq"

MESA_DIR="${MESA_DIR:-$HOME/mesa-${MESA_VERSION}}"
MESASDK_ROOT="${MESASDK_ROOT:-$HOME/mesasdk}"
BBQ_DIR="${BBQ_DIR:-$HOME/bbq}"
DL_DIR="$HOME/mesa_downloads"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$REPO_ROOT/scripts/mesa_install_logs"
STATUS_FILE="$LOG_DIR/STATUS"
mkdir -p "$LOG_DIR" "$DL_DIR"

status() { echo "PHASE=$1 STATE=$2 TS=$(date -Is)" >"$STATUS_FILE"; }

# Fatal shell errors (e.g. nounset) bypass run_phase's failure branch; make
# sure STATUS never claims "running" after the process is gone.
finalize_status() {
    if grep -q "STATE=running" "$STATUS_FILE" 2>/dev/null; then
        local phase
        phase=$(sed -n 's/^PHASE=\([^ ]*\).*/\1/p' "$STATUS_FILE")
        status "${phase:-unknown}" failed
    fi
}
trap finalize_status EXIT

run_phase() {
    local num="$1" phase="$2"
    local log="$LOG_DIR/${num}_${phase}.log"
    local marker="$LOG_DIR/.done_${phase}"
    if [[ -f "$marker" ]]; then
        echo "== skip $phase (already done) =="
        return 0
    fi
    status "$phase" running
    local t0=$SECONDS
    if "phase_${phase}" >>"$log" 2>&1; then
        touch "$marker"
        echo "PHASE=$phase WALL_SECONDS=$((SECONDS - t0))" >>"$LOG_DIR/timings.log"
        echo "== $phase done ($((SECONDS - t0)) s) =="
    else
        status "$phase" failed
        echo "== FAILED at $phase — see $log ==" >&2
        exit 1
    fi
}

phase_preflight() {
    local avail_kb
    avail_kb=$(df --output=avail "$HOME" | tail -1 | tr -d ' ')
    echo "avail on \$HOME: $((avail_kb / 1024 / 1024)) GB; nproc: $(nproc)"
    [[ $avail_kb -ge $((20 * 1024 * 1024)) ]] || { echo "need >= 20 GB free"; return 1; }
    command -v python3 >/dev/null || { echo "python3 required for Zenodo JSON"; return 1; }
    command -v curl >/dev/null || { echo "curl required"; return 1; }
    command -v git >/dev/null || { echo "git required"; return 1; }
}

phase_download_sdk() {
    local tarball="$DL_DIR/$SDK_TARBALL"
    if [[ ! -s "$tarball" ]]; then
        curl -fL --retry 3 -o "$tarball" "$SDK_URL"
    fi
    tar -tzf "$tarball" >/dev/null || { echo "SDK tarball corrupt"; return 1; }
    # Best-effort md5 cross-check against the SDK page listing.
    local page_md5 local_md5
    page_md5=$(curl -fsL "$SDK_PAGE" 2>/dev/null \
        | grep -oiE "${SDK_TARBALL}[^<]*<[^>]*>[^<]*[0-9a-f]{32}|[0-9a-f]{32}[^<]*${SDK_TARBALL}" \
        | grep -oiE '[0-9a-f]{32}' | head -1 || true)
    local_md5=$(md5sum "$tarball" | cut -d' ' -f1)
    echo "SDK md5 local=$local_md5 page=${page_md5:-unscrapable}"
    if [[ -n "$page_md5" && "$page_md5" != "$local_md5" ]]; then
        echo "SDK md5 MISMATCH vs page listing"; return 1
    fi
}

phase_download_mesa() {
    # Resolve the MESA release file via the Zenodo API; verify the record
    # really is r23.05.1 before trusting it.
    python3 - "$ZENODO_RECORD_GUESS" "$MESA_VERSION" "$DL_DIR" <<'PYEOF'
import json, sys, urllib.request, urllib.parse

guess, version, dl_dir = sys.argv[1], sys.argv[2], sys.argv[3]

def get(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.load(r)

def record_matches(rec):
    md = rec.get("metadata", {})
    blob = " ".join([md.get("title", ""), md.get("version", "")])
    if "candidate" in blob.lower() or "-rc" in blob.lower():
        return False  # release candidates are not the pinned release
    return version in blob or version.lstrip("r") in blob

rec = None
try:
    cand = get(f"https://zenodo.org/api/records/{guess}")
    if record_matches(cand):
        rec = cand
    else:
        print(f"record {guess} does not name {version}; falling back to search")
except Exception as e:
    print(f"record {guess} fetch failed ({e}); falling back to search")

if rec is None:
    q = urllib.parse.quote(f'title:MESA "{version}"')
    hits = get(f"https://zenodo.org/api/records?q={q}&size=20").get("hits", {}).get("hits", [])
    hits = [h for h in hits if record_matches(h)]
    if not hits:
        sys.exit(f"no Zenodo record found for MESA {version}; "
                 "check docs.mesastar.org release notes for the mirror link")
    rec = hits[0]

title = rec["metadata"]["title"]
print(f"using Zenodo record {rec['id']}: {title}")
files = rec.get("files", [])
# Exact release archive first; never fall through to an -rc file.
want = [f for f in files if f["key"] in (f"mesa-{version}.zip", f"mesa-{version}.tar.gz")]
if not want:
    want = [f for f in files
            if version.lstrip("r") in f["key"] and "rc" not in f["key"].lower()
            and f["key"].endswith((".zip", ".tar.gz", ".tgz"))]
if not want:
    want = [f for f in files if f["key"].endswith((".zip", ".tar.gz", ".tgz"))]
if not want:
    sys.exit(f"no archive file on record {rec['id']}: {[f['key'] for f in files]}")
f = max(want, key=lambda f: f.get("size", 0))
url = f["links"]["self"]
checksum = f.get("checksum", "")
print(f"file={f['key']} size={f.get('size')} checksum={checksum}")
with open(f"{dl_dir}/MESA_FILE_INFO", "w") as fh:
    fh.write(f"{f['key']}\n{url}\n{checksum}\n")
PYEOF
    local key url checksum
    { read -r key; read -r url; read -r checksum; } <"$DL_DIR/MESA_FILE_INFO"
    local archive="$DL_DIR/$key"
    if [[ ! -s "$archive" ]]; then
        curl -fL --retry 3 -o "$archive" "$url"
    fi
    if [[ "$checksum" == md5:* ]]; then
        echo "${checksum#md5:}  $archive" | md5sum -c - || return 1
    else
        echo "WARNING: no md5 in API response (checksum='$checksum'); skipping verify"
    fi
}

phase_unpack() {
    if [[ ! -f "$MESASDK_ROOT/bin/mesasdk_init.sh" ]]; then
        tar -xzf "$DL_DIR/$SDK_TARBALL" -C "$(dirname "$MESASDK_ROOT")"
    fi
    [[ -f "$MESASDK_ROOT/bin/mesasdk_init.sh" ]] || { echo "SDK unpack failed"; return 1; }
    if [[ ! -f "$MESA_DIR/install" ]]; then
        local key archive
        key=$(head -1 "$DL_DIR/MESA_FILE_INFO")
        archive="$DL_DIR/$key"
        local tmp="$HOME/.mesa_unpack_tmp"
        rm -rf "$tmp" && mkdir -p "$tmp"
        case "$key" in
            *.zip) python3 -c "import zipfile,sys; zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])" "$archive" "$tmp" ;;
            *) tar -xzf "$archive" -C "$tmp" ;;
        esac
        local top
        top=$(find "$tmp" -mindepth 1 -maxdepth 2 -name install -type f | head -1 | xargs -r dirname)
        [[ -n "$top" ]] || { echo "no install script found in archive"; return 1; }
        mv "$top" "$MESA_DIR"
        rm -rf "$tmp"
    fi
    [[ -f "$MESA_DIR/install" ]] || { echo "MESA unpack failed"; return 1; }
    chmod +x "$MESA_DIR/install" 2>/dev/null || true
}

phase_build_mesa() {
    export MESASDK_ROOT MESA_DIR
    # mesasdk_init.sh reads possibly-unset vars (MANPATH); relax nounset for it.
    set +u
    # shellcheck disable=SC1091
    source "$MESASDK_ROOT/bin/mesasdk_init.sh"
    set -u
    export OMP_NUM_THREADS="$(nproc)"
    gfortran --version | head -1
    cd "$MESA_DIR"
    ./install
}

phase_test_mesa() {
    # MESA's ./install runs each module's own test suite and prints a
    # success banner only if everything passed.
    grep -q "MESA installation was successful" "$LOG_DIR/05_build_mesa.log" \
        || { echo "success banner not found in build log"; return 1; }
    echo "MESA installation was successful (banner confirmed)"
}

phase_build_bbq() {
    export MESASDK_ROOT MESA_DIR
    set +u
    # shellcheck disable=SC1091
    source "$MESASDK_ROOT/bin/mesasdk_init.sh"
    set -u
    export OMP_NUM_THREADS="$(nproc)"
    if [[ ! -d "$BBQ_DIR/.git" ]]; then
        git clone "$BBQ_REPO" "$BBQ_DIR"
    fi
    cd "$BBQ_DIR"
    git log -1 --format='bbq commit: %H %cs'
    sed -n '1,60p' README* 2>/dev/null || true
    if [[ -x ./mk ]]; then ./mk
    elif [[ -f Makefile ]]; then make
    elif [[ -x ./build ]]; then ./build
    else echo "no recognized bbq build entry point"; return 1
    fi
}

main() {
    run_phase 01 preflight
    run_phase 02 download_sdk
    run_phase 03 download_mesa
    run_phase 04 unpack
    run_phase 05 build_mesa
    run_phase 06 test_mesa
    run_phase 07 build_bbq
    status done done
    echo "== all phases complete =="
    echo "MESA_DIR=$MESA_DIR  MESASDK_ROOT=$MESASDK_ROOT  BBQ_DIR=$BBQ_DIR"
}

main "$@"
