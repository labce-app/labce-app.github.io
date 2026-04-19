@echo off
setlocal enabledelayedexpansion

REM ===== Aller dans le dossier du script (.bat) =====
cd /d "%~dp0"

REM ===== Nom du script principal =====
set "MAIN_PY=labCE_app.py"

REM ===== Proxy Zscaler =====
set "PROXY=http://gateway.schneider.zscaler.net:80"

echo [INFO] Dossier courant: %CD%
echo [INFO] Fichier principal: %MAIN_PY%
if not exist "%MAIN_PY%" (
    echo [ERREUR] Introuvable: "%MAIN_PY%"
    pause
    exit /b 1
)

REM ===== Activer le venv s'il existe =====
if exist "venv\Scripts\activate" (
    echo [INFO] Activation du venv...
    call "venv\Scripts\activate"
) else (
    echo [INFO] Aucun venv detecte. On continue avec l'environnement courant...
)

REM ===== Mettre a jour pip/outils de build =====
python -m pip install --proxy "%PROXY%" --upgrade pip setuptools wheel

REM ===== Installer dependances via proxy =====
python -m pip install --proxy "%PROXY%" scipy numpy matplotlib pillow openpyxl nidaqmx pyinstaller

REM ===== Nettoyage build precedent =====
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist labCE_app.spec del /f labCE_app.spec

REM ===== Build avec collectes pour matplotlib, scipy, numpy, nitypes =====
pyinstaller --onefile --windowed --icon="logo_labce.ico" --add-data "logo_labce.png;." --add-data "config.ini;." --collect-data matplotlib --collect-submodules matplotlib --collect-submodules scipy --collect-binaries numpy --collect-binaries scipy --collect-metadata nitypes "%MAIN_PY%"

echo.
if exist "dist" (
    echo [OK] Build termine. Exe dans: "%CD%\\dist"
    echo Pour tester: cd dist && labCE_app.exe
) else (
    echo [ATTENTION] Le dossier dist n'a pas ete cree. Regarde les erreurs ci-dessus.
)

pause
endlocal
