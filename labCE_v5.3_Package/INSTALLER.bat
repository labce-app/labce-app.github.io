@echo off
:: ============================================================
::  labCE v5.3 - Lanceur d'installation
::  Double-cliquez sur ce fichier pour tout installer.
:: ============================================================
cd /d "%~dp0"

echo.
echo  labCE v5.3 - Demarrage de l'installation...
echo  (Une fenetre administrateur va s'ouvrir)
echo.

:: Lancer install.ps1 avec bypass de politique d'execution
:: Le script se charge lui-meme de l'elevation admin
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo  [ERREUR] L'installation a echoue (code %ERRORLEVEL%).
    echo  Verifiez que le dossier NI-DAQmx contient l'installateur.
    echo.
    pause
)
