# Web Flask 应用

Language/语言: [English](./README.md) | 简体中文

此目录包含通过浏览器分发的 OctaBit 主要实现。该服务的公开站点是 `https://octabit.cc`。

## 职责

- Flask 入口点与请求处理
- HTML 模板与 Web 专用静态资源
- 启动脚本
- 仅包含浏览器 UI；合成工作委托给 `../../core/python-renderer/` 中的 Python 渲染器
- 用于验证按层频率-增益曲线 UI 的第一阶段方案

## 运行

在仓库根目录执行：

```bash
python3 -m venv .venv
./.venv/bin/python3 -m pip install -r apps/web-flask/requirements.txt
./.venv/bin/python3 apps/web-flask/app.py
```

或者运行辅助脚本：

```bash
apps/web-flask/Launch_Synthesiser.command
```

在 Windows 上，请使用：

```bat
apps\web-flask\Launch_Synthesiser.bat
```

## 共享依赖

- 渲染器：`../../core/python-renderer/midi_to_wave.py`
- 规范预览资源：`../../assets/previews/`

此应用从共享资源目录提供预览 WAV 文件，不应复制渲染器逻辑。

## 当前上传约定

`POST /synthesise` 使用 `multipart/form-data`，包含：

- `midi_file`：上传的 `.mid` 或 `.midi`
- `rate`：整数采样率
- `layers_json`：层对象的 JSON 数组

每个层对象包含：

- `type`
- `duty`
- `volume`
- `frequency_curve`：可选的 `{frequency_hz, gain_db}` 点数组

浏览器 UI 在 JavaScript 中保存层状态，并将其序列化到 `layers_json` 中。

在服务器部署中，浏览器 UI 使用渲染任务接口，而不是等待单个请求同时完成上传、渲染和下载：

- `POST /synthesise/jobs`：接受相同表单字段并返回任务 id。
- `GET /synthesise/jobs/<job_id>`：报告 queued、rendering、ready、failed 或 expired 状态。
- `GET /synthesise/jobs/<job_id>/download`：下载已准备好的 WAV 文件。
- `DELETE /synthesise/jobs/<job_id>`：当用户清空已转换文件列表时删除服务器上的临时文件。

已准备好的任务文件是临时文件，会在 `WEB_DOWNLOAD_TTL_SECONDS` 后过期；默认值为 1800 秒。浏览器也会在用户清空已转换文件列表时立即删除服务器上已准备好的文件。

## 输出命名

- 单个可听层且无曲线：`<original>_<wave>.wav`
- 多个可听层且无曲线：`<original>_mix.wav`
- 任一可听层带有非空频率曲线：`<original>_<base>_<hash>.wav`

哈希值基于清理后的层载荷生成，因此不同曲线设置不会复用同一个导出名称。
