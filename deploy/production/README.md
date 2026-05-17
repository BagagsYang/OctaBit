# Vue Production Deployment

This is the intended non-Docker production path for `octabit.cc`.

- Caddy serves the built Vue 3 frontend from `apps/web-vue/dist`.
- Caddy reverse proxies `/api/*`, `/static/previews/*`, and `/synthesise*` to
  Flask/Gunicorn on `127.0.0.1:8000`.
- Flask/Gunicorn remains the private backend for workspace, upload, synthesis,
  download, preview asset, and legacy compatibility routes.
- The Flask-rendered page remains in the repository and can be restored by
  switching Caddy back to full reverse proxy mode.

The Docker files in `deploy/web-flask/` are an alternate Flask-backend or
legacy fallback path. Do not introduce Docker into the current production
cutover unless the production plan changes.

## One-Time Server Shape

Use a repository checkout such as `/home/deploy/octabit`, a repo-local Python virtual
environment, the `octabit-web` systemd service for Gunicorn, and Caddy as the
public server.

Gunicorn should stay private:

```bash
/home/deploy/octabit/.venv/bin/python3 -m gunicorn --chdir /home/deploy/octabit/apps/web-flask --bind 127.0.0.1:8000 --workers 2 --timeout 600 app:app
```

Install Node.js and npm from the server's normal package source before the Vue
cutover. The Vue dependency install should use the lockfile:

```bash
cd /home/deploy/octabit/apps/web-vue
npm ci
npm run build
```

## Caddy Routing

Use `Caddyfile.vue-production` as the production model:

```caddyfile
octabit.cc {
	encode zstd gzip

	handle /api/* {
		reverse_proxy 127.0.0.1:8000
	}

	handle /static/previews/* {
		reverse_proxy 127.0.0.1:8000
	}

	handle /synthesise* {
		reverse_proxy 127.0.0.1:8000
	}

	handle {
		root * /home/deploy/octabit/apps/web-vue/dist
		try_files {path} /index.html
		file_server
	}
}
```

This keeps the Vue app as the public frontend while preserving the Flask API,
preview audio route, and legacy synthesis routes. The `try_files` fallback is
for Vue/Vite browser routes and should not catch API requests because those are
handled first.

## Deployment Flow

From the production VM:

```bash
cd /home/deploy/octabit
git fetch --prune origin
git checkout main
git pull --ff-only origin main
./.venv/bin/python3 -m pip install -r apps/web-flask/requirements.txt
cd apps/web-vue
npm ci
npm run build
cd /home/deploy/octabit
sudo systemctl restart octabit-web
sudo caddy validate --config /etc/caddy/Caddyfile
sudo systemctl reload caddy
```

If deploying this branch before merge, set `BRANCH=feature/vue-frontend` when
using the helper script:

```bash
BRANCH=feature/vue-frontend deploy/production/deploy-vue-production.sh
```

After merge, the default helper script target is `main`:

```bash
deploy/production/deploy-vue-production.sh
```

Set `APP_DIR=/path/to/octabit` if the production checkout uses a different
path.

## Smoke Checks

Run local checks on the VM:

```bash
curl -fsS http://127.0.0.1:8000/api/health
test -f /home/deploy/octabit/apps/web-vue/dist/index.html
```

Run public checks after Caddy reload:

```bash
curl -fsS https://octabit.cc/
curl -fsS https://octabit.cc/api/health
curl -fsSI https://octabit.cc/static/previews/pulse_50.wav
```

Then use a browser to upload a small MIDI file, verify the workspace survives a
refresh, run synthesis, download the WAV, change theme/language, and clear the
queued/converted files.

## Rollback

If Vue production serving fails, keep the Flask backend running and replace the
Caddy site block with `Caddyfile.flask-fallback`:

```caddyfile
octabit.cc {
	encode zstd gzip
	reverse_proxy 127.0.0.1:8000
}
```

Validate and reload Caddy:

```bash
sudo caddy validate --config /etc/caddy/Caddyfile
sudo systemctl reload caddy
```

That restores the legacy Flask-rendered frontend while keeping the same
Gunicorn backend, API, workspace storage, and synthesis paths.
