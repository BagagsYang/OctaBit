# Windows App

This folder contains the native Windows desktop rewrite of the MIDI-8bit Synthesiser.

## Responsibilities

- WinUI 3 desktop interface for Windows
- Native queue, layer editing, preview, and export workflow
- C# port of the shared synthesis contract
- Windows CI publish pipeline for a portable `win-x64` bundle

## Project Layout

- `src/Midi8BitSynthesiser.Core/`: rendering engine, waveform models, output naming
- `src/Midi8BitSynthesiser.App/`: WinUI 3 shell, file dialog integration, preview playback
- `tests/Midi8BitSynthesiser.Tests/`: unit tests, workflow tests, Python parity tests

## Build On Windows

1. Install .NET 8 SDK and the Visual Studio components required for WinUI 3 desktop development.
2. Install Python 3 and the shared synthesis requirements:
   `python -m pip install -r ../shared/requirements.txt`
3. Restore, build, and test:
   `dotnet restore Midi8BitSynthesiser.sln`
   `dotnet build Midi8BitSynthesiser.sln -c Release -p:Platform=x64`
   `dotnet test Midi8BitSynthesiser.sln -c Release -p:Platform=x64 --no-build`
4. Publish the portable bundle:
   `dotnet publish src/Midi8BitSynthesiser.App/Midi8BitSynthesiser.App.csproj -c Release -r win-x64 --self-contained true -p:Platform=x64`

The published folder contains the main `.exe`, runtime files, and bundled waveform preview assets. Users can unzip the folder and launch the executable directly.

## Runtime Requirements For End Users

The published Windows release is self-contained.

End users need:
- a supported 64-bit Windows installation
- the published app files from the portable zip or installer

End users do **not** need:
- the .NET SDK
- a local source checkout
- Python

## Build Requirements For Developers And Reviewers

Build, test, and publish still require:
- .NET 8 SDK
- WinUI 3 compatible Visual Studio components
- Python 3
- `shared/requirements.txt` installed for parity tests

## Reviewer Preflight

Before reporting Windows build or runtime failures, confirm the review machine can actually validate the app:

- `dotnet --info`
- `python --version`
- `python -c "import pretty_midi, numpy, scipy"`

The detailed checklist lives in `REVIEWING.md`.

## Review Bundle

To prepare a bundle for an external Windows review, run:

```bash
windows-app/scripts/create_review_bundle.sh
```

The bundle includes:
- `windows-app/`
- `shared/`
- `.github/workflows/windows-release.yml`
- `global.json`

## Installer And Portable Release

The Windows release now ships in two forms:
- a portable self-contained zip for manual distribution and review
- an Inno Setup installer for ordinary end users

Both are built from the same published `win-x64` output.

## Compatibility Troubleshooting

- Unsupported Windows version:
  Use Windows `10.0.17763.0` or newer for this release.
- Wrong architecture:
  This release is `win-x64` only.
- Missing bundled files:
  Reinstall from a complete published zip or installer package.
- Export blocked by folder permissions:
  Choose a writable output folder and confirm the current user can write to `%TEMP%`.

## Release Validation

After CI builds the release, validate on a clean supported Windows machine:
- install or unzip the release without installing the .NET SDK
- launch the app
- confirm the compatibility check passes
- import a MIDI file, preview a layer, and export a WAV successfully
