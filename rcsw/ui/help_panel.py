from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    StrongBodyLabel,
    BodyLabel,
    ScrollArea,
)

from .style import PANEL_BG, TransparentCard

_HELP_CONTENT = [
    ("快速上手", [
        "1. 在「文件」页面添加需要处理的 PDF 文件（可拖拽或点击按钮选择）",
        "2. 在「处理设置」中配置：缩放模式、输出质量、水印尺寸、水印位置、输出目录",
        "3. 点击底部「开始处理」按钮，等待进度完成",
        "4. 处理后的文件保存在输出目录，文件名添加 _RCSW 后缀",
        "提示：所有处理设置更改即时生效，无需手动保存。",
    ]),
    ("支持的 PDF 格式", [
        "本软件专为「扫描全能王」生成的 PDF 设计",
        "每页应包含一张扫描图片和一个水印图标",
        "水印通常位于页面右下角的小尺寸图片",
        "页面中的文本内容将被移除，仅保留图片",
    ]),
    ("缩放模式说明", [
        "填充整页（居中裁剪）— 等比缩放覆盖整页，超出部分居中裁剪，无白边",
        "适应页面（留白边距）— 等比缩放完整放入页面，可能留下白边",
        "拉伸至整页 — 直接拉伸填满整页，图片可能变形",
        "适应宽度 — 等比缩放至页面宽度，高度可能超出或留白",
        "适应高度 — 等比缩放至页面高度，宽度可能超出或留白",
    ]),
    ("输出质量说明", [
        "低质量 — DPI=150, JPEG=75，文件最小",
        "中等质量 — DPI=200, JPEG=90，推荐日常使用",
        "高质量 — DPI=300, JPEG=95，文件较大",
        "原图 — 保持原始分辨率，JPEG=100，文件最大，默认选项",
    ]),
    ("水印检测", [
        "自动检测 — 根据尺寸和多页一致性自动识别水印，推荐",
        "右下角 — 仅移除右下角的小尺寸图片",
        "左下角 / 右上角 / 左上角 / 底部居中 — 指定位置检测",
        "可通过「最大水印尺寸」滑块调整检测阈值（100-1000px，默认 500）",
    ]),
    ("软件设置", [
        "浅色 / 深色 / 跟随系统 — 切换界面主题",
        "关闭窗口时最小化到系统托盘 — 点击关闭按钮不退出",
        "窗口失焦时使用系统通知 — 处理完成后弹出系统通知",
        "处理完成后打开输出文件夹 — 自动打开文件资源管理器",
        "日志 — 可导出调试日志文件，清除缓存释放空间",
        "重置设置 — 恢复所有软件和处理设置为默认值",
    ]),
]


class HelpPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("helpPanel")
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet(PANEL_BG)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)

        title = StrongBodyLabel("帮助")
        title.setObjectName("panelTitle")
        layout.addWidget(title)

        scroll = ScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        root = QWidget()
        root.setAutoFillBackground(False)
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 8, 0, 0)
        root_layout.setSpacing(16)

        for section_title, lines in _HELP_CONTENT:
            card = TransparentCard()
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(16, 12, 16, 16)
            card_layout.setSpacing(8)

            heading = StrongBodyLabel(section_title)
            heading.setObjectName("helpSectionTitle")
            card_layout.addWidget(heading)

            for line in lines:
                lbl = BodyLabel(line)
                lbl.setWordWrap(True)
                lbl.setObjectName("helpContentLabel")
                card_layout.addWidget(lbl)

            root_layout.addWidget(card)

        root_layout.addStretch()

        scroll.setWidget(root)
        scroll.enableTransparentBackground()
        layout.addWidget(scroll, 1)


