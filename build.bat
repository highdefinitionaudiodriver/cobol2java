@echo off
echo ==========================================
echo  COBOL to Java Migration Tool - Build
echo ==========================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.8+ from https://www.python.org/
    pause
    exit /b 1
)

:: Install PyInstaller if needed
echo [1/3] Checking PyInstaller...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

:: Build EXE
echo.
echo [2/3] Building EXE...
cd /d "%~dp0"

python -m PyInstaller ^
    --name "COBOL2Java" ^
    --onefile ^
    --windowed ^
    --noconfirm ^
    --clean ^
    --distpath "%TEMP%\cobol2java_dist" ^
    --workpath "%TEMP%\cobol2java_build" ^
    --add-data "src;src" ^
    --hidden-import "src" ^
    --hidden-import "src.cobol_parser" ^
    --hidden-import "src.oop_transformer" ^
    --hidden-import "src.java_generator" ^
    --hidden-import "src.i18n" ^
    --hidden-import "src.vendor_extensions" ^
    main.py

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed!
    pause
    exit /b 1
)

:: Copy to local dist
echo.
if not exist "dist" mkdir dist
copy "%TEMP%\cobol2java_dist\COBOL2Java.exe" "dist\COBOL2Java.exe" /Y

echo.
echo [3/3] Build complete!
echo.
echo EXE file: %~dp0dist\COBOL2Java.exe
echo.
echo You can distribute this single EXE file.
echo No Python installation required on target machine.
echo.
pause
