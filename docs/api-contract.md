# Web API contract

Language/语言: English | [简体中文](./api-contract.zh-CN.md)

This document describes the browser-facing API boundary for the current
Flask/Gunicorn OctaBit web service. The web UI is still server-rendered by
Flask, and synthesis still uses the canonical Python renderer in
`core/python-renderer/`.

## Scope

- New frontend code should use the `/api/*` routes.
- Legacy `/synthesise*` routes remain for compatibility.
- Render jobs are filesystem-backed; there is no database.
- Job ids are random UUID hex strings and should be treated as bearer tokens.

## Common formats

API errors use this JSON shape:

```json
{
  "error": {
    "code": "invalid_layers",
    "message": "Layer 1 frequency_curve frequencies must be strictly increasing."
  }
}
```

Render job JSON uses these fields when available:

```json
{
  "job_id": "0123456789abcdef0123456789abcdef",
  "status": "ready",
  "created_at": 1770000000.0,
  "updated_at": 1770000001.0,
  "expires_at": 1770001801.0,
  "download_name": "lead_sine.wav",
  "size_bytes": 123456,
  "download_url": "/api/synthesis-jobs/0123456789abcdef0123456789abcdef/download",
  "delete_url": "/api/synthesis-jobs/0123456789abcdef0123456789abcdef"
}
```

Statuses are `queued`, `rendering`, `ready`, `failed`, and `expired`.

## Configuration

- `WEB_SYNTHESISE_JOB_ROOT`: job metadata, upload, and WAV storage root. Default:
  system temp directory plus `octabit-jobs`.
- `WEB_DOWNLOAD_TTL_SECONDS`: ready or failed job retention. Default: `1800`.
- `WEB_MAX_UPLOAD_BYTES`: Flask upload cap. Default: `20971520`.
- Supported upload extensions: `.mid`, `.midi`.
- Supported sample rates: `44100`, `48000`, `96000`.

## Endpoints

### `GET /api/health`

Returns service health for local checks and reverse-proxy probes.

Success:

- Status: `200`
- Type: JSON

```json
{
  "status": "ok",
  "service": "octabit-web"
}
```

### `POST /api/synthesis-jobs`

Creates a render job from one MIDI upload.

Request:

- Type: `multipart/form-data`
- `midi_file`: `.mid` or `.midi` file
- `rate`: `44100`, `48000`, or `96000`
- `layers_json`: JSON array of renderer layer objects

Success:

- Status: `202`
- Type: JSON render job payload
- `download_url` and `delete_url`, when present, use `/api/synthesis-jobs`.

Errors:

- `400` with code `missing_midi_file`
- `400` with code `no_selected_file`
- `400` with code `empty_midi_file`
- `413` with code `upload_too_large`
- `415` with code `unsupported_file_type`
- `422` with code `invalid_sample_rate`
- `422` with code `invalid_layers`
- `500` with code `internal_error`

### `GET /api/synthesis-jobs/<job_id>`

Returns current job state.

Success:

- Status: `200`
- Type: JSON render job payload

Errors and terminal states:

- `400` with code `invalid_job_id`
- `410` JSON with `{"job_id": "...", "status": "expired"}` when missing or expired

### `GET /api/synthesis-jobs/<job_id>/download`

Downloads a ready WAV file.

Success:

- Status: `200`
- Type: WAV file attachment

Errors and terminal states:

- `400` with code `invalid_job_id`
- `400` JSON render job payload when the job failed
- `409` JSON render job payload when the job is not ready yet
- `410` JSON with `{"job_id": "...", "status": "expired"}` when missing or expired

### `DELETE /api/synthesis-jobs/<job_id>`

Deletes the server-side job directory and any ready WAV file.

Success:

- Status: `204`
- Body: empty

Errors:

- `400` with code `invalid_job_id`

## Legacy compatibility

The legacy routes remain available:

- `POST /synthesise`
- `POST /synthesise/jobs`
- `GET /synthesise/jobs/<job_id>`
- `GET /synthesise/jobs/<job_id>/download`
- `DELETE /synthesise/jobs/<job_id>`

Legacy JSON errors generally use `{"error": "message"}` and ready legacy job
payloads return `/synthesise/jobs/...` links. New frontend code should use the
`/api/*` routes.
