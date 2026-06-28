from __future__ import annotations

import sys

from rcsw.app import main
from rcsw.silent import run_silent, parse_file_args

if __name__ == "__main__":
    pdfs = parse_file_args(sys.argv)
    if pdfs:
        from PySide6.QtCore import Qt, QThread, QTimer
        from PySide6.QtWidgets import QApplication, QSystemTrayIcon
        from PySide6.QtGui import QIcon
        from qfluentwidgets import setTheme, Theme
        from rcsw.core.config import Config

        app = QApplication(sys.argv)
        if sys.platform == "win32":
            app.setAttribute(Qt.ApplicationAttribute.AA_DontCreateNativeWidgetSiblings)

        cfg = Config.instance()
        theme_val = cfg.get("theme", Theme.LIGHT.value)
        try:
            theme = Theme(theme_val)
        except (ValueError, TypeError):
            theme = Theme.LIGHT
        setTheme(theme)

        icon = QIcon()
        pixmap = icon.pixmap(32, 32)
        if pixmap.isNull():
            from PySide6.QtGui import QPixmap, QPainter, QColor
            px = QPixmap(32, 32)
            px.fill(Qt.GlobalColor.transparent)
            painter = QPainter(px)
            painter.setBrush(QColor("#0078D4"))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(2, 2, 28, 28, 6, 6)
            painter.setPen(Qt.GlobalColor.white)
            painter.setFont(app.font())
            painter.drawText(px.rect(), Qt.AlignmentFlag.AlignCenter, "R")
            painter.end()
            icon = QIcon(px)

        tray = QSystemTrayIcon(icon)
        if QSystemTrayIcon.isSystemTrayAvailable():
            tray.show()
            tray.setToolTip("RCSW - 处理中...")
            tray.showMessage(
                "RCSW", f"开始处理 {len(pdfs)} 个文件...",
                QSystemTrayIcon.MessageIcon.Information, 3000,
            )

        worker_done = [False]

        def on_finished(success, errors):
            worker_done[0] = True
            if tray.supportsMessages():
                if errors:
                    tray.showMessage(
                        "RCSW",
                        f"处理完成: 成功 {len(success)}, 失败 {len(errors)}",
                        QSystemTrayIcon.MessageIcon.Warning, 5000,
                    )
                else:
                    tray.showMessage(
                        "RCSW",
                        f"处理完成: {len(success)} 个文件",
                        QSystemTrayIcon.MessageIcon.Information, 5000,
                    )

        class Worker(QThread):
            def run(self):
                run_silent(pdfs, on_finished=on_finished)

        worker = Worker()
        worker.start()

        def check_done():
            if worker_done[0]:
                QTimer.singleShot(3000, app.quit)
            else:
                QTimer.singleShot(500, check_done)

        QTimer.singleShot(500, check_done)
        app.exec()
        worker.wait(3000)
        tray.hide()
        sys.exit(0)
    else:
        main()
