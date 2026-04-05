# Shared Runtime

This folder contains the cross-platform synthesis core used by all application variants.

## Public Interface

- Module: `midi_to_wave.py`
- Primary function: `midi_to_audio(midi_path, output_path, sample_rate=48000, layers=None)`
- CLI entrypoint:
  - positional args: input MIDI path, output WAV path
  - options: `--type`, `--duty`, `--rate`, `--layers-json`

## Contract

- Inputs are platform-neutral file paths plus waveform configuration
- Output is a rendered WAV file written to disk
- Invalid configuration should fail with an explicit error instead of falling back silently, except for the documented default single pulse layer when no audible layers are supplied

UI code, packaging code, and platform-specific launch behavior should stay outside this folder.
