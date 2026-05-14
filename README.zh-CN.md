# OctaBit

Language/语言: [English](./README.md) | 简体中文

OctaBit 是一个用于将 MIDI 文件转换为 8-bit 风格音乐的简单 Web 工具。官方网站是 <https://octabit.cc>。

该仓库是为 OctaBit 重新整理后的单体仓库。当前活跃目标是 `apps/web-flask/` 中的 Flask/Gunicorn Web 服务，并通过 Docker 面向服务器部署。原生 macOS 和 Windows 应用已 deprecated/paused，不再作为活跃开发目标；代码保留在仓库中，用于参考或未来可能的恢复。Python 参考渲染器位于 `core/` 下，共享预览资源位于 `assets/` 下。

## 目录结构

| 目录 | 职责 |
| --- | --- |
| `apps/web-flask/` | 当前活跃的 Flask / 浏览器 UI 和可部署 Web 服务 |
| `apps/macos/` | 已 deprecated/paused 的原生 macOS SwiftUI 应用和 Xcode 工程，保留用于参考 |
| `apps/windows/` | 已 deprecated/paused 的原生 Windows WinUI 3 解决方案、C# 渲染器、安装程序，保留用于参考 |
| `apps/desktop/` | 为未来桌面打包工作保留的占位目录 |
| `core/python-renderer/` | 规范 Python MIDI 转 WAV 渲染器与对齐参考实现 |
| `assets/previews/` | Web 应用和保留的原生应用代码使用的规范波形预览 WAV 资源 |
| `docs/` | 评审记录与仓库结构说明 |

## 共享渲染器

- 规范渲染器入口：`core/python-renderer/midi_to_wave.py`
- 稳定输入：MIDI 路径、输出 WAV 路径、采样率、波形层
- 稳定输出：渲染后的 WAV 文件，或明确的错误信息
- 保留的 Windows 代码包含原生 C# 实现，并通过对齐测试与 Python 渲染器进行校验

## 构建说明

在仓库根目录创建仓库本地环境：

```bash
python3 -m venv .venv
```

仅安装你当前处理的区域所需依赖：

- Web UI：`./.venv/bin/python3 -m pip install -r apps/web-flask/requirements.txt`
- macOS 辅助构建（仅在检查已暂停的原生应用时需要）：`./.venv/bin/python3 -m pip install -r apps/macos/requirements-build.txt`
- Windows 对齐测试（仅在检查已暂停的原生应用时需要）：`./.venv/bin/python3 -m pip install -r core/python-renderer/requirements.txt`

各应用的专用说明位于：

- `apps/web-flask/README.md`
- `apps/macos/macos/README.md`
- `apps/windows/README.md`

仓库结构说明位于 `docs/repository-layout.md`。

## 许可证

本项目采用 GNU Affero General Public License v3.0 或更新版本（`AGPL-3.0-or-later`）授权。完整详情请参阅 [LICENSE](LICENSE.md) 文件。
