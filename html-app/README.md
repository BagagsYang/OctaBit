# HTML App

This folder contains the browser-distributed version of the MIDI-8bit Synthesiser.

## Responsibilities

- Flask entrypoint and request handling
- HTML templates and static assets
- Legacy browser launcher
- Web-specific build artifacts and previews

## Run

From the repository root:

```bash
python3 -m venv .venv
./.venv/bin/python3 -m pip install -r shared/requirements.txt
./.venv/bin/python3 html-app/app.py
```

Or launch the legacy helper script:

```bash
html-app/Launch_Synthesiser.command
```

## Shared Dependency

This variant imports the synthesis core from `../shared/midi_to_wave.py`. Platform-specific code in this folder should not duplicate synthesis behavior.
