# Flask Web Docker 部署

Language/语言: [English](./README.md) | 简体中文

此部署仅用于基于浏览器的 Flask 应用。镜像包含 `apps/web-flask/`、`core/python-renderer/` 中的共享渲染器入口、`assets/previews/` 中的共享预览 WAV 文件，以及项目许可证。它不会打包 macOS 或 Windows 桌面应用。

Compose 文件会把服务在服务器上绑定到 `127.0.0.1:8000`，便于在添加公开反向代理之前先通过 SSH 隧道测试。

## 构建并启动

在 Debian 服务器的仓库根目录执行：

```bash
docker compose -f compose.web.yml up -d --build
```

检查服务状态：

```bash
docker compose -f compose.web.yml ps
```

在服务器本机测试：

```bash
curl http://127.0.0.1:8000
```

查看日志：

```bash
docker compose -f compose.web.yml logs -f
```

## 通过 SSH 隧道测试

在你的 Mac 上打开隧道：

```bash
ssh -p 22080 -N -L 18080:127.0.0.1:8000 debian@42.121.121.121
```

然后在 Mac 上打开这个地址：

```text
http://127.0.0.1:18080
```

## 停止

在 Debian 服务器的仓库根目录执行：

```bash
docker compose -f compose.web.yml down
```

## 生产部署说明

- 容器会以非 root 用户运行 Gunicorn，并监听 `0.0.0.0:${PORT:-8000}`。
- `compose.web.yml` 将 Gunicorn 超时时间配置为 600 秒。这样慢速 SSH 隧道下载有更长时间完成，但浏览器仍会在服务器完成渲染后再下载生成的 WAV。
- 上传的 MIDI 文件、生成的 WAV 文件和短期渲染任务元数据都是 `/tmp` 下的临时文件；Compose 文件把 `/tmp` 挂载为内存 tmpfs，不会持久化上传数据。
- 已准备好的渲染任务会保留 `WEB_DOWNLOAD_TTL_SECONDS` 秒，默认 1800 秒，因此用户遇到 WAV 下载超时时可以重试下载而不必重新渲染。当用户清空已转换文件列表时，浏览器会请求服务器立即删除这些已准备好的文件。
- 主机端口有意绑定到 `127.0.0.1:8000`，用于仅通过隧道访问的测试阶段。
- 后续公开部署时，应在此服务前放置 Caddy 或 Nginx，并只公开 80 和 443 端口。Flask/Gunicorn 服务应保持为服务器本机或 Docker 网络内的私有服务。
