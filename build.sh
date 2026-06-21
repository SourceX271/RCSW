#!/bin/bash
set -e

python -m nuitka --mode=app \
  --lto=yes \
  --macos-app-icon=rcsw/resources/icon.icns \
  --enable-plugin=pyside6 \
  --include-package=rcsw \
  --include-package-data=rcsw \
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
