# OctaBit Vue frontend

This is the intended production Vue 3 + TypeScript frontend for OctaBit. It is
a thin client over the Flask API in `../web-flask/`; it does not duplicate
workspace, upload, synthesis, download, preview, theme, or language behaviour.

The older Flask-rendered frontend remains in `../web-flask/` as a legacy
fallback, but normal production traffic should serve this app's Vite `dist`
build through Caddy.

## Development

Start the Flask backend on port 8000:

```bash
PORT=8000 WEB_FLASK_OPEN_BROWSER=0 ./.venv/bin/python3 apps/web-flask/app.py
```

In another terminal:

```bash
cd apps/web-vue
npm ci
npm run dev
```

Open `http://127.0.0.1:5173/`.

During development, Vite proxies `/api/*` and `/static/previews/*` to
`http://127.0.0.1:8000`.

## Build

```bash
cd apps/web-vue
npm ci
npm run build
```

The production build output is `apps/web-vue/dist`. The DigitalOcean production
model serves that directory directly with Caddy and reverse proxies `/api/*`,
`/static/previews/*`, and `/synthesise*` to Flask/Gunicorn on
`127.0.0.1:8000`. See `../../deploy/digitalocean/README.md`.
