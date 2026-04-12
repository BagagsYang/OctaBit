# Licensing Audit

Date checked: 2026-04-12

This report covers repository manifests and tracked bundled assets for the AGPLv3
adoption step. It does not apply UI notices or other runtime interface changes.

## Items checked

- `core/python-renderer/requirements.txt`
- `apps/web-flask/requirements.txt`
- `apps/macos/requirements-build.txt`
- `apps/windows/Directory.Packages.props`
- `apps/windows/src/Midi8BitSynthesiser.Core/Midi8BitSynthesiser.Core.csproj`
- `apps/windows/src/Midi8BitSynthesiser.App/Midi8BitSynthesiser.App.csproj`
- `apps/windows/tests/Midi8BitSynthesiser.Tests/Midi8BitSynthesiser.Tests.csproj`
- `global.json`
- `assets/previews/*.wav`
- `apps/windows/src/Midi8BitSynthesiser.App/Assets/Previews/*.wav`

## Dependencies

### Core Python renderer runtime

- `importlib_resources` 6.5.2: Apache-2.0 from installed package metadata. No
  obvious AGPL compatibility issue.
- `mido` 1.3.3: MIT from installed package metadata. No obvious AGPL
  compatibility issue.
- `numpy` 2.4.3: `BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0` from
  installed package metadata. No obvious AGPL compatibility issue.
- `packaging` 26.0: `Apache-2.0 OR BSD-2-Clause` from installed package
  metadata. No obvious AGPL compatibility issue.
- `pretty_midi` 0.2.11: MIT from installed package metadata. No obvious AGPL
  compatibility issue.
- `scipy` 1.17.1: BSD-style core license from installed package metadata. The
  installed wheel metadata also references bundled third-party libraries such as
  OpenBLAS (BSD-3-Clause), LAPACK (BSD-style), `libgfortran` (`GPL-3.0-or-later
  WITH GCC-exception-3.1`), and `libquadmath` (`LGPL-2.1-or-later`).
  Compatibility looks workable, but binary redistribution should preserve the
  upstream notices and warrants a dedicated packaging review.
- `setuptools` 82.0.1: MIT from installed package metadata. No obvious AGPL
  compatibility issue.
- `six` 1.17.0: MIT from installed package metadata. No obvious AGPL
  compatibility issue.

### Web Flask dependencies

- `Flask` 3.1.3, `Werkzeug` 3.1.7, `click` 8.3.1, `MarkupSafe` 3.0.3:
  BSD-3-Clause from installed package metadata. No obvious AGPL compatibility
  issue.
- `itsdangerous` 2.2.0 and `Jinja2` 3.1.6: BSD-style from installed package
  metadata. No obvious AGPL compatibility issue.
- `blinker` 1.9.0: MIT from installed package metadata. No obvious AGPL
  compatibility issue.

### macOS helper build dependencies

- `altgraph` 0.17.5 and `macholib` 1.16.4: MIT from installed package metadata.
  No obvious AGPL compatibility issue.
- `pyinstaller` 6.19.0: GPL-2.0-or-later with the PyInstaller special
  exception, from installed package metadata. This usually needs case-specific
  review for bundled application distribution, but it is not an immediate blocker
  for the repository-level relicensing step.
- `pyinstaller-hooks-contrib` 2026.3: mixed licensing from the installed
  package's bundled `LICENSE` file. Standard hooks are GPL-2.0-or-later; runtime
  hooks are Apache-2.0. Manual follow-up is required to confirm which hooks, if
  any, are shipped in distributed macOS helper artifacts.

### Windows/.NET dependencies

- `Melanchall.DryWetMidi` 8.0.3: MIT per the NuGet Gallery package page. No
  obvious AGPL compatibility issue.
- `NAudio` 2.3.0: MIT per the NuGet Gallery package page. No obvious AGPL
  compatibility issue.
- `Microsoft.NET.Test.Sdk` 18.3.0: MIT per the NuGet Gallery package page. Test
  dependency only.
- `xunit` 2.9.3: Apache-2.0 per the NuGet Gallery package page. Test dependency
  only.
- `xunit.runner.visualstudio` 3.1.5: the xUnit package pages describe xUnit.net
  as Apache-2.0 licensed, and this package is additionally marked
  `PrivateAssets=all` in the test project. Treat as test-only, but confirm the
  exact package license before any formal distribution audit.
- `Microsoft.WindowsAppSDK` 1.8.260317003: Microsoft Software License Terms from
  the NuGet Gallery license page, not an open-source permissive license. The
  redistributable code restrictions prohibit distributing source so that the
  Microsoft code becomes subject to a source-disclosure licence. This is a likely
  AGPL-compatibility concern for the Windows self-contained desktop app and needs
  manual legal review before that app is relicensed or redistributed under AGPL
  terms.

### Tooling manifest

- `global.json` pins the .NET SDK version (`8.0.100`) but does not itself add a
  redistributed third-party source or asset.

## Bundled assets

- The only tracked non-code media found in source-controlled, non-build
  directories for this step are the six waveform preview WAV files under
  `assets/previews/`.
- The copies under
  `apps/windows/src/Midi8BitSynthesiser.App/Assets/Previews/` are byte-for-byte
  identical to the canonical files in `assets/previews/`.
- Git history shows these preview files were introduced in the initial project
  import and later moved during the repository reorganisation, but no authoring,
  provenance, or licence note for the audio files was found in the repository.
- No tracked fonts, icon packs, or other third-party media were found in the
  repository outside build output directories.

## Manual follow-up required

- Confirm the provenance and intended licence of the preview WAV assets before
  asserting that they are covered by the repository AGPL terms.
- Review how `scipy` and any bundled native libraries are redistributed in app
  bundles, and preserve any required third-party notices.
- Review the exact macOS helper packaging output for `pyinstaller` and
  `pyinstaller-hooks-contrib`, especially if GPL-covered hooks are shipped.
- Review `Microsoft.WindowsAppSDK` licensing before applying AGPL-driven
  redistribution terms to the Windows app or its self-contained published output.
- Confirm the exact published license for `xunit.runner.visualstudio` when doing a
  distribution-grade dependency inventory, even though it currently appears to be
  test-only.
