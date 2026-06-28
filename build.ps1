<#
.SYNOPSIS
    RCSW Windows 构建脚本
.DESCRIPTION
    使用 Nuitka 将 RCSW 打包为独立 Windows 可执行文件。
    输出: dist/rcsw.exe
.NOTES
    作者: SourceX271
    项目: https://github.com/SourceX271/RCSW
    许可证: GNU General Public License v3.0
#>
uv run python -m nuitka --standalone --windows-console-mode=disable `
  --output-filename=rcsw.exe `
  --company-name="SourceX271" `
  --product-name="RCSW" `
  --file-version="0.4.0" `
  --product-version="0.4.0" `
  --file-description="Remove CamScanner Watermark" `
  --copyright="GNU General Public License v3.0" `
  --lto=yes `
  --enable-plugin=pyside6 `
  --include-package=rcsw `
  --include-package-data=rcsw `
  --output-dir=dist `
  --windows-icon-from-ico=rcsw/resources/icon.ico `
  --noinclude-default-mode=nofollow `
  --noinclude-unittest-mode=nofollow `
  --noinclude-pytest-mode=nofollow `
  --noinclude-setuptools-mode=nofollow `
  --noinclude-IPython-mode=nofollow `
  --noinclude-pydoc-mode=nofollow `
  --noinclude-dask-mode=nofollow `
  --noinclude-numba-mode=nofollow `
  --nofollow-import-to=scipy `
  --nofollow-import-to=numpy `
  --nofollow-import-to=lxml `
  --nofollow-import-to=fontTools `
  --nofollow-import-to=matplotlib `
  --nofollow-import-to=pandas `
  --nofollow-import-to=cv2 `
  --nofollow-import-to=tkinter `
  --nofollow-import-to=PySide6.QtWebEngine `
  --nofollow-import-to=PySide6.QtWebEngineCore `
  --nofollow-import-to=PySide6.QtWebEngineWidgets `
  --nofollow-import-to=PySide6.QtWebEngineQuick `
  --nofollow-import-to=PySide6.Qt3DCore `
  --nofollow-import-to=PySide6.Qt3DAnimation `
  --nofollow-import-to=PySide6.Qt3DRender `
  --nofollow-import-to=PySide6.Qt3DInput `
  --nofollow-import-to=PySide6.Qt3DLogic `
  --nofollow-import-to=PySide6.Qt3DExtras `
  main.py
