#!/usr/bin/env bash
# APPLY.sh - Apply the M2.3b "Atari Platform Pack" overlay.
#
# Consistent with the M2.3a delivery convention, this milestone is shipped
# as an overlay archive (overlay.tar.gz) containing every file that was
# added or modified for this milestone, with paths relative to the
# repository root. APPLY.sh does not hand-edit files in place; it applies
# the milestone purely by extracting the overlay archive on top of the
# working tree, so the applied result is byte-for-byte identical to what
# was built and verified when this delivery was produced.
#
# Files added by this overlay:
#   src/retropal/palettes/definitions/atari-2600-tia.json
#   src/retropal/palettes/definitions/atari-8bit-antic-gtia.json
#   src/retropal/palettes/definitions/atari-st.json
#   src/retropal/palettes/definitions/atari-ste.json
#   src/retropal/palettes/definitions/atari-falcon030.json
#   tests/test_atari_palettes.py
#
# Files modified by this overlay:
#   src/retropal/__init__.py        (version -> 0.2.0.dev2)
#   src/retropal/cli.py             (adds `retropal palettes --family`)
#   src/retropal/palettes/fixed.py  (registers the 5 new palette ids)
#   tests/test_cli.py               (adds --family CLI smoke tests)
#   README.md                       (documents the new palettes)
#   CHANGELOG.md                    (adds the M2.3b entry)
#
# Usage:
#   ./.delivery/M2.3b/APPLY.sh [path-to-repo-root]
#
# If no path is given, the repository root is assumed to be two directories
# above this script (.delivery/M2.3b/APPLY.sh -> repo root).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${1:-$(cd "${SCRIPT_DIR}/../.." && pwd)}"
OVERLAY="${SCRIPT_DIR}/overlay.tar.gz"

if [[ ! -f "${OVERLAY}" ]]; then
  echo "error: overlay archive not found at ${OVERLAY}" >&2
  exit 1
fi

echo "Applying M2.3b overlay to: ${REPO_ROOT}"
tar -xzf "${OVERLAY}" -C "${REPO_ROOT}"
echo "Overlay extracted. Run ./.delivery/M2.3b/VERIFY.sh next to validate the result."
