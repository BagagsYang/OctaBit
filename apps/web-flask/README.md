# Web Flask app

Language/语言: English | [简体中文](./README.zh-CN.md)

This folder contains the Flask backend for OctaBit and the legacy Flask-rendered
frontend fallback. The public production frontend is now the Vue app in
`../web-vue/`, served from its Vite `dist` build.

## Responsibilities

- Flask entrypoint and request handling
- Backend API routes for workspace, upload, synthesis, download, and preview assets
- HTML templates and web-specific static assets for the legacy Flask-rendered fallback
- Launcher script
- Synthesis delegation to the Python renderer in `../../core/python-renderer/`

## Run

From the repository root:

```bash
python3 -m venv .venv
./.venv/bin/python3 -m pip install -r apps/web-flask/requirements.txt
./.venv/bin/python3 apps/web-flask/app.py
```

Or launch the helper script:

```bash
apps/web-flask/Launch_Synthesiser.command
```

On Windows, use:

```bat
apps\web-flask\Launch_Synthesiser.bat
```

## Shared dependencies

- Renderer: `../../core/python-renderer/midi_to_wave.py`
- Canonical preview assets: `../../assets/previews/`

This app serves preview WAVs from the shared asset folder and should not duplicate renderer logic.

## Current API contract

The production Vue frontend and legacy Flask-rendered fallback use
cookie-backed anonymous temporary workspaces. Uploaded MIDI
files, sound configuration, and converted WAV links are restored through
`/api/workspace` after refresh. The full contract lives in
`../../docs/api-contract.md`.

Current API routes:

- `GET /api/health`: lightweight JSON health check.
- `GET /api/workspace`: creates or restores the anonymous temporary workspace.
- `POST /api/workspace/uploads`: stores one queued `.mid` or `.midi` upload.
- `DELETE /api/workspace/uploads/<file_id>`: deletes an owned queued upload.
- `PATCH /api/workspace/queue`: persists queue order.
- `PUT /api/workspace/config`: persists sample rate and layer controls.
- `POST /api/synthesis-jobs`: accepts an owned `file_id` plus workspace config
  and returns a job id; the older multipart API shape is still accepted for
  compatibility.
- `GET /api/synthesis-jobs/<job_id>`: reports queued, rendering, ready, failed, or expired status for an owned job.
- `GET /api/synthesis-jobs/<job_id>/download`: downloads the ready WAV file.
- `DELETE /api/synthesis-jobs/<job_id>`: removes an owned temporary server file when a user clears converted files.

Compatibility routes:

- `POST /synthesise`: single-request upload, render, and download path.
- `POST /synthesise/jobs`: accepts the same form fields and returns a job id.
- `GET /synthesise/jobs/<job_id>`: reports queued, rendering, ready, failed, or expired status.
- `GET /synthesise/jobs/<job_id>/download`: downloads the ready WAV file.
- `DELETE /synthesise/jobs/<job_id>`: removes the temporary server file when a user clears converted files.

Workspace files are temporary and expire after `WEB_WORKSPACE_TTL_SECONDS`, which
defaults to 86400 seconds. The browser deletes queued uploads or converted WAVs
immediately when the user clears those lists.

API errors use `{"error":{"code":"...","message":"..."}}`. Compatibility routes
keep their existing `{"error":"..."}` response shape unless they are explicitly
migrated later.

## Production notes

The intended production model can run without Docker:

- Install `apps/web-flask/requirements.txt` into the repo-local virtual environment.
- Run Gunicorn against `app:app` from `apps/web-flask/`.
- Bind Gunicorn privately to `127.0.0.1:8000`.
- Manage Gunicorn with systemd, for example through the `octabit-web` service.
- Build the Vue frontend with `npm ci && npm run build` in `../web-vue/`.
- Use Caddy to serve `../web-vue/dist` publicly and reverse proxy `/api/*`,
  `/static/previews/*`, and `/synthesise*` to `127.0.0.1:8000`.
- Keep `WEB_SYNTHESISE_JOB_ROOT`, `WEB_WORKSPACE_TTL_SECONDS`,
  `WEB_WORKSPACE_MAX_QUEUED_FILES`, `WEB_WORKSPACE_MAX_UPLOAD_BYTES`,
  `WEB_WORKSPACE_MAX_CONVERTED_FILES`, `WEB_DOWNLOAD_TTL_SECONDS`,
  `WEB_MAX_UPLOAD_BYTES`, and the Gunicorn timeout aligned with expected upload,
  render, and download behaviour.

Example Gunicorn shape:

```bash
./.venv/bin/python3 -m gunicorn --chdir apps/web-flask --bind 127.0.0.1:8000 --workers 2 --timeout 600 app:app
```

The Docker files under `../../deploy/web-flask/` and `../../compose.web.yml`
remain an alternate Flask-backend or legacy Flask-rendered fallback deployment
path. The current DigitalOcean production path is documented in
`../../deploy/digitalocean/README.md`.

## Output naming

- Single audible layer without a curve: `<original>_<wave>.wav`
- Multiple audible layers without a curve: `<original>_mix.wav`
- Any audible layer with a non-empty frequency curve: `<original>_<base>_<hash>.wav`

The hash is derived from the sanitised layer payload so different curve settings do not reuse the same export name.
