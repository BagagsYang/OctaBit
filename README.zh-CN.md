# OctaBit

Language/语言: [English](./README.md) | 简体中文

OctaBit 是一个基于浏览器的工具，用于将 MIDI 文件转换为 8-bit 风格 WAV 音频。公开服务地址是 <https://octabit.cc>。

生产 Web 前端是 `apps/web-vue/` 中的 Vue 3 应用。Flask 继续作为 `apps/web-flask/` 中的后端 API 与工作区/合成服务，并将音频渲染委托给 `core/python-renderer/` 中的规范 Python 渲染器。旧 Flask 渲染前端仍保留在仓库中，作为 legacy fallback。原生 macOS 和 Windows 应用已暂停/弃用，只保留作参考或未来可能恢复。

## 当前活跃内容

| 路径 | 作用 |
| --- | --- |
| `apps/web-vue/` | 从 Vite `dist` 构建产物提供服务的生产 Vue 3 前端 |
| `apps/web-flask/` | Flask 后端 API、工作区/合成服务、预览路由、测试和旧 Flask 渲染前端 |
| `core/python-renderer/` | Flask 后端使用的规范 MIDI 转 WAV 渲染器 |
| `assets/previews/` | 通过 Flask 后端提供的共享波形预览 WAV 文件 |
| `deploy/digitalocean/` | Vue 生产路径的非 Docker DigitalOcean 部署说明、辅助脚本和 Caddy 示例 |
| `deploy/web-flask/` | Flask 后端或旧前端回退路径的 Docker 镜像定义和说明 |
| `compose.web.yml` | Flask 后端或旧前端回退路径的最小 Docker Compose 入口 |
| `docs/api-contract.md` | Web API 请求和响应契约 |

保留的原生应用目录：

| 路径 | 状态 |
| --- | --- |
| `apps/macos/` | 已暂停/弃用的原生 SwiftUI macOS 应用 |
| `apps/windows/` | 已暂停/弃用的原生 WinUI 3 Windows 应用 |

## 运行 Web 应用

在仓库根目录执行：

```bash
python3 -m venv .venv
./.venv/bin/python3 -m pip install -r apps/web-flask/requirements.txt
PORT=8000 WEB_FLASK_OPEN_BROWSER=0 ./.venv/bin/python3 apps/web-flask/app.py
```

在另一个终端运行 Vue 前端：

```bash
cd apps/web-vue
npm ci
npm run dev
```

打开 `http://127.0.0.1:5173/`。Vite 会把 `/api/*` 和 `/static/previews/*` 代理到
`127.0.0.1:8000` 上的 Flask。

旧 Flask 渲染前端仍可直接从 Flask 打开，用于回退测试：

```bash
./.venv/bin/python3 apps/web-flask/app.py
```

运行活跃 Web 相关测试：

```bash
./.venv/bin/python3 -m unittest discover -s apps/web-flask/tests
./.venv/bin/python3 -m unittest discover -s core/python-renderer/tests
cd apps/web-vue && npm run build
```

## 用户限制

以下是当前 Web 应用和渲染器的默认限制。部署者可以通过环境变量调整部分 Web 服务限制，但渲染器安全限制会在 `core/python-renderer/midi_to_wave.py` 中强制执行。

| 限制 | 默认值 | 来源 |
| --- | ---: | --- |
| 单次请求上传大小 | 20 MiB | `WEB_MAX_UPLOAD_BYTES` |
| 工作区最后活动后的保留时间 | 86400 秒 | `WEB_WORKSPACE_TTL_SECONDS` |
| 每个工作区排队 MIDI 文件数 | 20 个文件 | `WEB_WORKSPACE_MAX_QUEUED_FILES` |
| 每个工作区排队上传总存储 | 100 MiB | `WEB_WORKSPACE_MAX_UPLOAD_BYTES` |
| 每个工作区已转换 WAV 文件数 | 20 个文件 | `WEB_WORKSPACE_MAX_CONVERTED_FILES` |
| 兼容任务下载保留时间 | 1800 秒 | `WEB_DOWNLOAD_TTL_SECONDS` |
| 每个容器活跃渲染工作线程 | 2 个线程 | `WEB_RENDER_WORKERS` |
| 每个容器等待渲染队列 | 8 个任务 | `WEB_RENDER_QUEUE_SIZE` |
| MIDI 时长 | 1800 秒 | 渲染器限制 |
| 渲染样本数 | 172800000 个样本 | 渲染器限制 |
| WAV 样本数据大小 | 345600000 字节，约 329.6 MiB | 渲染器限制 |
| MIDI 音符数 | 20000 个音符 | 渲染器限制 |
| 声音层数 | 4 层 | 渲染器限制和 Web 配置 |
| 每层频率曲线点数 | 8 个点 | 渲染器限制 |
| 采样率 | 44100、48000 或 96000 Hz | Web 校验 |
| Pulse 占空比 | 0.01 到 0.99 | 渲染器校验 |
| Web 层音量 | 0.0 到 2.0 | 工作区配置校验 |
| 频率曲线增益 | -36 dB 到 12 dB | 渲染器校验 |
| 频率曲线范围 | MIDI 音符 0 到 127 对应频率 | 渲染器校验 |

排队上传和已转换 WAV 文件都是临时文件。用户在浏览器中清空排队文件或已转换文件时，Web 应用会请求服务器立即删除对应的临时文件。

## Web API

Vue 前端通过 Flask API 使用基于 cookie 的匿名临时工作区。`GET /api/workspace` 会创建或恢复工作区，资源路由要求携带当前工作区 cookie。完整 API 契约位于 `docs/api-contract.md`。

主要路由：

- `GET /api/health`
- `GET /api/workspace`
- `POST /api/workspace/uploads`
- `DELETE /api/workspace/uploads/<file_id>`
- `PATCH /api/workspace/queue`
- `PUT /api/workspace/config`
- `POST /api/synthesis-jobs`
- `GET /api/synthesis-jobs/<job_id>`
- `GET /api/synthesis-jobs/<job_id>/download`
- `DELETE /api/synthesis-jobs/<job_id>`

兼容旧客户端的路由仍然保留：

- `POST /synthesise`
- `POST /synthesise/jobs`
- `GET /synthesise/jobs/<job_id>`
- `GET /synthesise/jobs/<job_id>/download`
- `DELETE /synthesise/jobs/<job_id>`

API 错误使用 `{"error":{"code":"...","message":"..."}}`。兼容路由保留旧的 `{"error":"..."}` 形状。

## 声音配置

Web 应用会在临时工作区中保存采样率和声音层设置。合成支持 pulse、sine、sawtooth 和 triangle 层。频率-增益曲线由共享渲染器校验，并在合成时按层应用。

输出命名：

- 单个可听层且没有曲线：`<original>_<wave>.wav`
- 多个可听层且没有曲线：`<original>_mix.wav`
- 任一可听层带有非空频率曲线：`<original>_<base>_<hash>.wav`

哈希来自经过清理的层配置，因此不同曲线设置不会复用同一个导出名称。

## 本地化

生产 Vue UI 使用 `apps/web-vue/src/i18n/` 中的 JSON catalog 文件。旧 Flask 渲染 UI 使用 `apps/web-flask/i18n/` 中的 catalog。修改任一 catalog 集合时，请保持 `en.json`、`fr.json` 和 `zh-CN.json` 的键集合一致。英文是回退语言。

面向用户的 Web 字符串应进入 catalog，不应硬编码在模板或 JavaScript 中。只要原生 macOS 和 Windows 应用仍处于暂停状态，它们的本地化工作就不在当前范围内。

## 部署

预期生产模型不使用 Docker：

```bash
./.venv/bin/python3 -m gunicorn --chdir apps/web-flask --bind 127.0.0.1:8000 --workers 2 --timeout 600 app:app
cd apps/web-vue && npm ci && npm run build
```

公开部署时，应让 Gunicorn 私有监听 `127.0.0.1:8000`。Caddy 将 `apps/web-vue/dist` 作为公开前端，并把 `/api/*`、`/static/previews/*` 和 `/synthesise*` 反向代理到 Flask。DigitalOcean 部署说明、Caddy 示例、smoke 检查和回滚步骤位于 `deploy/digitalocean/README.zh-CN.md`。

`deploy/web-flask/` 中的 Docker 镜像仍可用于 Flask 后端或旧 Flask 渲染前端回退路径。它通过摘要固定 Python 基础镜像，并从带哈希锁定的 requirements 文件安装依赖。

## 许可证

本项目采用 GNU Affero General Public License v3.0 或更新版本（`AGPL-3.0-or-later`）授权。详情见 [LICENSE.md](./LICENSE.md)。
