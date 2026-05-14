# Web API 约定

Language/语言: [English](./api-contract.md) | 简体中文

本文档描述当前 Flask/Gunicorn OctaBit Web 服务面向浏览器的 API 边界。Web UI
仍由 Flask 在服务器端渲染，合成仍使用 `core/python-renderer/` 中的规范
Python 渲染器。

## 范围

- 新的前端代码应使用 `/api/*` 路由。
- 旧的 `/synthesise*` 路由保留用于兼容。
- 渲染任务以文件系统为后端；当前没有数据库。
- 任务 id 是随机 UUID 十六进制字符串，应视为 bearer token。

## 通用格式

API 错误使用此 JSON 结构：

```json
{
  "error": {
    "code": "invalid_layers",
    "message": "Layer 1 frequency_curve frequencies must be strictly increasing."
  }
}
```

渲染任务 JSON 在可用时包含以下字段：

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

状态包括 `queued`、`rendering`、`ready`、`failed` 和 `expired`。

## 配置

- `WEB_SYNTHESISE_JOB_ROOT`：任务元数据、上传文件和 WAV 文件的存储根目录。默认值为系统临时目录加 `octabit-jobs`。
- `WEB_DOWNLOAD_TTL_SECONDS`：ready 或 failed 任务的保留时间。默认值为 `1800`。
- `WEB_MAX_UPLOAD_BYTES`：Flask 上传大小上限。默认值为 `20971520`。
- 支持的上传扩展名：`.mid`、`.midi`。
- 支持的采样率：`44100`、`48000`、`96000`。

## 端点

### `GET /api/health`

用于本地检查和反向代理探测的服务健康端点。

成功：

- 状态码：`200`
- 类型：JSON

```json
{
  "status": "ok",
  "service": "octabit-web"
}
```

### `POST /api/synthesis-jobs`

从一个 MIDI 上传创建渲染任务。

请求：

- 类型：`multipart/form-data`
- `midi_file`：`.mid` 或 `.midi` 文件
- `rate`：`44100`、`48000` 或 `96000`
- `layers_json`：渲染器层对象的 JSON 数组

成功：

- 状态码：`202`
- 类型：JSON 渲染任务载荷
- 如果返回 `download_url` 和 `delete_url`，它们使用 `/api/synthesis-jobs`。

错误：

- `400`，代码 `missing_midi_file`
- `400`，代码 `no_selected_file`
- `400`，代码 `empty_midi_file`
- `413`，代码 `upload_too_large`
- `415`，代码 `unsupported_file_type`
- `422`，代码 `invalid_sample_rate`
- `422`，代码 `invalid_layers`
- `500`，代码 `internal_error`

### `GET /api/synthesis-jobs/<job_id>`

返回当前任务状态。

成功：

- 状态码：`200`
- 类型：JSON 渲染任务载荷

错误和终止状态：

- `400`，代码 `invalid_job_id`
- 任务缺失或过期时返回 `410` JSON：`{"job_id": "...", "status": "expired"}`

### `GET /api/synthesis-jobs/<job_id>/download`

下载已准备好的 WAV 文件。

成功：

- 状态码：`200`
- 类型：WAV 文件附件

错误和终止状态：

- `400`，代码 `invalid_job_id`
- 任务失败时返回 `400` JSON 渲染任务载荷
- 任务尚未 ready 时返回 `409` JSON 渲染任务载荷
- 任务缺失或过期时返回 `410` JSON：`{"job_id": "...", "status": "expired"}`

### `DELETE /api/synthesis-jobs/<job_id>`

删除服务器端任务目录和已准备好的 WAV 文件。

成功：

- 状态码：`204`
- 正文：空

错误：

- `400`，代码 `invalid_job_id`

## 旧路由兼容

旧路由仍可使用：

- `POST /synthesise`
- `POST /synthesise/jobs`
- `GET /synthesise/jobs/<job_id>`
- `GET /synthesise/jobs/<job_id>/download`
- `DELETE /synthesise/jobs/<job_id>`

旧 JSON 错误通常使用 `{"error": "message"}`，ready 的旧任务载荷会返回
`/synthesise/jobs/...` 链接。新的前端代码应使用 `/api/*` 路由。
