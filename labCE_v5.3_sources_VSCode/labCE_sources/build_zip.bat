@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

:: ============================================================
::  labCE v5.3 - Script de packaging ZIP all-in-one
::  Produit : labCE_v5.3_Package.zip pret a livrer
::
::  PREREQUIS AVANT D'UTILISER CE SCRIPT :
::    1. Placer ni-daqmx_XX.X_runtime.exe dans  .\NI-DAQmx\
::    2. S'assurer que le venv est actif (ou .venv present)
::    3. PyInstaller doit etre installe
:: ============================================================

set "APP_VERSION=v5.3"
set "PACKAGE_NAME=labCE_%APP_VERSION%_Package"
set "OUTPUT_ZIP=%~dp0%PACKAGE_NAME%.zip"
set "TEMP_DIR=%~dp0%PACKAGE_NAME%"

echo.
echo ============================================================
echo  labCE %APP_VERSION% - Build ZIP all-in-one
echo ============================================================
echo.

:: ============================================================
:: ETAPE 1 : Compiler l'exe avec PyInstaller
:: ============================================================
echo [1/4] Compilation de l'executable...

:: Detecter Python utilisable (venv d'abord, sinon systeme)
set "PYTHON_EXE=python"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" --version >nul 2>&1
    if not errorlevel 1 (
        set "PYTHON_EXE=.venv\Scripts\python.exe"
        echo [INFO] Utilisation du .venv
    ) else (
        echo [INFO] .venv present mais Python inaccessible, utilisation du Python systeme.
    )
) else if exist "venv\Scripts\python.exe" (
    "venv\Scripts\python.exe" --version >nul 2>&1
    if not errorlevel 1 (
        set "PYTHON_EXE=venv\Scripts\python.exe"
        echo [INFO] Utilisation du venv
    ) else (
        echo [INFO] venv present mais Python inaccessible, utilisation du Python systeme.
    )
) else (
    echo [INFO] Pas de venv detecte, utilisation de l'environnement Python systeme.
)

:: Verifier que PyInstaller est disponible
%PYTHON_EXE% -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo [INFO] PyInstaller absent, installation...
    %PYTHON_EXE% -m pip install pyinstaller
)

:: Nettoyer les anciens builds
if exist build rmdir /s /q build
if exist dist  rmdir /s /q dist

:: Build avec le .spec existant (contient toutes les options)
if exist "labCE_app.spec" (
    echo [INFO] Utilisation du fichier .spec existant...
    %PYTHON_EXE% -m PyInstaller labCE_app.spec
) else (
    echo [INFO] Pas de .spec trouve, build avec options directes...
    %PYTHON_EXE% -m PyInstaller --onefile --windowed ^
        --icon="Logo_LabCE.ico" ^
        --add-data "Logo_LabCE.png;." ^
        --add-data "config.ini;." ^
        --collect-data matplotlib ^
        --collect-submodules matplotlib ^
        --collect-submodules scipy ^
        --collect-binaries numpy ^
        --collect-binaries scipy ^
        --collect-metadata nitypes ^
        --collect-metadata nidaqmx ^
        --exclude-module torch ^
        --name labCE_app ^
        labCE_app.py
)

if not exist "dist\labCE_app.exe" (
    echo.
    echo [ERREUR] La compilation a echoue. labCE_app.exe introuvable dans dist\
    echo Verifie les erreurs PyInstaller ci-dessus.
    pause
    exit /b 1
)
echo [OK] Executable cree : dist\labCE_app.exe

:: ============================================================
:: ETAPE 2 : Construire l'arborescence du package
:: ============================================================
echo.
echo [2/4] Construction du package...

:: Nettoyer le dossier temporaire
if exist "%TEMP_DIR%" rmdir /s /q "%TEMP_DIR%"
mkdir "%TEMP_DIR%"
mkdir "%TEMP_DIR%\NI-DAQmx"

:: Fichiers principaux
copy /y "dist\labCE_app.exe"  "%TEMP_DIR%\labCE_app.exe"  >nul
copy /y "INSTALLER.bat"        "%TEMP_DIR%\INSTALLER.bat"   >nul
copy /y "install.ps1"          "%TEMP_DIR%\install.ps1"     >nul
copy /y "config.ini"           "%TEMP_DIR%\config.ini"      >nul

if exist "Logo_LabCE.ico" copy /y "Logo_LabCE.ico" "%TEMP_DIR%\Logo_LabCE.ico" >nul
if exist "Logo_LabCE.png" copy /y "Logo_LabCE.png" "%TEMP_DIR%\Logo_LabCE.png" >nul

:: Copier le runtime NI-DAQmx s'il est present dans .\NI-DAQmx\
set "NI_FOUND=0"
if exist "NI-DAQmx\*.exe" (
    echo [INFO] Runtime NI-DAQmx (.exe) detecte, inclusion dans le package...
    copy /y "NI-DAQmx\*.exe" "%TEMP_DIR%\NI-DAQmx\" >nul
    set "NI_FOUND=1"
)
if exist "NI-DAQmx\*.nipkg" (
    echo [INFO] Package NI-DAQmx (.nipkg) detecte, inclusion dans le package...
    copy /y "NI-DAQmx\*.nipkg" "%TEMP_DIR%\NI-DAQmx\" >nul
    set "NI_FOUND=1"
)
if "!NI_FOUND!"=="0" (
    echo [ATTENTION] Aucun installateur NI-DAQmx dans .\NI-DAQmx\
    echo            Le ZIP sera cree SANS le runtime NI.
    echo            Ajouter ni-daqmx_XX.X_runtime.exe ou .nipkg dans .\NI-DAQmx\ avant de zipper.
)

:: Fichier d'instructions pour le sous-dossier NI-DAQmx
(
echo ============================================================
echo  Dossier NI-DAQmx - Installateur du driver NI
echo ============================================================
echo.
echo Ce dossier doit contenir le fichier d'installation
echo NI-DAQmx Runtime fourni par votre referent technique.
echo.
echo Nom attendu : ni-daqmx_XX.X_runtime.exe
echo              ^(ou NI_DAQmx_XX.X.exe, setup.exe^)
echo.
echo IMPORTANT : NE PAS SUPPRIMER CE DOSSIER.
echo L'installateur INSTALLER.bat recherche le driver ici.
echo.
echo Si le dossier est vide, telechargez le runtime sur :
echo https://www.ni.com/fr-fr/support/downloads/drivers/download.ni-daq-mx.html
echo ^(Choisir "Runtime" uniquement - pas de compte NI requis^)
echo ============================================================
) > "%TEMP_DIR%\NI-DAQmx\LIRE_MOI.txt"

echo [OK] Arborescence creee dans : %TEMP_DIR%

:: ============================================================
:: ETAPE 3 : Creer le ZIP avec PowerShell
:: ============================================================
echo.
echo [3/4] Creation du ZIP...

if exist "%OUTPUT_ZIP%" del /f "%OUTPUT_ZIP%"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "Compress-Archive -Path '%TEMP_DIR%\*' -DestinationPath '%OUTPUT_ZIP%' -Force"

if not exist "%OUTPUT_ZIP%" (
    echo [ERREUR] La creation du ZIP a echoue.
    pause
    exit /b 1
)

:: Taille du ZIP
for %%A in ("%OUTPUT_ZIP%") do set "ZIP_SIZE=%%~zA"
set /a "ZIP_MB=!ZIP_SIZE! / 1048576"

echo [OK] ZIP cree : %OUTPUT_ZIP%  (!ZIP_MB! MB^)

:: ============================================================
:: ETAPE 4 : Nettoyage du dossier temporaire
:: ============================================================
echo.
echo [4/4] Nettoyage...
rmdir /s /q "%TEMP_DIR%"
echo [OK] Dossier temporaire supprime.

:: ============================================================
:: RECAPITULATIF
:: ============================================================
echo.
echo ============================================================
echo  Package pret a livrer :
echo  %OUTPUT_ZIP%
echo.
echo  Structure du ZIP :
echo    INSTALLER.bat          <- double-clic pour tout installer
echo    install.ps1            <- script d'installation
echo    labCE_app.exe          <- application
echo    config.ini             <- configuration initiale
echo    Logo_LabCE.ico/png     <- icones
echo    NI-DAQmx\
echo      LIRE_MOI.txt
echo      ni-daqmx_XX.X.exe   <- runtime NI (si present)
echo ============================================================
echo.
pause
endlocal
