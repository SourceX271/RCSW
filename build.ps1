# Build script for RCSW
# Requires: icon.ico in rcsw/resources/ (generated from icon.svg)
python -m nuitka --standalone --windows-console-mode=disable `
  --windows-icon-from-ico=rcsw/resources/icon.ico `
  --enable-plugin=pyside6 `
  --include-package=rcsw `
  --output-dir=dist `
  main.py