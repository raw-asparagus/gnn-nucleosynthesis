#!/usr/bin/env bash
# Run bbq in one campaign run directory (argument 1). Sources the MESA SDK,
# pins the environment, and executes bbq on the directory's inlist. stdout+
# stderr go to run.log inside the directory. Exit code = bbq's exit code.
# no `set -u`: mesasdk_init.sh references unset vars and would kill the shell

RUNDIR="${1:?usage: run_one.sh RUNDIR}"
export MESASDK_ROOT="${MESASDK_ROOT:-$HOME/mesasdk}"
# mesasdk_init warns about missing csh/X11 — harmless for bbq (no-root install)
source "$MESASDK_ROOT/bin/mesasdk_init.sh" > /dev/null 2>&1 || true
export MESA_DIR="${MESA_DIR:-$HOME/mesa-r23.05.1}"
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"
# alternate binary (e.g. ~/bbq_24081/bbq against MESA 24.08.1) via BBQ_BIN
BBQ_BIN="${BBQ_BIN:-$HOME/bbq/bbq}"

cd "$RUNDIR" || exit 97
exec "$BBQ_BIN" inlist > run.log 2>&1
