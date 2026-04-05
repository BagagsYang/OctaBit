#!/bin/bash
set -euo pipefail

if [[ -z "${SRCROOT:-}" ]]; then
  DESKTOP_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
else
  DESKTOP_ROOT="${SRCROOT}"
fi

PROJECT_ROOT="$(cd "${DESKTOP_ROOT}/.." && pwd)"
SHARED_ROOT="${PROJECT_ROOT}/shared"
HTML_ROOT="${PROJECT_ROOT}/html-app"
PYTHON_BIN="${PROJECT_ROOT}/.venv/bin/python3"
HELPER_NAME="midi_to_wave_helper"
DERIVED_ROOT="${DERIVED_FILE_DIR:-${DESKTOP_ROOT}/build/derived}"
WORK_ROOT="${DERIVED_ROOT}/python-helper"
DIST_DIR="${WORK_ROOT}/dist"
WORK_DIR="${WORK_ROOT}/work"
SPEC_DIR="${WORK_ROOT}/spec"
CACHE_DIR="${WORK_ROOT}/cache"
RESOURCES_DIR="${TARGET_BUILD_DIR:-${DESKTOP_ROOT}/build}/${UNLOCALIZED_RESOURCES_FOLDER_PATH:-Resources}"

if [[ ! -x "${PYTHON_BIN}" ]]; then
  echo "error: Missing ${PYTHON_BIN}. Recreate the repo-local virtual environment before building." >&2
  exit 1
fi

if ! "${PYTHON_BIN}" -c "import numpy, pretty_midi, scipy, PyInstaller" >/dev/null 2>&1; then
  echo "error: Missing Python desktop-build dependencies. Run '${PYTHON_BIN} -m pip install -r ${SHARED_ROOT}/requirements.txt' first." >&2
  exit 1
fi

mkdir -p "${DIST_DIR}" "${WORK_DIR}" "${SPEC_DIR}" "${CACHE_DIR}"
mkdir -p "${RESOURCES_DIR}/python" "${RESOURCES_DIR}/previews"

export PYINSTALLER_CONFIG_DIR="${CACHE_DIR}/pyinstaller"
export PYTHONPYCACHEPREFIX="${CACHE_DIR}/pycache"

"${PYTHON_BIN}" -m PyInstaller \
  --noconfirm \
  --clean \
  --onefile \
  --name "${HELPER_NAME}" \
  --distpath "${DIST_DIR}" \
  --workpath "${WORK_DIR}" \
  --specpath "${SPEC_DIR}" \
  --collect-all pretty_midi \
  --collect-all mido \
  "${SHARED_ROOT}/midi_to_wave.py"

install -m 755 "${DIST_DIR}/${HELPER_NAME}" "${RESOURCES_DIR}/python/${HELPER_NAME}"
rm -rf "${RESOURCES_DIR}/previews"
mkdir -p "${RESOURCES_DIR}/previews"
cp -R "${HTML_ROOT}/static/previews/." "${RESOURCES_DIR}/previews/"
