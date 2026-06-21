from __future__ import annotations

import sys
import os

from rcsw.app import main
from rcsw.silent import run_silent, MiniProgressWindow, parse_file_args

if __name__ == "__main__":
    pdfs = parse_file_args(sys.argv)
    if pdfs:
        from rcsw.core.config import Config
        cfg = Config.instance()
        mode = cfg.get("silentMode", "mini")

        if mode == "headless":
            run_silent(pdfs, mode="headless")
        else:
            from PySide6.QtWidgets import QApplication
            app = QApplication(sys.argv)
            app.setStyle("Fusion")
            from qfluentwidgets import setTheme, Theme
            theme_val = cfg.get("theme", Theme.LIGHT.value)
            try:
                theme = Theme(theme_val)
            except (ValueError, TypeError):
                theme = Theme.LIGHT
            setTheme(theme)

            win = MiniProgressWindow()
            win.show()

            def on_progress(current, total, filename):
                win.update_file(filename)
                win.update_page(current, total)

            def on_finished(success, errors):
                win.show_done(len(success), len(errors))

            from PySide6.QtCore import QThread, QTimer

            class SilentThread(QThread):
                done = False
                def run(self):
                    run_silent(pdfs, mode="headless",
                              on_progress=on_progress,
                              on_finished=on_finished,
                              check_cancel=lambda: win.is_cancelled)

            thread = SilentThread()
            win.cancelled.connect(thread.terminate)
            thread.start()

            app.exec()
            thread.wait(3000)

        sys.exit(0)
    else:
        main()
