# Repository layout

Language/语言: English | [简体中文](./repository-layout.zh-CN.md)

This repository is a monorepo for the MIDI-8bit Synthesiser product family. It
contains the public Flask web app, native macOS and Windows apps, the canonical
Python renderer, shared preview assets, deployment files, and release
documentation.

## Top-level map

| Path | Purpose |
| --- | --- |
| `AGENTS.md` | Repository instructions for coding agents and local workflows. |
| `README.md`, `README.zh-CN.md` | Root project overview, setup notes, app entry points, and repository licence summary. |
| `LICENSE.md` | Repository AGPL licence text. |
| `apps/` | Platform app targets and the reserved desktop placeholder. |
| `core/python-renderer/` | Canonical Python MIDI-to-WAV renderer and parity reference. |
| `assets/previews/` | Canonical waveform preview WAV files shared by the apps. |
| `docs/` | Repository layout notes, licensing audit, and review reports. |
| `deploy/web-flask/` | Docker deployment documentation and Dockerfile for the Flask web app. |
| `.github/workflows/` | GitHub Actions workflow for Windows release builds. |
| `compose.web.yml` | Docker Compose entry point for the Flask web deployment. |
| `global.json` | .NET SDK selection for the Windows solution. |
| `.dockerignore`, `.gitignore`, `.gitattributes` | Repository packaging, ignore, and line-ending rules. |
| `output/`, `tmp/` | Tracked historical generated review artefacts; both paths are ignored for future generated output. |

Local-only folders such as `.venv/`, build outputs, `.codex/`, `.sisyphus/`,
`.DS_Store`, `__pycache__/`, `.xcodebuild/`, and app `build/` folders are not
part of the maintained source layout.

## App targets

### `apps/web-flask/`

Primary Flask/browser UI for the project.

- `app.py`: Flask entry point, upload handling, synthesis endpoints, preview
  routes, and server-side render job endpoints.
- `templates/index.html`: browser UI shell.
- `static/css/` and `static/js/`: web-specific styling and browser behaviour.
- `i18n/`: JSON catalogues for English, French, and Simplified Chinese UI text.
- `tests/`: Flask and render-path tests.
- `requirements.txt`: web runtime dependencies; it includes the shared renderer
  requirements.
- `Launch_Synthesiser.command` and `Launch_Synthesiser.bat`: local launchers.
- `README.md`, `README.zh-CN.md`, `User_Guide.txt`: web app documentation.

The web app delegates synthesis to `core/python-renderer/midi_to_wave.py` and
serves preview audio from `assets/previews/`.

### `apps/macos/`

Native SwiftUI macOS app and Xcode project.

- `MIDI8BitSynthesiser.xcodeproj/`: Xcode project and shared scheme.
- `MIDI8BitSynthesiser/`: SwiftUI app source.
- `MIDI8BitSynthesiserTests/`: XCTest target for model and filename logic.
- `macos/build_desktop_resources.sh`: Xcode build-phase script that freezes the
  Python renderer into a helper binary and copies preview WAV assets into the
  app bundle.
- `requirements-build.txt`: Python build dependencies for the helper.
- `macos/README.md`, `macos/README.zh-CN.md`: macOS build and usage notes.

The macOS app does not run the Flask server. It launches the bundled Python
helper for each queued MIDI file.

### `apps/windows/`

Native WinUI 3 Windows app, C# renderer, tests, installer, and review tooling.

- `Midi8BitSynthesiser.sln`: Windows solution.
- `Directory.Packages.props`: central NuGet package versions.
- `src/Midi8BitSynthesiser.Core/`: C# rendering engine, waveform models, and
  output naming.
- `src/Midi8BitSynthesiser.App/`: WinUI 3 shell, compatibility checks, file
  dialog services, preview playback, localisation resources, and app manifest.
- `tests/Midi8BitSynthesiser.Tests/`: unit, workflow, compatibility, and Python
  parity tests.
- `installer/Midi8BitSynthesiser.iss`: Inno Setup installer script.
- `installer/RuntimeNotice.txt`: installer pre-install runtime notice.
- `scripts/create_review_bundle.sh`: script for preparing a Windows review
  bundle.
- `README.md`, `README.zh-CN.md`, `REVIEWING.md`: Windows build, review, and
  release documentation.

The Windows app has its own C# renderer and validates it against the Python
reference renderer in parity tests. The app project links preview WAV files from
the canonical `assets/previews/` folder for build and publish output. A
byte-identical tracked copy also exists under
`src/Midi8BitSynthesiser.App/Assets/Previews/`, but the project file uses the
shared asset folder as the current build source.

### `apps/desktop/`

Reserved placeholder for a future desktop packaging layer. It contains README
files only and no app implementation.

## Shared core and assets

### `core/python-renderer/`

Canonical Python MIDI-to-WAV renderer.

- `midi_to_wave.py`: renderer module and CLI entry point.
- `requirements.txt`: renderer/runtime dependencies only.
- `tests/`: renderer tests.
- `README.md`: renderer interface, layer schema, and dependency boundary.

The renderer accepts platform-neutral file paths and waveform layer settings,
then writes a WAV file to disk. Web and macOS call it directly; Windows uses it
as the parity reference for the native C# renderer.

### `assets/previews/`

Canonical preview WAV assets used by the web, macOS, and Windows app paths.
`assets/README.md` records their intended usage and provenance.

## Documentation and generated artefacts

- `docs/repository-layout.md` and `docs/repository-layout.zh-CN.md`: current
  repository layout in English and Simplified Chinese.
- `docs/licensing-audit.md`: licensing and attribution audit for repository and
  release planning.
- `docs/reviews/windows-app-review.md`: Windows review notes.
- `output/pdf/repo-structure-evaluation.pdf`,
  `tmp/pdfs/repo-structure-evaluation.html`, and
  `tmp/pdfs/rendered/repo-structure-evaluation.png`: tracked historical
  generated review artefacts. They are not the source of truth for the current
  layout.

## Build and development flow

Run commands from the repository root unless a document says otherwise.

Create the local Python environment:

```bash
python3 -m venv .venv
```

Install only the dependencies for the area being worked on:

```bash
./.venv/bin/python3 -m pip install -r apps/web-flask/requirements.txt
./.venv/bin/python3 -m pip install -r apps/macos/requirements-build.txt
./.venv/bin/python3 -m pip install -r core/python-renderer/requirements.txt
```

Common checks:

```bash
./.venv/bin/python3 -m unittest discover -s apps/web-flask/tests
./.venv/bin/python3 -m unittest discover -s core/python-renderer/tests
```

Windows development uses .NET 8 and Python renderer dependencies:

```powershell
dotnet restore apps/windows/Midi8BitSynthesiser.sln
dotnet build apps/windows/Midi8BitSynthesiser.sln -c Release -p:Platform=x64
dotnet test apps/windows/Midi8BitSynthesiser.sln -c Release -p:Platform=x64 --no-build
```

Windows publishing uses:

```powershell
dotnet publish apps/windows/src/Midi8BitSynthesiser.App/Midi8BitSynthesiser.App.csproj -c Release -r win-x64 --self-contained true -p:Platform=x64
```

macOS builds run through Xcode with the `MIDI8BitSynthesiser` scheme. The Xcode
build phase runs `apps/macos/macos/build_desktop_resources.sh`.

The Flask Docker deployment uses:

```bash
docker compose -f compose.web.yml up -d --build
```

The compose file binds the service to `127.0.0.1:8000` for tunnel-first testing
and builds only the Flask web app, shared renderer, shared preview assets, and
project licence into the image.

## Dependency and packaging boundaries

- Python renderer dependencies live in `core/python-renderer/requirements.txt`.
- Web-only Python dependencies live in `apps/web-flask/requirements.txt`.
- macOS helper build dependencies live in `apps/macos/requirements-build.txt`.
- Windows NuGet versions live in `apps/windows/Directory.Packages.props`.
- There is no JavaScript package manager metadata in this checkout; the web app
  currently uses static local JavaScript/CSS plus external Bootstrap and Google
  Fonts links from the HTML template.
- Docker deployment files are scoped to `apps/web-flask/`.
- Native app packaging stays under the relevant app folder.

## Ownership boundaries

- Shared renderer behaviour belongs in `core/python-renderer/`.
- Platform-specific UI, launch, packaging, and release logic belongs under
  `apps/`.
- Shared binary/media assets belong under `assets/`.
- Repository-wide documentation, audits, and review notes belong under `docs/`.
- Deployment-specific files belong under `deploy/` and root deployment entry
  points such as `compose.web.yml`.
