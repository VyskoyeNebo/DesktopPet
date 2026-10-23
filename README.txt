轻量 Windows 桌宠

文件位置：D:\Pet
目标：Windows 7 SP1，x86 / x64；安装对应位数的 VC++ 2015–2019 运行库。
构建环境：Windows 11 专业版 10.0.26200 x64。
解释器：CPython 3.8.10，分别使用官方 x86 和 x64 解释器。
核心依赖：PyQt5 5.15.9、Qt 5.15.2、PyInstaller 4.10。
完整锁定版本见 requirements.txt。

使用
1. 64 位系统运行 Pet_x64.exe；32 位系统运行 Pet_x86.exe。
   exe 已内置 Python、Qt 和图片，无需安装 Python，也无需旁放 pet.png。
2. 默认 Q 版长边 128、蕾米埃尔长边 384，单位为逻辑像素。
   高 DPI 系统按实际像素生成显示图像，例如 200% 下 384 对应 768 像素。
   右键桌宠或托盘 → 调整大小 → 96、128、192、256、384、512 六档。
   两种形态分别记忆本次运行选择的大小，下次启动恢复各自默认值。
   右键 → 切换形态 → 默认 Q 版 / 蕾米埃尔。
   蕾米埃尔支持“形态动作”菜单中的两种循环动作，默认动作二。
   两种形态均支持固定、置顶、隐藏和点击穿透；隐藏或拖动时暂停动作，
   恢复后沿用暂停时刻，不从头重播。
3. 左键拖拽，释放后自动缩小或校正到所在屏幕的可用区域。
   右键桌宠或托盘 → 勾选“固定位置”可禁止拖动，取消勾选恢复拖动。
   固定时仍保留轻微浮动动画，显示/隐藏后固定状态继续有效；
   下次重新启动默认允许拖动。
4. 托盘双击显示/隐藏；右键菜单也可显示/隐藏或退出。
   系统托盘不可用时会警告并禁用隐藏入口。
   右键桌宠或托盘 → “窗口置顶”：默认勾选，保持在普通窗口之上；
   取消勾选后恢复普通窗口层级，再次勾选即可置顶。
   切换时保留当前位置、大小和固定状态；隐藏中的桌宠保持隐藏。
   下次重新启动默认启用置顶。
   右键桌宠或托盘 → “鼠标点击穿透”：开启后，鼠标操作会穿过桌宠，
   到达下方窗口，无法直接拖动或右键桌宠；托盘菜单仍可操作。
   全局快捷键 Ctrl+Alt+P 切换穿透/可交互，无需桌宠位于前台。
   如果该组合被占用，自动尝试 Ctrl+Alt+Shift+P，并在托盘通知、
   托盘提示及菜单中标明实际快捷键。实际可用组合以菜单显示为准。
   按住快捷键不会因键盘自动重复而连续切换。
   两组快捷键都注册失败时会提示；仍可通过托盘取消穿透。
   全局快捷键和托盘都不可用时禁止开启穿透，避免无法恢复操作。
   默认关闭穿透；隐藏、置顶和固定功能与穿透状态独立。
   热键随程序退出释放，未增加第三方依赖。
5. x86、x64、源码和调试版共用同一用户的单实例锁。
   多次启动只保留一个主程序实例。onefile 本身有引导和主进程，
   任务管理器中看到同一次启动的两个进程属于 PyInstaller 的正常结构。

图片
pet.png 为真正带 alpha 的 PNG，512 x 494 像素；背景角点 alpha=0。
使用内置 image_gen 做背景提取，生成结果经 QImage 等比缩小并校验。
AI 抠图对原图线条有少量重绘；PNG 原始分辨率保留，显示时另行缩放。
原始 JPG 保持不变。完整编辑提示词见 image-edit-prompt.txt。
源码从自身目录读取 pet.png；exe 从 PyInstaller 内置资源目录读取图片。
若替换图片，源码可直接使用新图；exe 需要重新打包。

蕾米埃尔形态来自用户提供的 Spine 素材，离线渲染后存入 forms\remielle.pet。
包含两种动作，每种 64 帧，12 fps，尺寸为 1024 x 641 / 1024 x 655。
动画从原始骨骼与贴图重新渲染，以高品质透明 WebP（画质 96）存储，
由 Qt 自带 WebP 插件解码。窗口图像保留真实 DPI 像素及 devicePixelRatio，
避免先缩成逻辑像素、再被 Windows 放大造成模糊。
运行时使用 Qt 播放透明帧，不安装或内置 Spine、浏览器或 Node 动画引擎。
动画按需读取，缓存最多 24 帧并限制约 4 MiB 像素内存（至少保留 1 帧）。
切换动作、大小或屏幕缩放比例会清理并重建缓存。
缺失或损坏的形态文件会提示；后续动画帧损坏时恢复默认形态。
Windows 原生源码应用在 200% 缩放下播放新形态 6.1 秒后，工作集一次采样
约 59.12 MiB，同一进程默认形态约 51.12 MiB；这不是长期峰值或内存上限。
也可使用 Pet_x64.exe --form remielle 直接启动蕾米埃尔形态。

构建
在 D:\Pet 中执行，确保解释器精确为 3.8.10：
源码目录需要 main.py、pet_forms.py、pet.png 及 forms\remielle.pet。
  build_x64.bat "C:\对应64位Python目录\python.exe"
  build_x86.bat "C:\对应32位Python目录\python.exe"
  build_debug.bat "C:\对应64位Python目录\python.exe"
不传解释器路径时，脚本尝试 py -3.8-64 或 py -3.8-32。
脚本会检查版本与位数，安装锁定依赖，分别使用独立构建缓存。

实际执行的完整打包参数（通过对应解释器 -m PyInstaller）：
64 位：
  pyinstaller --noconfirm --clean --onefile --windowed --noupx ^
    --name Pet_x64 --add-data "D:\Pet\pet.png;." --add-data "D:\Pet\forms;forms" ^
    --distpath "D:\Pet" --workpath "D:\Pet\build_x64" --specpath "D:\Pet\spec_x64" main.py
32 位：
  pyinstaller --noconfirm --clean --onefile --windowed --noupx ^
    --name Pet_x86 --add-data "D:\Pet\pet.png;." --add-data "D:\Pet\forms;forms" ^
    --distpath "D:\Pet" --workpath "D:\Pet\build_x86" --specpath "D:\Pet\spec_x86" main.py
调试版：--console 替代 --windowed，名称 Pet_x64_debug。
源码、两个正式 exe 和调试 exe 均已实际生成。

已验证的范围
- x64 和 x86 各 8 项 Qt 自动检查通过（使用 offscreen 测试平台）：
  alpha 与尺寸、窗口属性、QLabel 鼠标穿透属性、整个动画周期无裁剪、
  大小菜单、固定后禁止拖动及取消固定后恢复、拖拽实时位移、
  释放校正、负坐标小屏缩放及主屏回退、
  暂停/恢复时间和相位、托盘双击只切换一次、菜单显示文字、
  无托盘时禁用隐藏并警告、异常图片、退出顺序。
- 正常退出、图片缺失、图片损坏、QApplication 创建失败场景中，
  锁均可再次获取；错误弹框调用经过检查，自动测试中拦截了弹框显示。
- x64 持锁时 x86 不能取得锁；超过 30 秒后仍不能夺取活实例的锁。
- 两个正式 exe 均在 Windows 11 上实际启动，加载 qwindows.dll 和
  Qt5Widgets.dll；分别重复及跨位数启动 3 次，新增启动均正常退出。
- exe PE 架构、内嵌 pet.png 和 qwindows.dll 均已检查。
- x64 / x86 均通过 Windows 原生扩展样式检查：窗口置顶开关会实际
  添加/移除 WS_EX_TOPMOST，同时保留工具窗口属性；切换前后位置、
  大小、固定状态、显示/隐藏状态和动画相位保持正确。
- x64 / x86 均通过实际 Windows 输入命中测试：穿透前可命中桌宠，
  穿透后同一位置不再命中桌宠；原生透明输入样式已设置。
  已验证全局热键注册及 WM_HOTKEY 消息经 Qt 事件循环切换状态、
  重建窗口后快捷键仍有效、托盘共用菜单仍可取消穿透、
  热键释放及恢复入口不可用的兜底。
  自动测试通过投递 WM_HOTKEY 验证消息处理；实际键盘按键仍需人工复核。
最终启动检查的体积及主进程工作集见 verification.json。
新形态源码应用的内存采样见 form-verification.json。
新形态的 x64 / x86 检查覆盖两种动作、64 帧播放、缓存上限、
三档尺寸无裁剪、暂停恢复、与固定/置顶/穿透/隐藏状态的联动及异常回退。
工作集是启动后一次采样，不是内存上限，也不含 onefile 引导进程。

未验证的范围及 Win7 SP1 复核清单
本机不是 Win7，未在 Win7 SP1 实测，不能据此保证 Win7 兼容。
PyInstaller 4.10 官方说明 Windows 7 可能工作，但不在其支持范围内。
需要在目标 Win7 SP1 x86 / x64 机器复核：
1. 安装相应架构的 VC++ 2015–2019 运行库后，onefile 首次和重复启动；
   检查临时解包目录权限、启动耗时、是否缺少运行库/DLL。
2. 透明窗口边缘、白色角色部位、置顶、不占任务栏、高 DPI 显示；
   包括目标机器的 Aero / 桌面合成设置。
3. 系统托盘出现、显示/隐藏、双击只切换一次、右键退出及无托盘兜底。
4. 多次启动和跨位数启动只出现一个桌宠；正常及异常退出后再次启动。
5. 在真实多显示器、不同 DPI、负坐标屏幕上拖拽、释放和屏幕断开；
   当前多屏边界检查使用模拟几何，未进行真实多屏人工拖拽。
6. 图片缺失/损坏时弹框可见，关闭弹框后程序退出且锁释放。
   测试源码时可临时移动 pet.png 后运行 main.py；exe 图片已内置。
7. 长时间运行的内存和动画、休眠唤醒后的行为。
8. 点击穿透是否能点击下方其他应用；后台按菜单所示全局快捷键恢复；
   按住不重复切换；托盘菜单恢复；快捷键冲突及无托盘时的兜底。

参考资料
Python 3.8.10 官方发行及 x86/x64 安装器：
https://www.python.org/downloads/release/python-3810/
PyInstaller 4.10 的系统要求和 Win7 支持说明：
https://pyinstaller.org/en/v4.10/requirements.html
Windows 全局热键注册及重复按键抑制：
https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-registerhotkey
Windows 分层窗口及透明输入命中规则：
https://learn.microsoft.com/en-us/windows/win32/winmsg/window-features
Spine 官方离线渲染接口（仅用于开发时生成帧）：
https://esotericsoftware.com/spine-canvaskit
