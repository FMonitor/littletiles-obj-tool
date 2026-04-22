# LittleTiles OBJ Tool

[English](#english) | [中文](#中文)

---

## English

### Overview

LittleTiles OBJ Tool is a standalone Python project for converting LittleTiles structure data without requiring a Minecraft or Forge runtime.

It is designed for practical asset conversion workflows around LittleTiles `SNBT` and `OBJ` data, with both a command-line interface and a local Web UI.

### Features

- Convert `1.12 SNBT -> 1.20/1.21 SNBT`
- Convert `1.12 SNBT -> OBJ + MTL`
- Convert `1.20/1.21 SNBT -> OBJ + MTL`
- Convert `OBJ -> 1.20/1.21 SNBT`
- Inspect structures from the command line
- Launch a local browser-based UI with preview tools
- Package the Web UI into a standalone executable
- Run the 3D preview fully from bundled local frontend assets, without CDN dependencies

### Supported Conversion Paths

```text
1.12 SNBT/TXT  ->  1.20/1.21 SNBT
1.12 SNBT/TXT  ->  OBJ + MTL
1.20/1.21 SNBT ->  OBJ + MTL
OBJ            ->  1.20/1.21 SNBT
```

### Run a Prebuilt Release

If you already downloaded a packaged release, you do not need to install Python or project dependencies.

Run on Windows:

1. Download the Windows release package or `LittleTilesOBJTool.exe`
2. Double-click `LittleTilesOBJTool.exe`
3. Your default browser will open the local Web UI automatically
4. Closing the browser page will stop the background process after a short timeout

Run on Linux:

1. Download the Linux release package or `LittleTilesOBJTool`
2. Make it executable if needed:

```bash
chmod +x LittleTilesOBJTool
```

3. Start it:

```bash
./LittleTilesOBJTool
```

4. Your default browser will open the local Web UI automatically
5. Closing the browser page will stop the background process after a short timeout

If your desktop environment does not auto-open a browser, open the shown local address manually in your browser.

### Project Structure

```text
littletiles-obj-tool/
├── LICENSE
├── README.md
├── packaging/
│   └── build_desktop.py
├── scripts/
│   ├── run_cli.py
│   └── run_web.py
├── pyproject.toml
└── src/littletiles_obj_tool/
    ├── cli.py
    ├── converters.py
    ├── desktop.py
    ├── obj_codec.py
    ├── web.py
    ├── templates/
    └── static/
        ├── css/
        ├── js/
        └── vendor/
```

### Installation

Recommended editable install:

```bash
python3 -m pip install -e .
```

Optional build dependencies for packaging:

```bash
python3 -m pip install -e .[build]
```

Lightweight local dependency mode is also possible:

```bash
python3 -m pip install --target ./.deps nbtlib Flask
```

### CLI Usage

Convert old LittleTiles SNBT to newer SNBT:

```bash
python3 scripts/run_cli.py old-to-new old.snbt new.snbt
```

Convert old LittleTiles SNBT to OBJ:

```bash
python3 scripts/run_cli.py old-to-obj old.snbt out/model.obj
```

Convert current SNBT to OBJ:

```bash
python3 scripts/run_cli.py snbt-to-obj structure.snbt out/model.obj
```

Convert OBJ to current SNBT:

```bash
python3 scripts/run_cli.py obj-to-snbt model.obj structure.snbt --grid 16 --max-size 16 --block minecraft:white_concrete --color-hex "#ff8844"
```

Inspect a file:

```bash
python3 scripts/run_cli.py inspect structure.snbt
```

Show help:

```bash
python3 scripts/run_cli.py --help
```

### Web UI

Run the local Web UI:

```bash
python3 scripts/run_web.py
```

Or use the package entry point after installation:

```bash
lt-obj-web
```

Desktop-style launcher that opens the browser automatically:

```bash
lt-obj-desktop
```

### Web UI Highlights

- Three mutually exclusive source inputs: `1.12 SNBT/TXT`, `1.20/1.21 SNBT`, and `OBJ`
- Built-in 3D preview pane for converted or uploaded geometry
- Color wheel and RGBA controls for `OBJ -> SNBT`
- Local bundled `three.js` assets
- Browser-based workflow without external CDN requirements

### Build a Standalone Executable

Build the desktop executable with PyInstaller:

```bash
python3 packaging/build_desktop.py
```

On Windows, hide the console window:

```bash
python3 packaging/build_desktop.py --windowed
```

Output location:

```text
dist/LittleTilesOBJTool
```

### Platform-Specific Packaging

PyInstaller builds for the current platform only.

- Build on Windows if you want a Windows `.exe`
- Build on Linux if you want a Linux native executable
- Cross-building between Windows and Linux is generally not recommended for this project

Build on Windows:

```bash
python -m pip install -e .[build]
python packaging/build_desktop.py --windowed
```

Typical output:

```text
dist/LittleTilesOBJTool.exe
```

Build on Linux:

```bash
python3 -m pip install -e .[build]
python3 packaging/build_desktop.py
```

Typical output:

```text
dist/LittleTilesOBJTool
```

Recommended release workflow:

1. Build the Windows package on Windows
2. Build the Linux package on Linux
3. Upload both artifacts separately to GitHub Releases

### Notes

- The desktop executable starts a local Flask server and opens your default browser automatically.
- In desktop mode, closing the browser page stops the heartbeat and the background process exits automatically after a short timeout.
- If the default port is already in use, the app falls back to another free local port.
- The preview panel still requires browser WebGL support.
- `OBJ -> SNBT` follows the general one-triangle-to-box style used by the old importer/exporter workflow where needed.
- `SNBT -> OBJ` exports flat-color materials and does not attempt to reconstruct Minecraft texture atlases.

### License

This project is currently released under the [MIT License](./LICENSE).

---

## 中文

### 项目简介

`LittleTiles OBJ Tool` 是一个独立的 Python 工具项目，用于在不依赖 Minecraft 或 Forge 运行环境的前提下，处理 LittleTiles 结构数据转换。

它同时提供命令行工具和本地 Web 页面，适合做 `SNBT` 与 `OBJ` 之间的实际转换工作。

### 主要功能

- `1.12 SNBT -> 1.20/1.21 SNBT`
- `1.12 SNBT -> OBJ + MTL`
- `1.20/1.21 SNBT -> OBJ + MTL`
- `OBJ -> 1.20/1.21 SNBT`
- 命令行结构检查
- 本地网页界面与 3D 预览
- 可打包为独立可执行文件
- 预览所需前端资源已本地化，不再依赖 CDN

### 直接运行已发布的程序

如果你下载的是已经打包好的发布版，就不需要额外安装 Python 或项目依赖。

在 Windows 上运行：

1. 下载 Windows 发布包或 `LittleTilesOBJTool.exe`
2. 双击 `LittleTilesOBJTool.exe`
3. 程序会自动打开默认浏览器并进入本地网页界面
4. 关闭网页后，后台进程会在短暂超时后自动退出

在 Linux 上运行：

1. 下载 Linux 发布包或 `LittleTilesOBJTool`
2. 如果没有执行权限，先执行：

```bash
chmod +x LittleTilesOBJTool
```

3. 运行：

```bash
./LittleTilesOBJTool
```

4. 程序会自动打开默认浏览器并进入本地网页界面
5. 关闭网页后，后台进程会在短暂超时后自动退出

如果桌面环境没有自动拉起浏览器，也可以手动打开程序显示的本地地址。

### 安装

推荐开发安装方式：

```bash
python3 -m pip install -e .
```

如果需要打包：

```bash
python3 -m pip install -e .[build]
```

### 命令行使用

旧版 SNBT 转新版 SNBT：

```bash
python3 scripts/run_cli.py old-to-new old.snbt new.snbt
```

旧版 SNBT 转 OBJ：

```bash
python3 scripts/run_cli.py old-to-obj old.snbt out/model.obj
```

新版 SNBT 转 OBJ：

```bash
python3 scripts/run_cli.py snbt-to-obj structure.snbt out/model.obj
```

OBJ 转新版 SNBT：

```bash
python3 scripts/run_cli.py obj-to-snbt model.obj structure.snbt --grid 16 --max-size 16 --block minecraft:white_concrete --color-hex "#ff8844"
```

查看帮助：

```bash
python3 scripts/run_cli.py --help
```

### Web 界面使用

启动本地网页界面：

```bash
python3 scripts/run_web.py
```

安装后也可以直接使用：

```bash
lt-obj-web
```

自动打开浏览器的桌面模式：

```bash
lt-obj-desktop
```

### 打包独立可执行文件

```bash
python3 packaging/build_desktop.py
```

Windows 隐藏控制台窗口：

```bash
python3 packaging/build_desktop.py --windowed
```

输出目录：

```text
dist/LittleTilesOBJTool
```

### 按平台打包

PyInstaller 默认只能为当前系统打包。

- 想得到 Windows 的 `.exe`，请在 Windows 上打包
- 想得到 Linux 的本地可执行文件，请在 Linux 上打包
- 一般不建议在这个项目里做 Windows 和 Linux 的交叉打包

在 Windows 上打包：

```bash
python -m pip install -e .[build]
python packaging/build_desktop.py --windowed
```

常见输出：

```text
dist/LittleTilesOBJTool.exe
```

在 Linux 上打包：

```bash
python3 -m pip install -e .[build]
python3 packaging/build_desktop.py
```

常见输出：

```text
dist/LittleTilesOBJTool
```

推荐发布方式：

1. 在 Windows 上打一次 Windows 包
2. 在 Linux 上打一次 Linux 包
3. 把两个产物分别上传到 GitHub Releases

### 说明

- 打包后的程序会启动本地 Flask 服务，并自动打开默认浏览器。
- 桌面模式下，关闭网页后心跳会停止，后台进程会在短暂超时后自动退出。
- 如果默认端口被占用，会自动切换到空闲端口。
- 3D 预览仍然依赖浏览器本身支持 WebGL。
- 页面所需的 `three.js` 等资源已经打包进项目，不再依赖外部 CDN。

### 开源协议

当前仓库使用 [MIT License](./LICENSE)。
