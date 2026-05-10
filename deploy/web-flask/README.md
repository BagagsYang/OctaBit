# Flask Web Docker Deployment

Language/语言: English | [简体中文](./README.zh-CN.md)

This deployment is for the browser-based Flask app only. The image includes `apps/web-flask/`, the shared renderer entrypoint in `core/python-renderer/`, the shared preview WAV files in `assets/previews/`, and the project licence. It does not package the macOS or Windows desktop apps.

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
- Gunicorn is configured with a 600 second timeout in `compose.web.yml`. This gives slow SSH tunnel downloads more time, but the browser still downloads the generated WAV after the server has finished rendering it.
- Uploaded MIDI files, generated WAV files, and short-lived render job metadata are temporary files under `/tmp`; the compose file mounts `/tmp` as an in-memory tmpfs and no upload data is persisted.
- Ready render jobs are kept for `WEB_DOWNLOAD_TTL_SECONDS` seconds, defaulting to 1800 seconds, so a user can retry a timed-out WAV download without rendering again. When a user clears the converted files list, the browser asks the server to delete those ready files immediately.
- The host port is intentionally bound to `127.0.0.1:8000` for tunnel-only testing.
- For public deployment later, put Caddy or Nginx in front of this service and expose only ports 80 and 443 publicly. Keep the Flask/Gunicorn service private to the server or Docker network.
