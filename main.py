"""Windows desktop pet. Build with CPython 3.8.10 and requirements.txt."""
import math
import os
import sys
import tempfile
import traceback
from collections import OrderedDict
from pathlib import Path

from PyQt5.QtCore import (
    QAbstractNativeEventFilter, QElapsedTimer, QLockFile, QPoint, QSize, Qt, QTimer,
)
from PyQt5.QtGui import QGuiApplication, QIcon, QImage, QPainter, QPixmap
from PyQt5.QtWidgets import (
    QApplication, QLabel, QMenu, QMessageBox, QSystemTrayIcon, QWidget,
)
from pet_forms import FramePack


def resource_path(name):
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / name


def load_pet_image(path):
    image = QImage(str(path))
    if image.isNull():
        raise ValueError("无法加载桌宠图片（文件缺失或损坏）：\n{}".format(path))
    if not image.hasAlphaChannel():
        raise ValueError("桌宠图片没有 alpha 通道，请使用透明 PNG：\n{}".format(path))
    if max(image.width(), image.height()) > 512:
        image = image.scaled(512, 512, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    return image


def create_lock():
    # Both architectures deliberately share the same per-user lock path.
    base = os.environ.get("LOCALAPPDATA") or tempfile.gettempdir()
    directory = Path(base) / "LightweightDesktopPet"
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except OSError:
        directory = Path(tempfile.gettempdir()) / "LightweightDesktopPet"
        directory.mkdir(parents=True, exist_ok=True)
    lock_file = QLockFile(str(directory / "pet.lock"))
    lock_file.setStaleLockTime(30_000)
    return lock_file


class GlobalHotkey(QAbstractNativeEventFilter):
    """Thread hotkey stays registered when Qt recreates the pet's HWND."""
    HOTKEY_ID = 0x5045

    def __init__(self, app, callback):
        super().__init__()
        self.app = app
        self.callback = callback
        self.registered = False
        self.error = ""
        self.sequence = "Ctrl+Alt+P"
        self.modifiers = 0x4003
        self._user32 = None

    def register(self):
        if self.registered:
            return True
        if sys.platform != "win32":
            self.error = "当前系统不支持 Windows 全局热键。"
            return False
        import ctypes
        from ctypes import wintypes
        self._user32 = ctypes.WinDLL("user32", use_last_error=True)
        self._user32.RegisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int,
                                               wintypes.UINT, wintypes.UINT]
        self._user32.RegisterHotKey.restype = wintypes.BOOL
        self._user32.UnregisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int]
        self._user32.UnregisterHotKey.restype = wintypes.BOOL
        # MOD_NOREPEAT prevents held keys from toggling repeatedly. Bind to
        # the GUI thread, not a QWidget HWND which changes with window flags.
        errors = []
        for modifiers, sequence in ((0x4003, "Ctrl+Alt+P"),
                                    (0x4007, "Ctrl+Alt+Shift+P")):
            if self._user32.RegisterHotKey(None, self.HOTKEY_ID, modifiers, ord("P")):
                self.sequence = sequence
                self.modifiers = modifiers
                break
            errors.append("{}：{}".format(sequence, ctypes.get_last_error()))
        else:
            self.error = "Windows 错误码 " + "；".join(errors)
            return False
        self.registered = True
        try:
            self.app.installNativeEventFilter(self)
            self.app.aboutToQuit.connect(self.close)
        except Exception:
            self.close()
            raise
        return True

    def nativeEventFilter(self, event_type, message):
        if self.registered and bytes(event_type) in (
                b"windows_generic_MSG", b"windows_dispatcher_MSG"):
            import ctypes
            from ctypes import wintypes
            native_message = wintypes.MSG.from_address(int(message))
            if native_message.message == 0x0312 and native_message.wParam == self.HOTKEY_ID:
                # Apply widget changes after native message dispatch completes.
                QTimer.singleShot(0, self.callback)
                return True, 0
        return False, 0

    def close(self):
        if self.registered:
            self._user32.UnregisterHotKey(None, self.HOTKEY_ID)
            self.registered = False
            self.app.removeNativeEventFilter(self)


class DesktopPet(QWidget):
    def __init__(self, app, image):
        super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.app = app
        self.setWindowTitle("轻量桌宠")
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setCursor(Qt.OpenHandCursor)
        self._source_pixmap = QPixmap.fromImage(image)
        self._source_pixmap.setDevicePixelRatio(1.0)
        self._default_pixmap = self._source_pixmap
        self._form_id = "default"
        self._form_pack = None
        self._motion = None
        self._motion_started_at = 0.0
        self._frame_index = -1
        self._frame_cache = OrderedDict()
        self._display_size = 128
        self._pixmap = self._source_pixmap.scaled(
            self._display_size, self._display_size,
            Qt.KeepAspectRatio, Qt.SmoothTransformation,
        )
        self._dragging = False
        self._position_fixed = False
        self._click_through = False
        self.hotkey = None
        self._drag_offset = QPoint()
        self._exiting = False
        self.accumulated_time = 0.0
        self.elapsed_timer = QElapsedTimer()
        self.animation_timer = QTimer(self)
        self.animation_timer.setInterval(60)
        self.animation_timer.timeout.connect(self._animate)

        self.label = QLabel(self)
        self.label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.label.setStyleSheet("background: transparent;")
        self._set_pixmap(self._pixmap)

        self._refresh_icon()

        self.menu = QMenu(self)
        self.visibility_action = self.menu.addAction("隐藏桌宠")
        self.visibility_action.triggered.connect(self.toggle_visibility)
        self.fixed_action = self.menu.addAction("固定位置")
        self.fixed_action.setCheckable(True)
        self.fixed_action.triggered.connect(self.set_position_fixed)
        self.topmost_action = self.menu.addAction("窗口置顶")
        self.topmost_action.setCheckable(True)
        self.topmost_action.setChecked(True)
        self.topmost_action.triggered.connect(self.set_always_on_top)
        self.click_through_action = self.menu.addAction("鼠标点击穿透\tCtrl+Alt+P")
        self.click_through_action.setCheckable(True)
        self.click_through_action.triggered.connect(self.set_click_through)
        form_menu = self.menu.addMenu("切换形态")
        self.form_actions = {}
        for form_id, title in (("default", "默认 Q 版"), ("remielle", "蕾米埃尔")):
            action = form_menu.addAction(title)
            action.setCheckable(True)
            action.setChecked(form_id == self._form_id)
            action.triggered.connect(lambda _checked=False, key=form_id: self.set_form(key))
            self.form_actions[form_id] = action
        self.motion_menu = self.menu.addMenu("形态动作")
        self.motion_menu.setEnabled(False)
        self.motion_actions = {}
        size_menu = self.menu.addMenu("调整大小")
        self.size_actions = {}
        for caption, side in (("小号", 96), ("标准", 128), ("大号", 192)):
            action = size_menu.addAction(caption)
            action.setCheckable(True)
            action.setChecked(side == self._display_size)
            action.triggered.connect(lambda _checked=False, size=side: self.set_display_size(size))
            self.size_actions[side] = action
        self.menu.addSeparator()
        self.exit_action = self.menu.addAction("退出程序")
        self.exit_action.triggered.connect(self.exit_program)
        self.menu.aboutToShow.connect(self._update_menu)

        self.tray = None
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray = QSystemTrayIcon(self.icon, self)
            self.tray.setToolTip("轻量桌宠 · 双击显示/隐藏 · 右键菜单")
            self.tray.setContextMenu(self.menu)
            self.tray.activated.connect(self._tray_activated)
            self.tray.show()
        else:
            self.visibility_action.setEnabled(False)
            QTimer.singleShot(0, self._warn_no_tray)

        screen = QGuiApplication.primaryScreen()
        if screen is None:
            raise RuntimeError("没有可用的显示器。")
        self.clamp_to_screen(screen=screen)
        area = screen.availableGeometry()
        self.move(area.right() - self.width() - 19,
                  area.bottom() - self.height() - 19)
        self.clamp_to_screen(screen=screen)
        # Keep the pet reachable after display removal or work-area changes.
        self.app.screenRemoved.connect(self._screen_removed)
        self.app.screenAdded.connect(self._connect_screen)
        for current_screen in self.app.screens():
            self._connect_screen(current_screen)
        self.app.aboutToQuit.connect(self._close_form_assets)

    def _refresh_icon(self):
        icon_pixmap = QPixmap(32, 32)
        icon_pixmap.fill(Qt.transparent)
        thumbnail = self._source_pixmap.scaled(32, 32, Qt.KeepAspectRatio,
                                               Qt.SmoothTransformation)
        painter = QPainter(icon_pixmap)
        painter.drawPixmap((32 - thumbnail.width()) // 2,
                           (32 - thumbnail.height()) // 2, thumbnail)
        painter.end()
        self.icon = QIcon(icon_pixmap)
        self.setWindowIcon(self.icon)
        tray = getattr(self, "tray", None)
        if tray is not None:
            tray.setIcon(self.icon)

    def _close_form_assets(self):
        if self._form_pack is not None:
            self._form_pack.close()
            self._form_pack = None
        self._frame_cache.clear()

    def _sync_form_actions(self):
        for key, action in self.form_actions.items():
            action.setChecked(key == self._form_id)
        for key, action in self.motion_actions.items():
            action.setChecked(key == self._motion)

    def _apply_form_pixmap(self, pixmap):
        anchor = self.frameGeometry().bottomRight()
        screen = QGuiApplication.screenAt(self.frameGeometry().center())
        self._source_pixmap = pixmap
        self._source_pixmap.setDevicePixelRatio(1.0)
        self._set_pixmap(pixmap.scaled(self._display_size, self._display_size,
                                      Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self._place_label(self._animation_time())
        self.move(anchor.x() - self.width() + 1, anchor.y() - self.height() + 1)
        self.clamp_to_screen(screen=screen)
        self._refresh_icon()

    def set_form(self, form_id):
        if form_id == self._form_id:
            self._sync_form_actions()
            return
        pack = None
        try:
            if form_id == "remielle":
                pack = FramePack(resource_path("forms/remielle.pet"))
                motion = pack.default_clip
                pixmap = QPixmap.fromImage(pack.frame_image(motion, 0))
            elif form_id == "default":
                motion = None
                pixmap = self._default_pixmap
            else:
                raise ValueError("未知形态。")
        except Exception as error:
            if pack is not None:
                pack.close()
            self._sync_form_actions()
            QMessageBox.warning(self, "无法切换形态", str(error))
            return
        self._close_form_assets()
        self._form_id, self._form_pack, self._motion = form_id, pack, motion
        self._motion_started_at = self._animation_time()
        self.motion_menu.clear()
        self.motion_actions = {}
        self.motion_menu.setEnabled(pack is not None)
        if pack is not None:
            for key, clip in pack.clips.items():
                action = self.motion_menu.addAction(clip["title"])
                action.setCheckable(True)
                action.triggered.connect(lambda _checked=False, name=key: self.set_motion(name))
                self.motion_actions[key] = action
        self._apply_form_pixmap(pixmap)
        self._sync_form_actions()

    def set_motion(self, motion):
        if self._form_pack is None or motion not in self._form_pack.clips:
            return
        if motion == self._motion:
            self._sync_form_actions()
            return
        try:
            pixmap = QPixmap.fromImage(self._form_pack.frame_image(motion, 0))
        except Exception as error:
            self._sync_form_actions()
            QMessageBox.warning(self, "无法切换动作", str(error))
            return
        self._motion = motion
        self._motion_started_at = self._animation_time()
        self._apply_form_pixmap(pixmap)
        self._sync_form_actions()

    def _update_form_frame(self, seconds):
        if self._form_pack is None:
            return
        index = self._form_pack.frame_index(self._motion, seconds - self._motion_started_at)
        if index == self._frame_index:
            return
        try:
            frame = self._frame_cache.get(index)
            if frame is None:
                image = self._form_pack.frame_image(self._motion, index)
                frame = QPixmap.fromImage(image).scaled(
                    self.label.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
                self._frame_cache[index] = frame
                if len(self._frame_cache) > 24:
                    self._frame_cache.popitem(last=False)
            else:
                self._frame_cache.move_to_end(index)
            self._pixmap = frame
            self.label.setPixmap(frame)
            self._frame_index = index
        except Exception as error:
            self.set_form("default")
            message = str(error)
            QTimer.singleShot(0, lambda: QMessageBox.warning(
                self, "形态动画损坏", "已恢复默认形态。\n" + message))

    def _connect_screen(self, screen):
        screen.availableGeometryChanged.connect(self._work_area_changed)

    def _screen_removed(self, _screen):
        QTimer.singleShot(0, self._work_area_changed)

    def _work_area_changed(self, *_args):
        if not self._dragging:
            self.clamp_to_screen()

    def _set_pixmap(self, pixmap):
        self._frame_cache.clear()
        self._frame_index = -1
        self._pixmap = pixmap
        self.setFixedSize(pixmap.width(), pixmap.height() + 6)
        self.label.setPixmap(pixmap)
        self.label.setFixedSize(pixmap.size())
        self.label.move(0, 3)

    def clamp_to_screen(self, global_position=None, screen=None):
        if screen is None:
            point = global_position if global_position is not None else self.frameGeometry().center()
            screen = QGuiApplication.screenAt(point)
        if screen is None:
            screen = QGuiApplication.primaryScreen()
        if screen is None:
            return
        area = screen.availableGeometry()
        if area.width() < 1 or area.height() <= 6:
            return
        if self.width() > area.width() or self.height() > area.height():
            fitted = self._source_pixmap.scaled(
                QSize(area.width(), area.height() - 6),
                Qt.KeepAspectRatio, Qt.SmoothTransformation,
            )
            self._set_pixmap(fitted)
            self._place_label(self._animation_time())
        # Full containment is stronger than retaining only a 30 px clickable strip.
        max_x = area.x() + area.width() - self.width()
        max_y = area.y() + area.height() - self.height()
        self.move(max(area.x(), min(self.x(), max_x)),
                  max(area.y(), min(self.y(), max_y)))

    def set_display_size(self, longest_side):
        anchor = self.frameGeometry().bottomRight()
        screen = QGuiApplication.screenAt(self.frameGeometry().center())
        self._display_size = longest_side
        self._set_pixmap(self._source_pixmap.scaled(
            longest_side, longest_side, Qt.KeepAspectRatio, Qt.SmoothTransformation,
        ))
        self._place_label(self._animation_time())
        self.move(anchor.x() - self.width() + 1, anchor.y() - self.height() + 1)
        self.clamp_to_screen(screen=screen)
        for side, action in self.size_actions.items():
            action.setChecked(side == longest_side)

    def _animation_time(self):
        extra = self.elapsed_timer.elapsed() / 1000.0 if self.elapsed_timer.isValid() else 0.0
        return self.accumulated_time + extra

    def _update_cursor(self):
        self.setCursor(Qt.ArrowCursor if self._position_fixed or self._click_through
                       else Qt.OpenHandCursor)

    def set_position_fixed(self, fixed):
        self._position_fixed = bool(fixed)
        self.fixed_action.setChecked(self._position_fixed)
        if self._dragging:
            self._dragging = False
            self.clamp_to_screen()
            self._resume_animation()
        self._update_cursor()

    def set_always_on_top(self, enabled):
        enabled = bool(enabled)
        self.topmost_action.setChecked(enabled)
        self._set_window_option(Qt.WindowStaysOnTopHint, enabled)

    def _set_window_option(self, flag, enabled):
        if bool(self.windowFlags() & flag) == enabled:
            return
        was_visible = self.isVisible()
        position = QPoint(self.pos())
        # Updating window flags recreates the native window and hides it.
        # hideEvent/showEvent preserve the accumulated animation phase.
        self.setWindowFlag(flag, enabled)
        self.move(position)
        if was_visible:
            self.show()
            if self.windowFlags() & Qt.WindowStaysOnTopHint:
                self.raise_()

    def initialize_hotkey(self):
        self.hotkey = GlobalHotkey(self.app, self.toggle_click_through)
        try:
            registered = self.hotkey.register()
        except OSError as error:
            self.hotkey.error = str(error)
            registered = False
        if not registered:
            QTimer.singleShot(0, self._warn_hotkey_unavailable)
        elif self.hotkey.sequence != "Ctrl+Alt+P":
            QTimer.singleShot(0, self._notify_fallback_hotkey)
        sequence = self.hotkey.sequence if registered else "快捷键不可用"
        self.click_through_action.setText("鼠标点击穿透\t{}".format(sequence))
        self._update_tray_tooltip()
        self._update_menu()

    def _notify_fallback_hotkey(self):
        message = "Ctrl+Alt+P 已被占用，恢复交互请按 {}。".format(self.hotkey.sequence)
        if self._tray_available():
            self.tray.showMessage("桌宠恢复快捷键", message, QSystemTrayIcon.Information, 8000)
        else:
            QMessageBox.warning(self, "恢复快捷键已调整", message)

    def _update_tray_tooltip(self):
        if self.tray is not None:
            sequence = (self.hotkey.sequence if self.hotkey is not None and self.hotkey.registered
                        else "托盘菜单切换穿透")
            self.tray.setToolTip("轻量桌宠 · {} · {}".format(
                "点击穿透已开启" if self._click_through else "可交互", sequence))

    def _warn_hotkey_unavailable(self):
        QMessageBox.warning(
            self, "恢复快捷键不可用",
            "Ctrl+Alt+P 和 Ctrl+Alt+Shift+P 均注册失败，可能已被其他程序占用。\n"
            "可通过托盘菜单切换穿透；托盘也不可用时将禁用穿透。\n{}".format(
                self.hotkey.error if self.hotkey is not None else ""),
        )

    def _can_restore_interaction(self):
        return bool(self.hotkey is not None and self.hotkey.registered) or self._tray_available()

    def set_click_through(self, enabled):
        enabled = bool(enabled)
        if enabled and not self._can_restore_interaction():
            self.click_through_action.setChecked(self._click_through)
            QMessageBox.warning(self, "无法开启点击穿透",
                                "全局快捷键和系统托盘均不可用，无法恢复交互。")
            return
        self._click_through = enabled
        self.click_through_action.setChecked(enabled)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, enabled)
        # On Windows, Qt applies WS_EX_TRANSPARENT to this layered window,
        # allowing clicks to reach windows in other applications underneath.
        self._set_window_option(Qt.WindowTransparentForInput, enabled)
        self._update_cursor()
        self._update_tray_tooltip()

    def toggle_click_through(self):
        self.set_click_through(not self._click_through)

    def _place_label(self, seconds):
        self._update_form_frame(seconds)
        offset = 3.0 * math.sin(2.0 * math.pi * seconds / 2.0)
        self.label.move(0, 3 + int(round(offset)))

    def _animate(self):
        self._place_label(self._animation_time())

    def _pause_animation(self):
        if self.elapsed_timer.isValid():
            self.accumulated_time += self.elapsed_timer.elapsed() / 1000.0
            self.elapsed_timer.invalidate()
        self.animation_timer.stop()
        self._place_label(self.accumulated_time)

    def _resume_animation(self):
        if self.isVisible() and not self._dragging and not self._exiting:
            if not self.elapsed_timer.isValid():
                self._place_label(self.accumulated_time)
                self.elapsed_timer.start()
            self.animation_timer.start()

    def showEvent(self, event):
        super().showEvent(event)
        self._resume_animation()

    def hideEvent(self, event):
        self._pause_animation()
        self._dragging = False
        self._update_cursor()
        super().hideEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self._position_fixed or self._click_through:
                event.accept()
                return
            self._dragging = True
            self._drag_offset = event.globalPos() - self.pos()
            self._pause_animation()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if (self._dragging and not self._position_fixed and not self._click_through
                and event.buttons() & Qt.LeftButton):
            self.move(event.globalPos() - self._drag_offset)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._dragging:
            self._dragging = False
            self._update_cursor()
            self.clamp_to_screen(global_position=event.globalPos())
            self._resume_animation()
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def contextMenuEvent(self, event):
        if self._click_through:
            event.ignore()
            return
        self.menu.exec_(event.globalPos())
        event.accept()

    def _tray_activated(self, reason):
        # Ignore Trigger: Windows emits it alongside DoubleClick.
        if reason == QSystemTrayIcon.DoubleClick:
            self.toggle_visibility()

    def _tray_available(self):
        return self.tray is not None and QSystemTrayIcon.isSystemTrayAvailable()

    def _update_menu(self):
        self.visibility_action.setText("隐藏桌宠" if self.isVisible() else "显示桌宠")
        self.visibility_action.setEnabled(self._tray_available())
        self.fixed_action.setChecked(self._position_fixed)
        self.topmost_action.setChecked(bool(self.windowFlags() & Qt.WindowStaysOnTopHint))
        self.click_through_action.setChecked(self._click_through)
        self.click_through_action.setEnabled(self._click_through or self._can_restore_interaction())
        self._sync_form_actions()

    def _warn_no_tray(self):
        QMessageBox.warning(self, "系统托盘不可用",
                            "系统托盘不可用，已禁用隐藏入口。\n可右键桌宠并选择“退出程序”。")

    def toggle_visibility(self):
        if self.isVisible():
            if not self._tray_available():
                self.visibility_action.setEnabled(False)
                self._warn_no_tray()
                return
            self.hide()
        else:
            self.clamp_to_screen()
            self.show()
            self.raise_()

    def exit_program(self):
        self._exiting = True
        self._pause_animation()
        if self.tray is not None:
            self.tray.hide()
        self.app.quit()

    def closeEvent(self, event):
        self.exit_program()
        event.accept()


def main():
    app = None
    lock_file = None
    pet = None
    try:
        lock_file = create_lock()
        if not lock_file.tryLock(0):
            lock_file.removeStaleLockFile()
            if not lock_file.tryLock(0):
                return 0

        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        app = QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)
        app.aboutToQuit.connect(lock_file.unlock)
        app.setApplicationName("LightweightDesktopPet")
        image = load_pet_image(resource_path("pet.png"))
        pet = DesktopPet(app, image)
        pet.initialize_hotkey()

        def handle_exception(exc_type, exc_value, exc_traceback):
            details = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
            if sys.stderr is not None:
                sys.stderr.write(details)
            QMessageBox.critical(pet, "桌宠运行错误", str(exc_value))
            pet.exit_program()

        sys.excepthook = handle_exception
        pet.show()
        return app.exec_()
    except Exception as error:
        if sys.stderr is not None:
            traceback.print_exc()
        if app is not None:
            QMessageBox.critical(None, "桌宠启动失败", str(error))
            if pet is not None:
                pet.exit_program()
            # quit() before exec_() has no effect; run one iteration to emit
            # aboutToQuit and release the lock through the connected signal.
            QTimer.singleShot(0, app.quit)
            app.exec_()
        elif sys.platform == "win32":
            import ctypes
            ctypes.windll.user32.MessageBoxW(None, str(error), "桌宠启动失败", 0x10)
        return 1
    finally:
        if app is None and lock_file is not None and lock_file.isLocked():
            lock_file.unlock()


if __name__ == "__main__":
    sys.exit(main())
