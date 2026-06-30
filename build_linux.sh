#!/bin/bash
set -e

# RCSW Linux 构建脚本
# 使用 Nuitka 打包为独立 Linux 可执行文件
# 输出: dist/rcsw

python -m nuitka --standalone \
  --output-filename=rcsw \
  --company-name="SourceX271" \
  --product-name="RCSW" \
  --file-version="0.4.0" \
  --product-version="0.4.0" \
  --file-description="Remove CamScanner Watermark" \
  --copyright="GNU General Public License v3.0" \
  --lto=yes \
  --enable-plugin=pyside6 \
  --include-package=rcsw \
  --include-data-dir=rcsw/resources=rcsw/resources \
  --output-dir=dist \
  --noinclude-default-mode=nofollow \
  --noinclude-unittest-mode=nofollow \
  --noinclude-pytest-mode=nofollow \
  --noinclude-setuptools-mode=nofollow \
  --noinclude-IPython-mode=nofollow \
  --noinclude-pydoc-mode=nofollow \
  --noinclude-dask-mode=nofollow \
  --noinclude-numba-mode=nofollow \
  --nofollow-import-to=scipy \
  --nofollow-import-to=numpy \
  --nofollow-import-to=lxml \
  --nofollow-import-to=fontTools \
  --nofollow-import-to=matplotlib \
  --nofollow-import-to=pandas \
  --nofollow-import-to=cv2 \
  --nofollow-import-to=tkinter \
  --nofollow-import-to=PySide6.QtWebEngine \
  --nofollow-import-to=PySide6.QtWebEngineCore \
  --nofollow-import-to=PySide6.QtWebEngineWidgets \
  --nofollow-import-to=PySide6.QtWebEngineQuick \
  --nofollow-import-to=PySide6.Qt3DCore \
  --nofollow-import-to=PySide6.Qt3DAnimation \
  --nofollow-import-to=PySide6.Qt3DRender \
  --nofollow-import-to=PySide6.Qt3DInput \
  --nofollow-import-to=PySide6.Qt3DLogic \
  --nofollow-import-to=PySide6.Qt3DExtras \
  main.py
