# MIDI-8bit Synthesiser

This repository is organised by deliverable so each published version can be built, documented, and released independently while reusing the same synthesis engine.

## Variant Matrix

| Folder | Target system | Owns |
| --- | --- | --- |
| `html-app/` | Browser / Flask | Web entrypoint, templates, static assets, legacy launcher, web build artifacts |
| `macos-app/` | Native macOS | Xcode project, SwiftUI app, macOS build script, app bundle resources |
| `windows-app/` | Native Windows | WinUI 3 solution, C# synthesis engine, Windows build/publish pipeline |
| `shared/` | Cross-platform runtime | MIDI-to-WAV synthesis logic and shared Python dependencies |

## Shared Core Contract

- Canonical synthesis module: `shared/midi_to_wave.py`
- Stable inputs: MIDI path, output WAV path, sample rate, waveform layers
- Stable output: rendered WAV file or explicit error
- Platform folders may own UI, packaging, and release workflows, but should not reimplement synthesis unless the platform requires a deliberate fork

## Build Notes

- Create the repo-local environment at the repository root:
  - `python3 -m venv .venv`
  - `./.venv/bin/python3 -m pip install -r shared/requirements.txt`
- Browser variant instructions live in `html-app/`
- macOS variant instructions live in `macos-app/macos/README.md`
- Windows variant instructions live in `windows-app/README.md`

## Future Variants

Additional platform ports should follow the same pattern: add a new top-level app folder for platform-specific code and continue importing or bundling `shared/` unless a hard platform constraint requires a separate runtime implementation.
