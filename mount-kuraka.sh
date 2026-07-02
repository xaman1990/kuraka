#!/bin/bash
# mount-kuraka.sh — Unix wrapper around the canonical cross-platform mount.
#
# The mount logic now lives in kuraka-mount.py (pure Python 3, no rsync — so it
# also runs natively on Windows/PowerShell). This wrapper keeps the historical
# `bash mount-kuraka.sh [target]` entrypoint working unchanged.
#
# Usage:  bash /path/to/vault/mount-kuraka.sh [target_dir]

set -euo pipefail

DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export KURAKA_VAULT="${KURAKA_VAULT:-$DIR}"

if command -v python3 >/dev/null 2>&1; then PY=python3
elif command -v python  >/dev/null 2>&1; then PY=python
else
    echo "❌ ERROR: se necesita Python 3 (python3/python) para el mount." >&2
    exit 1
fi

exec "$PY" "$DIR/kuraka-mount.py" "$@"
