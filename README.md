# OctaBit

Language/语言: English | [简体中文](./README.zh-CN.md)

OctaBit is a simple web tool for converting MIDI files into 8-bit style music. The official site is `https://octabit.cc`.

This repository is a reorganised monorepo for OctaBit. The current active target is the Flask/Gunicorn web service in `apps/web-flask/`, packaged for server deployment with Docker. The native macOS and Windows apps are deprecated/paused, not actively developed, and kept in the repository for reference or possible future revival. The Python reference renderer lives under `core/`, and shared preview assets live under `assets/`.

## Layout

| Folder | Responsibility |
| --- | --- |
| `apps/web-flask/` | Current active Flask/browser UI and deployable web service |
| `apps/macos/` | Deprecated/paused native macOS SwiftUI app and Xcode project, retained for reference |
| `apps/windows/` | Deprecated/paused native Windows WinUI 3 solution, C# renderer, installer, retained for reference |
| `apps/desktop/` | Reserved placeholder for future desktop packaging work |
| `core/python-renderer/` | Canonical Python MIDI-to-WAV renderer and parity reference |
| `assets/previews/` | Canonical waveform preview WAV files used by the web app and retained native app code |
| `docs/` | Reviews and repository structure notes |

## Shared renderer

- Canonical renderer entrypoint: `core/python-renderer/midi_to_wave.py`
- Stable inputs: MIDI path, output WAV path, sample rate, waveform layers
- Stable output: rendered WAV file or explicit error
- The retained Windows code includes a native C# implementation that validates against the Python renderer in parity tests

## Build notes

Create the repo-local environment at the repository root:

```bash
python3 -m venv .venv
```

Install only the dependencies needed for the area you are working on:

- Web UI: `./.venv/bin/python3 -m pip install -r apps/web-flask/requirements.txt`
- macOS helper build, if inspecting the paused native app: `./.venv/bin/python3 -m pip install -r apps/macos/requirements-build.txt`
- Windows parity tests, if inspecting the paused native app: `./.venv/bin/python3 -m pip install -r core/python-renderer/requirements.txt`

App-specific instructions live in:

- `apps/web-flask/README.md`
- `apps/macos/macos/README.md`
- `apps/windows/README.md`

Repository layout notes live in `docs/repository-layout.md`.

## License

This project is licensed under the GNU Affero General Public License v3.0 or later (`AGPL-3.0-or-later`). See the [LICENSE](LICENSE.md) file for full details.
