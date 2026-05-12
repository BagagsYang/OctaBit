# 仓库结构

Language/语言: [English](./repository-layout.md) | 简体中文

该仓库是 MIDI-8bit Synthesiser 产品族的单体仓库。当前活跃目标是
`apps/web-flask/` 中的公开 Flask/Gunicorn Web 服务。原生 macOS 和 Windows 应用已
deprecated/paused，不再作为活跃开发目标；代码保留用于参考或未来可能的恢复。仓库还包含规范
Python 渲染器、共享预览资源、部署文件和发布文档。

## 顶层结构

| 路径 | 用途 |
| --- | --- |
| `AGENTS.md` | 面向编码代理和本地工作流的仓库说明。 |
| `README.md`, `README.zh-CN.md` | 根项目概览、设置说明、应用入口和仓库许可证摘要。 |
| `LICENSE.md` | 仓库 AGPL 许可证文本。 |
| `apps/` | 当前 Web 应用目标、保留的原生应用代码和桌面占位目录。 |
| `core/python-renderer/` | 规范 Python MIDI 转 WAV 渲染器和对齐参考实现。 |
| `assets/previews/` | 各应用共享的规范波形预览 WAV 文件。 |
| `docs/` | 仓库结构说明、许可证审计和评审报告。 |
| `deploy/web-flask/` | Flask Web 应用的 Docker 部署文档和 Dockerfile。 |
| `.github/workflows/` | 保留的 Windows 发布构建 GitHub Actions 工作流。 |
| `compose.web.yml` | Flask Web 部署的 Docker Compose 入口。 |
| `global.json` | 保留的 Windows 解决方案使用的 .NET SDK 选择。 |
| `.dockerignore`, `.gitignore`, `.gitattributes` | 仓库打包、忽略和换行规则。 |
| `output/`, `tmp/` | 已跟踪的历史生成评审产物；两个路径都被忽略，用于未来生成输出。 |

`.venv/`、构建输出、`.codex/`、`.sisyphus/`、`.DS_Store`、`__pycache__/`、
`.xcodebuild/` 和各应用的 `build/` 目录等本地目录不属于维护中的源码结构。

## 应用目标

### `apps/web-flask/`

项目当前活跃的 Flask / 浏览器 UI 和可部署 Web 服务。

- `app.py`：Flask 入口、上传处理、合成端点、预览路由和服务器端渲染任务端点。
- `templates/index.html`：浏览器 UI 外壳。
- `static/css/` 和 `static/js/`：Web 专用样式和浏览器行为。
- `i18n/`：英文、法文和简体中文 UI 文本的 JSON 目录。
- `tests/`：Flask 和渲染路径测试。
- `requirements.txt`：Web 运行时依赖；它包含共享渲染器依赖。
- `Launch_Synthesiser.command` 和 `Launch_Synthesiser.bat`：本地启动器。
- `README.md`、`README.zh-CN.md`、`User_Guide.txt`：Web 应用文档。

Web 应用将合成交给 `core/python-renderer/midi_to_wave.py`，并从
`assets/previews/` 提供预览音频。

### `apps/macos/`

已 deprecated/paused 的原生 SwiftUI macOS 应用和 Xcode 工程。该代码不是主要开发目标；在项目聚焦
Web 服务期间，它保留用于参考或未来可能的恢复。

- `MIDI8BitSynthesiser.xcodeproj/`：Xcode 工程和共享 scheme。
- `MIDI8BitSynthesiser/`：SwiftUI 应用源码。
- `MIDI8BitSynthesiserTests/`：用于模型和文件名逻辑的 XCTest 目标。
- `macos/build_desktop_resources.sh`：Xcode 构建阶段脚本，用于将 Python 渲染器冻结为辅助二进制文件，并把预览 WAV 资源复制进应用包。
- `requirements-build.txt`：辅助程序的 Python 构建依赖。
- `macos/README.md`、`macos/README.zh-CN.md`：macOS 构建和使用说明。

macOS 应用不运行 Flask 服务器。它会为每个队列中的 MIDI 文件启动随包附带的 Python
辅助程序。

### `apps/windows/`

已 deprecated/paused 的原生 WinUI 3 Windows 应用、C# 渲染器、测试、安装程序和评审工具。该代码不是主要开发目标；在项目聚焦
Web 服务期间，它保留用于参考或未来可能的恢复。

- `Midi8BitSynthesiser.sln`：Windows 解决方案。
- `Directory.Packages.props`：集中管理的 NuGet 包版本。
- `src/Midi8BitSynthesiser.Core/`：C# 渲染引擎、波形模型和输出命名。
- `src/Midi8BitSynthesiser.App/`：WinUI 3 外壳、兼容性检查、文件对话框服务、预览播放、本地化资源和应用清单。
- `tests/Midi8BitSynthesiser.Tests/`：单元、工作流、兼容性和 Python 对齐测试。
- `installer/Midi8BitSynthesiser.iss`：Inno Setup 安装程序脚本。
- `installer/RuntimeNotice.txt`：安装前运行时提示。
- `scripts/create_review_bundle.sh`：准备 Windows 评审包的脚本。
- `README.md`、`README.zh-CN.md`、`REVIEWING.md`：Windows 构建、评审和发布文档。

保留的 Windows 应用有自己的 C# 渲染器，并在对齐测试中用 Python 参考渲染器进行校验。应用工程会从规范
`assets/previews/` 目录链接预览 WAV 文件，用于构建和发布输出。
`src/Midi8BitSynthesiser.App/Assets/Previews/` 下也存在一份字节相同的已跟踪副本，但工程文件使用共享资源目录作为构建来源。

### `apps/desktop/`

为未来桌面打包层保留的占位目录。它只包含 README 文件，没有应用实现。

## 共享核心和资源

### `core/python-renderer/`

规范 Python MIDI 转 WAV 渲染器。

- `midi_to_wave.py`：渲染器模块和 CLI 入口。
- `requirements.txt`：仅包含渲染器/运行时依赖。
- `tests/`：渲染器测试。
- `README.md`：渲染器接口、层结构和依赖边界。

渲染器接收平台无关的文件路径和波形层设置，然后将 WAV 文件写入磁盘。Web 应用会直接调用它；保留的
macOS 应用也会直接调用它，保留的 Windows 应用将它作为原生 C# 渲染器的对齐参考。

### `assets/previews/`

Web 应用和保留的原生应用路径使用的规范预览 WAV 资源。`assets/README.md`
记录了它们的预期用途和来源说明。

## 文档和生成产物

- `docs/repository-layout.md` 和 `docs/repository-layout.zh-CN.md`：当前仓库结构的英文和简体中文说明。
- `docs/licensing-audit.md`：面向仓库和发布规划的许可证与署名审计。
- `docs/reviews/windows-app-review.md`：Windows 评审记录。
- `output/pdf/repo-structure-evaluation.pdf`、
  `tmp/pdfs/repo-structure-evaluation.html` 和
  `tmp/pdfs/rendered/repo-structure-evaluation.png`：已跟踪的历史生成评审产物。它们不是当前结构的事实来源。

## 构建和开发流程

除非某个文档另有说明，否则从仓库根目录运行命令。

创建本地 Python 环境：

```bash
python3 -m venv .venv
```

只安装当前工作区域需要的依赖：

```bash
./.venv/bin/python3 -m pip install -r apps/web-flask/requirements.txt
./.venv/bin/python3 -m pip install -r apps/macos/requirements-build.txt
./.venv/bin/python3 -m pip install -r core/python-renderer/requirements.txt
```

常用检查：

```bash
./.venv/bin/python3 -m unittest discover -s apps/web-flask/tests
./.venv/bin/python3 -m unittest discover -s core/python-renderer/tests
```

已暂停的 Windows 应用仍可通过 .NET 8 和 Python 渲染器依赖进行检查：

```powershell
dotnet restore apps/windows/Midi8BitSynthesiser.sln
dotnet build apps/windows/Midi8BitSynthesiser.sln -c Release -p:Platform=x64
dotnet test apps/windows/Midi8BitSynthesiser.sln -c Release -p:Platform=x64 --no-build
```

保留的 Windows 发布路径使用：

```powershell
dotnet publish apps/windows/src/Midi8BitSynthesiser.App/Midi8BitSynthesiser.App.csproj -c Release -r win-x64 --self-contained true -p:Platform=x64
```

已暂停的 macOS 应用通过 Xcode 使用 `MIDI8BitSynthesiser` scheme 构建。Xcode 构建阶段会运行
`apps/macos/macos/build_desktop_resources.sh`。

Flask Docker 部署使用：

```bash
docker compose -f compose.web.yml up -d --build
```

Compose 文件将服务绑定到 `127.0.0.1:8000`，用于先通过隧道测试；镜像中只构建 Flask
Web 应用、共享渲染器、共享预览资源和项目许可证。

## 依赖和打包边界

- Python 渲染器依赖位于 `core/python-renderer/requirements.txt`。
- Web 专用 Python 依赖位于 `apps/web-flask/requirements.txt`。
- macOS 辅助构建依赖位于 `apps/macos/requirements-build.txt`。
- Windows NuGet 版本位于 `apps/windows/Directory.Packages.props`。
- 当前检出中没有 JavaScript 包管理器元数据；Web 应用目前使用本地静态 JavaScript/CSS，并在 HTML 模板中链接外部 Bootstrap 和 Google Fonts。
- Docker 部署文件仅限 `apps/web-flask/` 范围。
- 保留的原生应用打包仍位于对应应用目录下。

## 归属边界

- 共享渲染行为属于 `core/python-renderer/`。
- Web UI、启动、打包和发布逻辑属于 `apps/web-flask/`。
- 保留的原生 UI、启动、打包和发布逻辑仍位于对应的 `apps/` 目录下。
- 共享二进制/媒体资源属于 `assets/`。
- 仓库级文档、审计和评审记录属于 `docs/`。
- 部署专用文件属于 `deploy/` 和根目录部署入口，例如 `compose.web.yml`。
