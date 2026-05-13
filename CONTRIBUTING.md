# Contributing to OctaBit

Language/语言: English | [简体中文](./CONTRIBUTING.zh-CN.md)

Thank you for helping improve OctaBit. This guide explains where contributions
fit in the repository, when to open an issue first, and what to include in a
pull request.

## Start with the right area

OctaBit is a monorepo. The current active contribution targets are:

- `apps/web-flask/`: the active public Flask/browser UI and deployable web
  service.
- `core/python-renderer/`: the canonical Python MIDI-to-WAV renderer.
- `docs/`, `deploy/web-flask/`, and `assets/previews/`: supporting
  documentation, deployment, and shared asset areas.

The native macOS and Windows apps under `apps/macos/` and `apps/windows/` are
paused/reference areas. Please open an issue before starting substantial work
there so maintainers can confirm the scope.

For a fuller map of the repository, see [docs/repository-layout.md](./docs/repository-layout.md).

## Before you start

Small documentation fixes and narrow bug fixes may go straight to a pull
request.

Please open an issue first for substantial changes, including:

- public web UI or workflow changes;
- renderer behavior, renderer schema, or output naming changes;
- deployment, Docker, or server runtime changes;
- architecture, repository layout, or dependency changes;
- licensing-sensitive work, vendored assets, generated media, or new third-party
  material;
- macOS or Windows app changes.

In the issue, describe the problem, the intended behavior, and the area of the
repository you expect to touch.

## Development setup

Run commands from the repository root unless a document says otherwise.

Create the local Python environment:

```bash
python3 -m venv .venv
```

Install only the dependencies needed for the area you are touching:

```bash
./.venv/bin/python3 -m pip install -r apps/web-flask/requirements.txt
./.venv/bin/python3 -m pip install -r core/python-renderer/requirements.txt
```

For app-specific notes, start with:

- [apps/web-flask/README.md](./apps/web-flask/README.md)
- [core/python-renderer/README.md](./core/python-renderer/README.md)
- [deploy/web-flask/README.md](./deploy/web-flask/README.md)

## Making changes

- Keep the Flask web app as the primary public app target.
- Keep shared synthesis behavior in `core/python-renderer/` unless the change is
  explicitly app-specific.
- Do not duplicate app source trees for localisation. Use the existing
  localisation resources for the touched platform.
- For `apps/web-flask/`, prefer `i18n/*.json` plus separate static JS/CSS over
  adding large inline scripts or hardcoded user-facing strings in templates.
- Keep English and Simplified Chinese documentation pairs aligned when changing
  paired docs.
- Avoid unrelated refactors in feature or bug-fix pull requests.

## Pull request checklist

Before opening a pull request, make sure it includes:

- a clear summary of the problem and the change;
- the main repository areas touched;
- any user-facing behavior, UI, deployment, or compatibility impact;
- screenshots or short notes for visible web UI changes;
- the checks you ran, plus any relevant checks you could not run;
- provenance and license notes for new dependencies, vendored assets, generated
  media, or other third-party material.

## Validation

Run the checks relevant to the area you touched and report the result in the
pull request.

For the web app:

```bash
./.venv/bin/python3 -m unittest discover -s apps/web-flask/tests
```

For the Python renderer:

```bash
./.venv/bin/python3 -m unittest discover -s core/python-renderer/tests
```

For documentation-only changes, proofread the affected files and keep English
and Chinese versions aligned when both exist.

For deployment changes, include static review of the changed deployment files
and any available Docker or Compose validation.

For native app changes, run the checks documented in the relevant app README
when your machine has the required tools. If you cannot run a check because the
environment is missing Xcode, .NET, Docker, or another dependency, say that in
the pull request.

## Licensing and provenance

OctaBit is licensed under the GNU Affero General Public License v3.0 or later
(`AGPL-3.0-or-later`). See [LICENSE.md](./LICENSE.md).

By contributing, you confirm that you have the right to submit your code,
documentation, assets, and other materials, and that they are compatible with
the repository license. For new dependencies, vendored assets, generated media,
or licensing-sensitive files, include the source and license information in the
pull request.
