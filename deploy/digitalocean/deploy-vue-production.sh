#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${REPO_DIR:-/srv/octabit}"
BRANCH="${BRANCH:-main}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR="${VENV_DIR:-$REPO_DIR/.venv}"
FLASK_SERVICE="${FLASK_SERVICE:-octabit-web}"
CADDY_CONFIG="${CADDY_CONFIG:-/etc/caddy/Caddyfile}"
RELOAD_CADDY="${RELOAD_CADDY:-1}"

cd "$REPO_DIR"

git fetch --prune origin "$BRANCH"
git checkout "$BRANCH"
git pull --ff-only origin "$BRANCH"

if [ ! -x "$VENV_DIR/bin/python3" ]; then
	"$PYTHON_BIN" -m venv "$VENV_DIR"
fi

"$VENV_DIR/bin/python3" -m pip install -r apps/web-flask/requirements.txt

cd apps/web-vue
npm ci
npm run build
cd "$REPO_DIR"

sudo systemctl restart "$FLASK_SERVICE"
sudo systemctl status "$FLASK_SERVICE" --no-pager --lines=20

curl -fsS http://127.0.0.1:8000/api/health

if [ "$RELOAD_CADDY" = "1" ]; then
	sudo caddy validate --config "$CADDY_CONFIG"
	sudo systemctl reload caddy
fi
