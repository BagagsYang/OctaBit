#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WINDOWS_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PROJECT_ROOT="$(cd "${WINDOWS_ROOT}/.." && pwd)"
BUNDLE_ROOT="${PROJECT_ROOT}/windows-review-bundle"
ARCHIVE_PATH="${PROJECT_ROOT}/windows-review-bundle.zip"

rm -rf "${BUNDLE_ROOT}" "${ARCHIVE_PATH}"
mkdir -p "${BUNDLE_ROOT}/shared" "${BUNDLE_ROOT}/.github/workflows"

rsync -a \
  --exclude '.DS_Store' \
  --exclude '__pycache__' \
  "${WINDOWS_ROOT}/" \
  "${BUNDLE_ROOT}/windows-app/"

cp \
  "${PROJECT_ROOT}/shared/midi_to_wave.py" \
  "${PROJECT_ROOT}/shared/requirements.txt" \
  "${PROJECT_ROOT}/shared/README.md" \
  "${BUNDLE_ROOT}/shared/"

cp \
  "${PROJECT_ROOT}/.github/workflows/windows-release.yml" \
  "${BUNDLE_ROOT}/.github/workflows/"

cp \
  "${PROJECT_ROOT}/global.json" \
  "${BUNDLE_ROOT}/"

(cd "${PROJECT_ROOT}" && zip -r "$(basename "${ARCHIVE_PATH}")" "$(basename "${BUNDLE_ROOT}")" -x "*.DS_Store" "*/__pycache__/*")

echo "Created ${ARCHIVE_PATH}"
