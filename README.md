# DesktopPet

使用 Python + PyQt5 编写的轻量 Windows 桌宠，支持形态切换、透明动画、拖拽、托盘、置顶、固定位置、鼠标点击穿透及全局快捷键恢复。

<img src="pet.png" width="128" alt="桌宠外观">
<img src="forms/remielle-preview.png" width="256" alt="蕾米埃尔形态">

## 下载

[下载 v1.1.1 全部版本](https://github.com/GGAAOOTTIIAANN/DesktopPet/releases/tag/v1.1.1)

| 文件 | 用途 | 体积 |
| --- | --- | --- |
| [Pet_x64.exe](https://github.com/GGAAOOTTIIAANN/DesktopPet/releases/download/v1.1.1/Pet_x64.exe) | 64 位 Windows 正式版 | 约 49.56 MiB |
| [Pet_x86.exe](https://github.com/GGAAOOTTIIAANN/DesktopPet/releases/download/v1.1.1/Pet_x86.exe) | 32 位 Windows 正式版 | 约 42.91 MiB |
| [Pet_x64_debug.exe](https://github.com/GGAAOOTTIIAANN/DesktopPet/releases/download/v1.1.1/Pet_x64_debug.exe) | 64 位调试版，带控制台 | 约 49.56 MiB |

exe 已内置 Python、Qt 和透明图片，可直接运行。需要目标系统安装对应位数的 VC++ 2015–2019 运行库。发布页附有 `SHA256SUMS.txt` 校验值，源码也可从该页下载。

## 操作

- **左键拖动**：实时跟随鼠标，释放后校正到显示器可用区域。
- **固定位置**：右键桌宠或托盘，勾选后禁止拖动，取消后恢复。
- **窗口置顶**：右键菜单切换，默认开启。
- **切换形态**：右键 → 切换形态 → 默认 Q 版 / 蕾米埃尔。
- **形态动作**：蕾米埃尔支持两种循环动作，默认动作二；隐藏或拖动时暂停，恢复后继续。
- **大小**：96、128、192、256、384、512 六档，单位为逻辑像素；Q 版默认 128，蕾米埃尔默认 384，两种形态分别记忆本次选择。
- **显示／隐藏**：双击托盘，或使用托盘右键菜单。
- **点击穿透**：右键菜单开启后，鼠标可直接操作桌宠下方的窗口。
- **恢复交互**：全局快捷键 `Ctrl+Alt+P` 切换穿透；若被占用，自动尝试 `Ctrl+Alt+Shift+P`，以菜单和托盘提示显示的组合为准。也可在托盘菜单取消穿透。
- **退出**：右键菜单选择“退出程序”。

快捷键和托盘同时不可用时，程序禁止开启穿透。按住热键不会因自动重复而反复切换。窗口隐藏或重建后，已注册的热键仍可用。

默认允许拖动、置顶、关闭穿透。设置保留到本次运行结束。x64、x86 和调试版共用单实例锁，重复启动只保留一个桌宠。PyInstaller onefile 启动时可能显示引导和主程序两个进程。

## 源码运行和打包

使用对应位数的 **CPython 3.8.10**。核心依赖已锁定：

```text
PyQt5==5.15.9
PyQt5-Qt5==5.15.2
PyInstaller==4.10
```

完整版本见 [requirements.txt](requirements.txt)。

```bat
python -m pip install -r requirements.txt
python main.py
```

也可使用 `Pet_x64.exe --form remielle`，或源码运行 `python main.py --form remielle`，直接打开蕾米埃尔形态。

源码运行时，保留 `main.py`、`pet_forms.py`、`pet.png` 以及 `forms/remielle.pet` 的目录结构。原始图片具有 alpha 通道；加载失败时弹框退出。形态包缺失或损坏时提示并保留/恢复默认外观。

打包脚本使用 `D:\Pet` 作为工作和输出目录，请先将源码、图片、`forms` 目录、依赖文件及三个 `.bat` 脚本放入该目录，再分别运行：

```bat
build_x64.bat "C:\Python38-x64\python.exe"
build_x86.bat "C:\Python38-x86\python.exe"
build_debug.bat "C:\Python38-x64\python.exe"
```

脚本检查解释器版本及位数，并使用独立构建缓存。正式版采用 `--onefile --windowed --noupx`，调试版采用 `--console`。

蕾米埃尔来自用户提供的 Spine 素材，已从骨骼和贴图重新离线渲染成高清透明帧：两种动作各 64 帧、12 fps、最长边 1024 像素，使用高品质 WebP（画质 96）存储。Qt 自带插件负责解码，不需要安装 Spine、Node.js、浏览器或额外动画引擎，运行依赖保持不变。

高 DPI 绘制保留实际像素及 `devicePixelRatio`，例如 200% 下的 384 逻辑像素使用 768 像素图像，避免先缩小再由 Windows 放大造成模糊。缓存同时限制为最多 24 帧、约 4 MiB 像素内存（至少 1 帧），在大小或屏幕缩放变化时重建。

## 验证与兼容性

发布文件在 **Windows 11 x64** 上，分别通过 Python 3.8.10 x64 / x86 和 PyInstaller 4.10 实际构建。

已检查透明图片、拖拽边界、动画相位、固定和置顶、托盘切换、单实例、异常锁释放、原生点击穿透命中、热键注册和消息处理，以及两个正式 exe 的启动和内嵌新形态。

新形态的 x64 / x86 检查覆盖两种动作、实际帧变化、缓存上限、三档尺寸无裁剪、暂停恢复、固定/置顶/穿透/隐藏联动和异常回退。

在 200% 缩放下，通过 `--form remielle` 启动高清形态，主进程工作集一次采样约为 x64 58.54 MiB、x86 48.66 MiB；原生源码应用播放新形态 6.1 秒后约 59.12 MiB，同进程 Q 版约 51.12 MiB。采样不是内存上限，也不包括 onefile 引导进程，见 [verification.json](verification.json) 和 [form-verification.json](form-verification.json)。

**目标为 Windows 7 SP1，但尚未在 Win7 实测。** PyInstaller 4.10 文档表示 Win7 不在其正式支持范围。请在目标 x86 / x64 系统复核透明窗口、系统托盘、单实例、onefile 启动，以及实际点击穿透和全局快捷键恢复；真实多屏与不同 DPI 也需人工复核。

完整说明见 [README.txt](README.txt)，采样结果见 [verification.json](verification.json)。透明 PNG 由用户提供的参考图经 AI 背景提取生成，部分线条有少量重绘，编辑提示词见 [image-edit-prompt.txt](image-edit-prompt.txt)。
