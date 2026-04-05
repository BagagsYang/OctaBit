## Build

1. Install full Xcode.
2. Recreate or refresh the repo-local virtual environment:
   `python3 -m venv .venv`
3. Install the pinned Python packages with:
   `./.venv/bin/python3 -m pip install -r shared/requirements.txt`
4. Open `macos-app/MIDI8BitSynthesiser.xcodeproj` and run the `MIDI8BitSynthesiser` scheme.

## How the app works

- SwiftUI provides the native macOS interface and follows system appearance automatically.
- The Xcode build phase runs [`build_desktop_resources.sh`](/Users/yangyi/Programming/midi-8bit converter/macos-app/macos/build_desktop_resources.sh).
- That script freezes [`midi_to_wave.py`](/Users/yangyi/Programming/midi-8bit converter/shared/midi_to_wave.py) into a bundled helper binary with PyInstaller and copies the preview WAV assets from [`html-app/static/previews`](/Users/yangyi/Programming/midi-8bit converter/html-app/static/previews) into the app bundle.
- The app launches the bundled helper directly for each queued MIDI file, so no Flask server or browser is involved.
