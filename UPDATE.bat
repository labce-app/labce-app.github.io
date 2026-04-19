@echo off
:: ============================================================
::  labCE - Mise à jour de l'application
::  Placez ce fichier à côté du nouveau labCE_app.exe
::  puis double-cliquez dessus.
:: ============================================================
cd /d "%~dp0"

set "EXE_NAME=labCE_app.exe"
set "INSTALL_DIR=%LOCALAPPDATA%\labCE"

echo.
echo  labCE - Mise a jour...
echo.

:: Vérifier que le nouveau exe est présent
if not exist "%~dp0%EXE_NAME%" (
    echo  [ERREUR] %EXE_NAME% introuvable dans ce dossier.
    echo  Placez le nouveau labCE_app.exe a cote de ce fichier UPDATE.bat
    pause
    exit /b 1
)

:: Vérifier que l'application est installée
if not exist "%INSTALL_DIR%\%EXE_NAME%" (
    echo  [ERREUR] labCE ne semble pas installe sur ce PC.
    echo  Utilisez INSTALLER.bat pour une premiere installation.
    pause
    exit /b 1
)

:: Fermer l'application si elle tourne
taskkill /f /im "%EXE_NAME%" >nul 2>&1
timeout /t 1 /nobreak >nul

:: Copier le nouvel exe
copy /y "%~dp0%EXE_NAME%" "%INSTALL_DIR%\%EXE_NAME%" >nul

if %ERRORLEVEL% EQU 0 (
    echo  [OK] labCE mis a jour avec succes.
    echo  Lancez l'application depuis le raccourci sur le bureau.
) else (
    echo  [ERREUR] La copie a echoue. L'application est peut-etre encore ouverte.
)

echo.
pause
