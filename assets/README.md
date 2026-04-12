# Shared Assets

`assets/previews/` is the canonical source of waveform preview WAV files.

Usage:

- `apps/web-flask/` serves these files through a dedicated Flask route.
- `apps/macos/` copies these files into the app bundle at build time.
- `apps/windows/` links these files into the WinUI project at build and publish time.

## Preview Asset Provenance

The preview WAV files in `assets/previews/` are project-generated preview/test
assets created for waveform and timbre auditioning. They were rendered by this
project's own program from maintainer-directed MIDI test material. To the
maintainer's knowledge, they are not derived from third-party sample packs or
externally licensed audio recordings, and they are intended to be redistributed
with the project and its app outputs.
