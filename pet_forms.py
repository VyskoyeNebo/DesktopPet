"""Transparent frame packs; rendering engines are not needed at runtime."""
import json
import zipfile

from PyQt5.QtGui import QImage


class FramePack:
    def __init__(self, path):
        self.archive = zipfile.ZipFile(str(path), "r")
        try:
            manifest_info = self.archive.getinfo("manifest.json")
            if manifest_info.file_size > 64 * 1024:
                raise ValueError("形态说明文件过大。")
            manifest = json.loads(self.archive.read("manifest.json").decode("utf-8"))
            if manifest.get("format") != "desktop-pet-frames-v1":
                raise ValueError("不支持的形态格式。")
            self.clips = manifest["clips"]
            self.default_clip = manifest["default_clip"]
            if not isinstance(self.clips, dict) or self.default_clip not in self.clips:
                raise ValueError("形态缺少默认动作。")
            for clip in self.clips.values():
                width, height = clip["size"]
                frames = clip["frames"]
                if not (1 <= width <= 1024 and 1 <= height <= 1024):
                    raise ValueError("形态画面尺寸无效。")
                if not (1 <= clip["fps"] <= 30 and 1 <= len(frames) <= 240):
                    raise ValueError("形态帧率或帧数无效。")
                for name in frames:
                    if self.archive.getinfo(name).file_size > 4 * 1024 * 1024:
                        raise ValueError("形态动画帧过大。")
        except Exception:
            self.archive.close()
            raise

    def frame_index(self, clip_name, seconds):
        clip = self.clips[clip_name]
        return int(max(0.0, seconds) * clip["fps"]) % len(clip["frames"])

    def frame_image(self, clip_name, index):
        clip = self.clips[clip_name]
        image = QImage.fromData(self.archive.read(clip["frames"][index]))
        if (image.isNull() or not image.hasAlphaChannel()
                or [image.width(), image.height()] != clip["size"]):
            raise ValueError("形态动画帧缺失、损坏或没有透明通道。")
        return image

    def close(self):
        self.archive.close()
