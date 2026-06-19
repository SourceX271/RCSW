from __future__ import annotations

import os

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QColor, QPainter, QFont
from PySide6.QtWidgets import (
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
    QHBoxLayout,
    QFileDialog,
    QStyledItemDelegate,
    QStyle,
    QLabel,
)
from qfluentwidgets import (
    BodyLabel,
    PrimaryPushButton,
    TransparentPushButton,
    ScrollArea,
    ProgressBar,
    InfoBar,
    InfoBarPosition,
)

import fitz
from ..core.logger import get_logger
from .style import ACCENT, PANEL_BG

_log = get_logger("file_panel")


class _FileItemDelegate(QStyledItemDelegate):

    def paint(self, painter: QPainter, option, index):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        is_selected = option.state & QStyle.StateFlag.State_Selected
        is_hovered = option.state & QStyle.StateFlag.State_MouseOver
        is_valid = index.data(Qt.ItemDataRole.UserRole + 3)
        if is_valid is None:
            is_valid = True

        r = option.rect
        if is_selected:
            painter.fillRect(r, QColor(ACCENT))
        elif is_hovered:
            painter.fillRect(r, QColor("#00000014"))
        elif index.row() % 2 == 0:
            painter.fillRect(r, QColor("#00000006"))
        else:
            painter.fillRect(r, QColor(0, 0, 0, 0))

        if not is_selected:
            sep_y = r.bottom() - 1
            painter.setPen(QColor("#0000000A"))
            painter.drawLine(r.left() + 12, sep_y, r.right() - 12, sep_y)

        fm = option.fontMetrics
        name = index.data(Qt.ItemDataRole.DisplayRole)
        pages = index.data(Qt.ItemDataRole.UserRole + 1)
        size_mb = index.data(Qt.ItemDataRole.UserRole + 2)

        icon_r = r.adjusted(8, 6, -8, -6)
        icon_x = icon_r.left()
        icon_y = icon_r.top() + (icon_r.height() - 32) // 2

        if is_valid:
            pdf_color = QColor("#E74C3C") if not is_selected else Qt.GlobalColor.white
        else:
            pdf_color = QColor("#777")
        painter.setPen(pdf_color)
        painter.setBrush(pdf_color)
        painter.drawRoundedRect(icon_x, icon_y, 28, 34, 3, 3)

        painter.setPen(Qt.GlobalColor.white if is_selected else Qt.GlobalColor.black)
        font = QFont("Segoe UI", 7, QFont.Weight.Bold)
        painter.setFont(font)
        label = "PDF" if is_valid else "!"
        painter.drawText(icon_x, icon_y + 12, 28, 20, Qt.AlignmentFlag.AlignCenter, label)

        name_color = Qt.GlobalColor.white if is_selected else QColor("#1A1A1A")
        if not is_valid and not is_selected:
            name_color = QColor("#999")
        painter.setPen(name_color)
        font = QFont("Segoe UI", 10, QFont.Weight.Medium)
        painter.setFont(font)
        name_x = icon_x + 40
        name_w = r.right() - name_x - 8
        name_elided = fm.elidedText(name, Qt.TextElideMode.ElideMiddle, name_w)
        painter.drawText(name_x, r.top() + 6, name_w, 18, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, name_elided)

        meta_color = QColor("#AAA") if is_selected else QColor("#888")
        if not is_valid and not is_selected:
            meta_color = QColor("#E74C3C")
        painter.setPen(meta_color)
        font = QFont("Segoe UI", 9)
        painter.setFont(font)
        if is_valid:
            meta = f"{pages if pages else '?'} 页  |  {size_mb if size_mb else '?'} MB"
        else:
            meta = "无法读取此文件"
        painter.drawText(name_x, r.top() + 24, name_w, 16, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, meta)

        painter.restore()

    def sizeHint(self, option, index):
        return QSize(200, 52)


class FilePanel(QWidget):

    process_requested = Signal()
    cancel_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("filePanel")
        self.setAcceptDrops(True)
        self._file_paths: dict[str, str] = {}
        self._processing = False
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        self.setStyleSheet(
            PANEL_BG
            + f'QWidget#filePanel[dragActive="true"] #fileListScroll {{'
            f"  border: 2px dashed {ACCENT};"
            "  border-radius: 6px;"
            "}"
        )

        title = BodyLabel("PDF 文件列表")
        title.setObjectName("panelTitle")
        layout.addWidget(title)

        hint = BodyLabel("点击下方按钮选择 PDF 文件，或拖拽文件到窗口")
        hint.setWordWrap(True)
        hint.setProperty("hint", True)
        layout.addWidget(hint)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self._add_btn = PrimaryPushButton("添加 PDF 文件")
        self._add_btn.clicked.connect(self._on_add_files)
        btn_row.addWidget(self._add_btn)

        self._remove_btn = TransparentPushButton("移除选中")
        self._remove_btn.clicked.connect(self._on_remove)
        self._remove_btn.setEnabled(False)
        btn_row.addWidget(self._remove_btn)

        self._clear_btn = TransparentPushButton("清空列表")
        self._clear_btn.clicked.connect(self._on_clear)
        self._clear_btn.setEnabled(False)
        btn_row.addWidget(self._clear_btn)

        btn_row.addStretch()
        self._count_label = BodyLabel("")
        self._count_label.setProperty("hint", True)
        btn_row.addWidget(self._count_label)

        layout.addLayout(btn_row)

        self._scroll = ScrollArea()
        self._scroll.setObjectName("fileListScroll")

        self._empty_label = QLabel()
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setWordWrap(True)
        self._empty_label.setText(
            '\n\n拖拽 PDF 文件到此处\n或点击上方按钮添加文件'
        )
        self._empty_label.setVisible(True)
        self._empty_label.setMinimumHeight(160)
        self._empty_label.setStyleSheet(
            "color: #888888;"
            "font-size: 15px;"
            "padding: 32px;"
            f"border: 2px dashed {ACCENT}44;"
            "border-radius: 8px;"
            "background: rgba(0,0,0,0.02);"
        )

        self._list = QListWidget()
        self._list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self._list.setItemDelegate(_FileItemDelegate())
        self._list.setSpacing(2)
        self._list.setStyleSheet(
            "QListWidget::item { padding: 0px; }"
        )

        scroll_container = QWidget()
        scroll_container.setAutoFillBackground(False)
        sc_layout = QVBoxLayout(scroll_container)
        sc_layout.setContentsMargins(0, 0, 0, 0)
        sc_layout.addWidget(self._empty_label)
        sc_layout.addWidget(self._list)

        self._scroll.setWidget(scroll_container)
        self._scroll.setWidgetResizable(True)
        layout.addWidget(self._scroll, 1)

        bottom_bar = QHBoxLayout()
        bottom_bar.setSpacing(8)

        self._status_label = BodyLabel("就绪")
        bottom_bar.addWidget(self._status_label)
        bottom_bar.addStretch()

        self._progress_bar = ProgressBar()
        self._progress_bar.setMinimumWidth(160)
        self._progress_bar.setVisible(False)
        bottom_bar.addWidget(self._progress_bar)

        self._cancel_btn = TransparentPushButton("取消")
        self._cancel_btn.clicked.connect(self._on_cancel)
        self._cancel_btn.setVisible(False)
        bottom_bar.addWidget(self._cancel_btn)

        self._process_btn = PrimaryPushButton("开始处理")
        self._process_btn.clicked.connect(self._on_start_process)
        bottom_bar.addWidget(self._process_btn)

        layout.addLayout(bottom_bar)

        self._refresh_empty_state()

    def _on_add_files(self):
        if self._processing:
            return
        paths, _ = QFileDialog.getOpenFileNames(
            self, "选择 PDF 文件", "", "PDF 文件 (*.pdf)"
        )
        if paths:
            self.add_files(paths)

    def _on_clear(self):
        if self._processing:
            return
        self._file_paths.clear()
        self._list.clear()
        self._update_buttons()
        self._refresh_empty_state()

    def _on_remove(self):
        if self._processing:
            return
        row = self._list.currentRow()
        if row < 0:
            return
        item = self._list.takeItem(row)
        fp = item.data(Qt.ItemDataRole.UserRole)
        if fp in self._file_paths:
            del self._file_paths[fp]
        self._update_buttons()
        self._refresh_empty_state()

    def _on_start_process(self):
        if self._processing:
            return
        if not self._file_paths:
            InfoBar.warning(
                title="提示",
                content="请先添加 PDF 文件",
                parent=self.window(),
                position=InfoBarPosition.TOP,
            )
            return
        self._processing = True
        self._process_btn.setVisible(False)
        self._cancel_btn.setVisible(True)
        self._progress_bar.setVisible(True)
        self._progress_bar.setValue(0)
        self._status_label.setText("处理中...")
        self._add_btn.setEnabled(False)
        self._remove_btn.setEnabled(False)
        self._clear_btn.setEnabled(False)
        self.process_requested.emit()

    def _on_cancel(self):
        if self._processing:
            self.cancel_requested.emit()

    def _refresh_empty_state(self):
        has_items = self._list.count() > 0
        self._empty_label.setVisible(not has_items)
        self._list.setVisible(has_items)
        self._update_count_label()

    def _update_count_label(self):
        n = self._list.count()
        if n > 0:
            total_pages = 0
            total_size = 0.0
            for i in range(n):
                item = self._list.item(i)
                pages_val = item.data(Qt.ItemDataRole.UserRole + 1)
                size_val = item.data(Qt.ItemDataRole.UserRole + 2)
                if pages_val and isinstance(pages_val, int):
                    total_pages += pages_val
                if size_val:
                    try:
                        total_size += float(size_val)
                    except (ValueError, TypeError):
                        pass
            self._count_label.setText(f"共 {n} 个文件  |  {total_pages} 页  |  {total_size:.1f} MB")
        else:
            self._count_label.setText("")

    def update_progress(self, current: int, total: int, filename: str):
        if total > 0:
            pct = int(current / total * 100)
            self._progress_bar.setValue(pct)
            self._status_label.setText(f"处理中... {current}/{total} 页 ({pct}%)")

    def update_status(self, text: str):
        self._status_label.setText(text)

    def set_processing(self, active: bool):
        self._processing = active
        self._process_btn.setVisible(not active)
        self._cancel_btn.setVisible(active)
        self._progress_bar.setVisible(active)
        self._add_btn.setEnabled(not active)
        self._remove_btn.setEnabled(not active and len(self._file_paths) > 0)
        self._clear_btn.setEnabled(not active and len(self._file_paths) > 0)
        if not active:
            self._status_label.setText("就绪")

    def _update_buttons(self):
        has_items = self._list.count() > 0
        if not self._processing:
            self._clear_btn.setEnabled(has_items)
            self._remove_btn.setEnabled(has_items)

    def add_files(self, paths: list[str]):
        invalid_paths = []
        for p in paths:
            p = os.path.abspath(p)
            if p in self._file_paths:
                continue
            if not os.path.isfile(p) or not p.lower().endswith(".pdf"):
                continue
            self._file_paths[p] = p
            valid = True
            try:
                doc = fitz.open(p)
                pages = doc.page_count
                size_mb = os.path.getsize(p) / (1024 * 1024)
                doc.close()
            except Exception:
                pages = 0
                size_mb = 0
                valid = False
                invalid_paths.append(os.path.basename(p))
                _log.warning("Invalid PDF: %s", p)
            name = os.path.basename(p)
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.DisplayRole, name)
            item.setData(Qt.ItemDataRole.UserRole, p)
            item.setData(Qt.ItemDataRole.UserRole + 1, pages)
            item.setData(Qt.ItemDataRole.UserRole + 2, f"{size_mb:.1f}")
            item.setData(Qt.ItemDataRole.UserRole + 3, valid)
            item.setSizeHint(QSize(200, 52))
            self._list.addItem(item)

        self._update_buttons()
        self._refresh_empty_state()

        if invalid_paths:
            names = "\n".join(invalid_paths[:3])
            if len(invalid_paths) > 3:
                names += f"\n... 等 {len(invalid_paths)} 个文件"
            InfoBar.warning(
                title="部分文件无法读取",
                content=names,
                parent=self.window(),
                position=InfoBarPosition.TOP,
                duration=5000,
            )

    def get_file_paths(self) -> list[str]:
        return list(self._file_paths.keys())

    def clear(self):
        self._on_clear()

    def changeEvent(self, event):
        if event.type() == event.Type.StyleChange and hasattr(self, '_list'):
            self._list.viewport().update()
        super().changeEvent(event)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setProperty("dragActive", True)
            self.style().unpolish(self)
            self.style().polish(self)

    def dragLeaveEvent(self, event):
        self.setProperty("dragActive", False)
        self.style().unpolish(self)
        self.style().polish(self)

    def dropEvent(self, event):
        self.setProperty("dragActive", False)
        self.style().unpolish(self)
        self.style().polish(self)
        paths = [
            url.toLocalFile()
            for url in event.mimeData().urls()
            if url.toLocalFile().lower().endswith(".pdf")
        ]
        if paths:
            self.add_files(paths)
