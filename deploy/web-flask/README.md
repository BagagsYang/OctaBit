# Flask Web Docker Deployment

Language/语言: English | [简体中文](./README.zh-CN.md)

This deployment is for the browser-based OctaBit Flask app only. The image includes `apps/web-flask/`, the shared renderer entrypoint in `core/python-renderer/`, the shared preview WAV files in `assets/previews/`, and the project licence. It does not package the macOS or Windows desktop apps.

The compose file binds the container to `127.0.0.1:8000` on the server so the first deployment can be tested through SSH tunnelling before any public reverse proxy is added.

## Build and Start

From the repository root on the Debian server:

```bash
docker compose -f compose.web.yml up -d --build
```

Check the service:

```bash
docker compose -f compose.web.yml ps
```

When the container is healthy, `docker compose ps` should show the service as running with a healthy status.

Test it locally on the server:

```bash
curl http://127.0.0.1:8000
```

Follow logs:

```bash
docker compose -f compose.web.yml logs -f
```

## Test Through SSH Tunnel

From your Mac, open the tunnel:

```bash
ssh -p 22080 -N -L 18080:127.0.0.1:8000 debian@42.121.121.121
```

Then open this URL on your Mac:

```text
http://127.0.0.1:18080
```

## Stop

From the repository root on the Debian server:

```bash
docker compose -f compose.web.yml down
```

## Production Notes

- The container runs Gunicorn on `0.0.0.0:${PORT:-8000}` as a non-root user.
- The Dockerfile pins the Python base image by digest and installs from `deploy/web-flask/build-requirements.lock` plus `deploy/web-flask/requirements.lock` with pip hash verification. Regenerate the lock files intentionally when Python dependencies change.
- Background synthesis uses a bounded render pool. `WEB_RENDER_WORKERS` defaults to 2 active renders and `WEB_RENDER_QUEUE_SIZE` defaults to 8 waiting renders per container.
- The image default and `compose.web.yml` both set `GUNICORN_TIMEOUT=600`. This gives slow SSH tunnel downloads more time, while the browser still downloads the generated WAV only after the server has finished rendering it.
- The container includes a lightweight health check against `/` using Python's standard library, so no extra curl package is needed in the image.
- Anonymous workspace metadata, uploaded MIDI files, and generated WAV files live under `WEB_SYNTHESISE_JOB_ROOT`, defaulting to `/tmp/octabit-jobs`; the compose file mounts `/tmp` as a 1 GB in-memory tmpfs and no upload data is persisted.
- Workspace files are kept for `WEB_WORKSPACE_TTL_SECONDS` seconds after last activity, defaulting to 86400 seconds. The default caps are 20 queued files, 100 MiB active MIDI uploads, and 20 converted files per workspace.
- Legacy ready render jobs are kept for `WEB_DOWNLOAD_TTL_SECONDS` seconds, defaulting to 1800 seconds. When a user clears the queue or converted files list, the browser asks the server to delete the corresponding temporary files immediately.
- The host port is intentionally bound to `127.0.0.1:8000` for tunnel-only testing.
- For public deployment on `octabit.cc`, put Caddy or Nginx in front of this service and expose only ports 80 and 443 publicly. Keep the Flask/Gunicorn service private to the server or Docker network.
