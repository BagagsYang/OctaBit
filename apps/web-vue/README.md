# OctaBit Vue frontend

This is a parallel Vue 3 + TypeScript frontend for the existing Flask web API.
It does not replace the Flask template frontend yet.

## Development

Start the Flask backend on port 8000:

```bash
PORT=8000 WEB_FLASK_OPEN_BROWSER=0 ./.venv/bin/python3 apps/web-flask/app.py
```

In another terminal:

```bash
cd apps/web-vue
npm install
npm run dev
```

Open `http://127.0.0.1:5173/`.

During development, Vite proxies `/api/*` and `/static/previews/*` to
`http://127.0.0.1:8000`.

## Build

```bash
cd apps/web-vue
npm run build
```
