#!/bin/bash
set -e

# ── macOS Build Script for RCSW ──
# Usage: chmod +x build.sh && ./build.sh

APP_NAME="RCSW"
APP_VERSION="1.0.0"
ENTRY="main.py"
OUTDIR="dist"
ICON_PNG="rcsw/resources/icon.png"
ICON_ICNS="rcsw/resources/icon.icns"

echo ""
echo "========================================"
echo "  $APP_NAME macOS Build Script"
echo "========================================"
echo ""

# ── Step 1: Check Python ──
echo "[1/7] Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo "  ERROR: python3 not found"
    exit 1
fi
echo "  $(python3 --version)"

# ── Step 2: Venv ──
echo "[2/7] Preparing virtual environment..."
if [ -d ".venv" ]; then
    echo "  venv already exists"
else
    python3 -m venv .venv
    echo "  venv created"
fi
source .venv/bin/activate
echo "  venv activated"

# ── Step 3: Dependencies ──
echo "[3/7] Installing dependencies..."
pip install -r requirements.txt -q
pip install nuitka -q
echo "  done"

# ── Step 4: Generate icon.icns ──
echo "[4/7] Generating macOS icon..."
python3 -c "
import struct, io
from PIL import Image
from pathlib import Path

img = Image.open('$ICON_PNG').convert('RGBA')
entries = b''
for w, h, icon_type in [(256,256,b'ic08'), (128,128,b'ic07'), (64,64,b'ic12'), (32,32,b'ic11')]:
    resized = img.resize((w, h), Image.LANCZOS)
    buf = io.BytesIO()
    resized.save(buf, format='PNG')
    png_bytes = buf.getvalue()
    entries += icon_type + struct.pack('>I', 8 + len(png_bytes)) + png_bytes
data = b'icns' + struct.pack('>I', 8 + len(entries)) + entries
Path('$ICON_ICNS').write_bytes(data)
print(f'  icon.icns generated: {len(data)} bytes')
"
echo "  done"

# ── Step 5: Clean old dist ──
echo "[5/7] Cleaning old dist..."
rm -rf "$OUTDIR"
echo "  done"

# ── Step 6: Run tests ──
echo "[6/7] Running tests..."
python3 -m pytest tests/ -q || echo "  Tests failed, continuing..."
echo ""

# ── Step 7: Nuitka build ──
echo "[7/7] Building macOS .app bundle..."
python3 -m nuitka \
  --standalone \
  --macos-create-app-bundle \
  --macos-app-name="$APP_NAME" \
  --macos-app-version="$APP_VERSION" \
  --macos-app-icon="$ICON_ICNS" \
  --enable-plugin=pyside6 \
  --include-package=rcsw \
  --include-package-data=rcsw \
  --output-dir="$OUTDIR" \
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
  "$ENTRY"

echo ""
echo "========================================"
echo "  BUILD DONE"
echo "========================================"
echo "  Output: $OUTDIR/$APP_NAME.app"
echo ""

# Optionally skip these on pure CI
# open "$OUTDIR"
