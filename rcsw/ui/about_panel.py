from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QFont
from PySide6.QtWidgets import (
    QVBoxLayout,
    QWidget,
    QLabel,
)
from qfluentwidgets import (
    StrongBodyLabel,
    BodyLabel,
    ScrollArea,
    HyperlinkButton,
)

from .. import __version__
from .style import PANEL_BG, TransparentCard


class AboutPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("aboutPanel")
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet(PANEL_BG)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)

        title = StrongBodyLabel("关于")
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

        header_card = TransparentCard()
        hl = QVBoxLayout(header_card)
        hl.setContentsMargins(16, 20, 16, 20)
        hl.setSpacing(8)

        icon_lbl = QLabel()
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setFixedSize(64, 64)
        icon_lbl.setScaledContents(True)
        icon_path = Path(__file__).resolve().parent.parent / "resources" / "icon.svg"
        if icon_path.exists():
            icon_lbl.setPixmap(QPixmap(str(icon_path)))
        hl.addWidget(icon_lbl, 0, Qt.AlignmentFlag.AlignCenter)

        name_lbl = StrongBodyLabel("RCSW")
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = name_lbl.font()
        font.setPointSize(16)
        name_lbl.setFont(font)
        hl.addWidget(name_lbl)

        full_lbl = BodyLabel("Remove CamScanner Watermark")
        full_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hl.addWidget(full_lbl)

        ver_lbl = BodyLabel(f"版本 {__version__}")
        ver_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hl.addWidget(ver_lbl)

        root_layout.addWidget(header_card)

        info_card = TransparentCard()
        il = QVBoxLayout(info_card)
        il.setContentsMargins(16, 12, 16, 16)
        il.setSpacing(6)

        il.addWidget(StrongBodyLabel("简介"))
        il.addWidget(self._text(
            "RCSW 是一款专门用于去除「扫描全能王」PDF 水印的桌面工具。"
            "与其他通用去水印软件不同，RCSW 针对扫描全能王的特定水印格式进行了优化，"
            "能够精准识别并去除右下角的小尺寸水印图标，同时保持扫描图片的原始内容完整。"
        ))

        il.addWidget(StrongBodyLabel("技术栈"))
        il.addWidget(self._text(
            "Python 3 + PySide6 + PySide6-Fluent-Widgets + PyMuPDF + Pillow"
        ))

        il.addWidget(StrongBodyLabel("许可证"))
        il.addWidget(self._text("GNU General Public License v3.0"))

        il.addWidget(StrongBodyLabel("作者"))
        il.addWidget(HyperlinkButton(
            "mailto:860256006@qq.com",
            "860256006@qq.com",
        ))
        il.addWidget(HyperlinkButton(
            "mailto:liyichen314@outlook.com",
            "liyichen314@outlook.com",
        ))

        root_layout.addWidget(info_card)

        link_card = TransparentCard()
        ll = QVBoxLayout(link_card)
        ll.setContentsMargins(16, 12, 16, 16)
        ll.setSpacing(6)
        ll.addWidget(StrongBodyLabel("项目地址"))
        gh_link = HyperlinkButton(
            "https://github.com/SourceX271/RCSW",
            "https://github.com/SourceX271/RCSW",
        )
        ll.addWidget(gh_link)
        root_layout.addWidget(link_card)

        root_layout.addStretch()

        scroll.setWidget(root)
        scroll.enableTransparentBackground()
        layout.addWidget(scroll, 1)

    @staticmethod
    def _text(content: str) -> BodyLabel:
        lbl = BodyLabel(content)
        lbl.setWordWrap(True)
        font = lbl.font()
        font.setPointSize(10)
        lbl.setFont(font)
        return lbl
