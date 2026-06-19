#!/usr/bin/env bash
set -euo pipefail

python -m nuitka --standalone \
  --enable-plugin=pyside6 \
  --include-package=rcsw \
  --output-dir=dist \
  main.py

echo "Build complete. Output in dist/main.dist/"
