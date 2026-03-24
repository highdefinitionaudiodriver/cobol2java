#!/bin/bash
echo "=========================================="
echo " COBOL to Java Migration Tool - Build    "
echo "=========================================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] python3 is not installed or not in PATH."
    echo "Please install Python 3.8+ from https://www.python.org/"
    exit 1
fi

# Install PyInstaller if needed
echo "[1/3] Checking PyInstaller..."
if ! python3 -m pip show pyinstaller > /dev/null 2>&1; then
    echo "Installing PyInstaller..."
    python3 -m pip install pyinstaller
fi

# Build binary
echo ""
echo "[2/3] Building executable..."
cd "$(dirname "$0")"

python3 -m PyInstaller \
    --name "COBOL2Java" \
    --onefile \
    --noconsole \
    --noconfirm \
    --clean \
    --distpath "/tmp/cobol2java_dist" \
    --workpath "/tmp/cobol2java_build" \
    --add-data "src:src" \
    --hidden-import "src" \
    --hidden-import "src.cobol_parser" \
    --hidden-import "src.oop_transformer" \
    --hidden-import "src.java_generator" \
    --hidden-import "src.i18n" \
    --hidden-import "src.vendor_extensions" \
    main.py

if [ $? -ne 0 ]; then
    echo ""
    echo "[ERROR] Build failed!"
    exit 1
fi

# Copy to local dist
echo ""
mkdir -p dist
cp "/tmp/cobol2java_dist/COBOL2Java" "dist/COBOL2Java"

echo ""
echo "[3/3] Build complete!"
echo ""
echo "Executable file: $(pwd)/dist/COBOL2Java"
echo ""
echo "You can distribute this single file."
echo "No Python installation required on target machine."
echo ""
