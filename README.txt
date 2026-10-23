文件位置：D:\Pet

# DesktopPet

Python + PyQt5 Windows 桌宠，支持五种形态、透明动画、拖拽、托盘、置顶、固定位置、点击穿透和全局快捷键恢复。

<img src="pet.png" width="128" alt="Q版蕾米">
<img src="forms/remielle-preview.png" width="180" alt="蕾米埃尔">
<img src="forms/xingjianya-preview.png" width="115" alt="星见雅">
<img src="forms/promeia-preview.png" width="115" alt="普罗米娅">
<img src="forms/yixuan-preview.png" width="115" alt="仪玄">

## 下载

[下载 v1.2.0 全部版本](https://github.com/VyskoyeNebo/DesktopPet/releases/tag/v1.2.0)

| 文件 | 体积 |
| --- | --- |
| [Pet_x64.exe](https://github.com/VyskoyeNebo/DesktopPet/releases/download/v1.2.0/Pet_x64.exe) | 109.9 MiB |
| [Pet_x86.exe](https://github.com/VyskoyeNebo/DesktopPet/releases/download/v1.2.0/Pet_x86.exe) | 103.26 MiB |
| [Pet_x64_debug.exe](https://github.com/VyskoyeNebo/DesktopPet/releases/download/v1.2.0/Pet_x64_debug.exe) | 109.89 MiB |

Pet_x64.exe 为 64 位正式版，Pet_x86.exe 为 32 位正式版；Pet_x64_debug.exe 带控制台，供排查问题。三个 exe 内置 Python、Qt 和全部形态，无需安装 Python；目标机器需安装对应位数的 VC++ 2015–2019 运行库。发布页附有 SHA256SUMS.txt，历史 Releases 保留旧版本。

## 操作

- **形态**：右键桌宠或托盘 → 切换形态 → Q版蕾米 / 蕾米埃尔 / 星见雅 / 普罗米娅 / 仪玄。
- **动作**：右键 → 形态动作。Q版默认动作 A，提供静态姿势及其他素材动作；蕾米埃尔有两种循环，默认动作二；其他形态播放各自循环。
- **取消上下晃动**：所有形态的图片位置固定，已移除程序附加的上下浮动。素材自身的角色动作保留；Q版可选择“静态姿势”。
- **大小**：96、128、192、256、384、512 六档，单位为逻辑像素。Q版默认 128，其他形态默认 384；各形态分别记忆本次运行的大小。
- **拖动 / 固定**：左键拖动；释放后缩小或校正到显示器可用区域。右键勾选“固定位置”禁止拖动。
- **置顶**：右键“窗口置顶”，默认开启；切换时保留位置、大小和状态。
- **显示 / 隐藏**：双击托盘或使用菜单。拖动、隐藏时暂停角色动作，恢复后继续。
- **穿透 / 恢复**：右键开启“鼠标点击穿透”，鼠标可操作下方窗口。全局热键 Ctrl+Alt+P 切换穿透；若冲突自动尝试 Ctrl+Alt+Shift+P，以菜单和托盘显示为准。也可在托盘取消穿透。按住热键不会因自动重复而反复切换。
- **退出**：桌宠或托盘右键 → 退出程序。

托盘不可用会提示并禁用隐藏。托盘和热键同时不可用时禁止开启穿透。默认允许拖动、置顶、关闭穿透；设置保留到本次运行结束。x64、x86、源码与调试版共用单实例锁。onefile 启动时可能出现引导和主程序两个进程。

## 动画与清晰度

全部形态来自用户提供的 Spine 骨骼与贴图，开发时离线渲染为高品质透明 WebP（画质 96、12 fps、最长边 1024 像素）。Q版已替换为新提供的 Q版蕾米素材，静态备用 pet.png 为带 alpha 的 475 × 512 PNG。

| 形态 | 动作与帧数 | 默认显示长边 |
| --- | --- | --- |
| Q版蕾米 | 9 个选项，共 318 帧，含 1 帧静态姿势 | 128 |
| 蕾米埃尔 | 两种动作，各 64 帧 | 384 |
| 星见雅 | 128 帧 | 384 |
| 普罗米娅 | 64 帧 | 384 |
| 仪玄 | 80 帧 | 384 |

Qt 自带 WebP 插件解码；运行时无需 Spine、Node.js、浏览器或额外动画引擎。保留实际 DPI 像素及 devicePixelRatio，例如 200% 缩放下 384 逻辑像素对应 768 像素图像。缓存最多 24 帧并限制约 4 MiB 像素内存（至少 1 帧）；切换形态关闭旧包并清空缓存。高清形态会增加 exe 体积。

## 源码与构建

使用对应位数的 **CPython 3.8.10**，核心依赖为 PyQt5 5.15.9、Qt 5.15.2、PyInstaller 4.10，完整版本见 [requirements.txt](requirements.txt)。

```bat
python -m pip install -r requirements.txt
python main.py
```

保留 main.py、pet_forms.py、pet.png 和 forms 目录中的五个 .pet 文件。可用 --form default / remielle / xingjianya / promeia / yixuan 直接启动指定形态，例如 `Pet_x64.exe --form yixuan`。图片缺失、损坏或不带 alpha 时提示并退出；形态包加载失败时提示，损坏动画帧恢复 Q版静态备用图，再次选择 Q版可重试加载。

将源码、资源、依赖与三个脚本放入 D:\Pet，再分别运行：

```bat
build_x64.bat "C:\Python38-x64\python.exe"
build_x86.bat "C:\Python38-x86\python.exe"
build_debug.bat "C:\Python38-x64\python.exe"
```

脚本检查版本和位数、安装锁定依赖，使用独立缓存；正式版使用 --onefile --windowed --noupx，调试版使用 --console。32 位 exe 必须用 32 位 Python 构建。

## 验证与兼容性

三个版本均在 Windows 11 x64 使用 Python 3.8.10 / PyInstaller 4.10 实际构建。x64 / x86 检查覆盖五形态、14 个动作、718 帧、透明边界、无附加上下浮动、缓存预算、暂停恢复、独立尺寸记忆、关闭旧包以及固定/置顶/穿透/隐藏联动；新增 Q版损坏帧静态回退和重新加载检查。原有拖拽、托盘、锁释放、原生点击穿透和热键消息处理检查保留。

两个正式 exe 均校验全部五个内嵌形态包，并分别以 Q版蕾米 / 仪玄实际启动，各进行 3 次重复或跨位数启动检查。主进程工作集一次采样为 x64 62.02 MiB（Q版）、x86 50.14 MiB（仪玄）。这是一次采样，非长期峰值或内存上限，不含 onefile 引导进程。见 [verification.json](verification.json) 和 [new-forms-verification.json](new-forms-verification.json)；[form-verification.json](form-verification.json) 为历史蕾米埃尔采样。

**目标为 Windows 7 SP1，未在 Win7 实测。** PyInstaller 4.10 文档将 Win7 列于正式支持范围之外。请在目标 Win7 SP1 x86 / x64 上复核：

1. 对应架构 VC++ 2015–2019 运行库、onefile 首次及重复启动、解包权限和缺少 DLL 的情况。
2. 透明窗口、边缘、置顶、不占任务栏，以及 Aero / 桌面合成与高 DPI 显示。
3. 托盘显示、隐藏、双击只切换一次、右键退出及无托盘兜底。
4. 多次和跨位数启动、异常退出后的锁释放。
5. 真实多屏、不同 DPI、负坐标屏幕、拖动释放、显示器断开和尺寸兜底。
6. 图片与动画损坏时弹框可见、静态回退、正常退出和重新启动。
7. 点击穿透下方应用、实际键盘快捷键恢复、按住不重复触发和热键冲突；自动测试的热键部分通过投递 WM_HOTKEY 检查，仍需真人按键复核。
8. 长时间运行内存、动画、休眠唤醒。真实多屏及 Win7 的这些项目尚未实测。

历史 AI 抠图提示词保留于 image-edit-prompt.txt，仅对应旧版本图片，当前 Q版来自新素材。

参考：[Python 3.8.10](https://www.python.org/downloads/release/python-3810/)、[PyInstaller 4.10 系统要求](https://pyinstaller.org/en/v4.10/requirements.html)、[Windows RegisterHotKey](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-registerhotkey)、[Spine 离线渲染接口](https://esotericsoftware.com/spine-canvaskit)。
