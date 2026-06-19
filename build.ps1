python -m nuitka --standalone --windows-console-mode=disable `
  --enable-plugin=pyside6 `
  --include-package=rcsw `
  --output-dir=dist `
  --windows-icon-from-ico=rcsw/resources/icon.ico `
  main.py