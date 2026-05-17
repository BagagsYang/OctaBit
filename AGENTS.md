# Repository Guidelines

## Project Structure & Module Organization

OctaBit is a monorepo focused on the web app. Work from the repository root unless a subproject README says otherwise.

- `apps/web-flask/`: active public Flask web UI, API routes, static CSS/JS, i18n catalogs, launchers, and `unittest` tests.
- `apps/web-vue/`: parallel Vue/Vite frontend scaffold that proxies to the Flask API; it is not the production entrypoint unless explicitly changed.
- `core/python-renderer/`: canonical MIDI-to-WAV renderer and renderer tests.
- `assets/previews/`: shared waveform preview WAV files.
- `deploy/web-flask/`, `compose.web.yml`, and `docs/`: deployment and API documentation.
- `apps/macos/` and `apps/windows/`: deprecated/paused native apps retained for reference.

## Build, Test, and Development Commands

Create a local Python environment:

```bash
python3 -m venv .venv
```

Install only the dependencies for the area you touch:

```bash
./.venv/bin/python3 -m pip install -r apps/web-flask/requirements.txt
./.venv/bin/python3 -m pip install -r core/python-renderer/requirements.txt
```

Run the active Flask app:

```bash
./.venv/bin/python3 apps/web-flask/app.py
```

Run the Vue scaffold when needed:

```bash
cd apps/web-vue
npm install
npm run dev
npm run build
```

## Coding Style & Naming Conventions

Prefer small, localized changes. Keep shared synthesis behavior in `core/python-renderer/`. For web UI strings, use `apps/web-flask/i18n/*.json` instead of hardcoding text in templates or JavaScript. Keep English as fallback and align `en.json`, `fr.json`, and `zh-CN.json` keys. Use descriptive Python names, TypeScript component names in PascalCase, and existing file naming patterns.

## Testing Guidelines

Run checks for the touched area and report skipped checks.

```bash
./.venv/bin/python3 -m unittest discover -s apps/web-flask/tests
./.venv/bin/python3 -m unittest discover -s core/python-renderer/tests
cd apps/web-vue && npm run build
```

Name Python tests `test_*.py`. For web API or localization changes, add render-level or endpoint assertions where practical.

## Commit & Pull Request Guidelines

Recent history uses short imperative messages and lightweight prefixes such as `feat:`, `fix:`, and `docs:`. Keep commits focused, for example `fix: prevent duplicate waveform layers`.

Pull requests should include a clear summary, touched areas, user-facing or deployment impact, screenshots for visible UI changes, linked issues when relevant, and the exact checks run. Note source and license details for new dependencies, vendored assets, or generated media.

## Agent-Specific Instructions

Treat `apps/web-flask/` as the current public app. Do not reframe it as legacy. Do not modify paused native apps unless the task explicitly targets them. Preserve existing behavior unless the request asks for a UI, API, or renderer change.
