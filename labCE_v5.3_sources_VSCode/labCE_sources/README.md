# labCE — Déploiement multi-PC (NI-DAQmx)

Ce paquet contient l'application **labCE** (Tkinter + Matplotlib) pour l'acquisition via **NI-DAQmx** et un mécanisme de configuration par PC via `config.ini`.

## Contenu

- `labCE_app.py` — application principale
- `config.ini` — configuration par machine (device NI, canaux, sensibilités, etc.)
- `logo_labce.png` / `logo_labce.ico` — logos de l'application
- `requirements.txt` — dépendances Python
- `build_win.bat` — script de build Windows (PyInstaller)
- `build_posix.sh` — script de build Linux/Mac (PyInstaller)
- `Guide_installation_labCE.pdf` — guide d'installation

## Prérequis

- Driver **NI-DAQmx** et **NI MAX** installés sur chaque PC
- Carte NI reconnue dans NI MAX (nom du device ex.: `Dev1`)
- (Option 1) **Utiliser l'exécutable** généré (Windows) via PyInstaller
- (Option 2) **Utiliser Python** et installer les dépendances via `requirements.txt`

## Utilisation via exécutable (Windows)

1. Exécutez `build_win.bat` pour générer `dist/labCE.exe`.
2. Copiez `labCE.exe`, `config.ini`, `logo_labce.png`, `logo_labce.ico` ensemble.
3. Sur chaque PC, ajustez `config.ini` (nom du device, sensibilités, etc.).
4. Lancez `labCE.exe`.

## Utilisation via Python

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python labCE_app.py
```

## Fichier `config.ini`

- `NI.device` : nom tel qu'affiché dans NI MAX (ex. `Dev1`)
- `NI.has_ni` : `true/false` pour activer/désactiver l'utilisation NI (utile pour démo sans carte)
- `Channels.effort_ai` / `Channels.course_ai` : canaux analogiques pour Effort/Course
- `Sensors.sensitivity_*` : sensibilités capteurs
- `Acquisition.frequency_hz` : fréquence d'échantillonnage
- `UI.default_mode` / `UI.default_test_name` : paramètres visuels par défaut

## Build (PyInstaller)

### Windows

```bat
@echo off
set SCRIPT=labCE_app.py
set APPNAME=labCE
set ICON=logo_labce.ico

if not exist .venv (
    python -m venv .venv
)
call .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

pyinstaller ^
  --name %APPNAME% ^
  --windowed ^
  --icon %ICON% ^
  --add-data "logo_labce.png;." ^
  --add-data "logo_labce.ico;." ^
  --add-data "config.ini;." ^
  %SCRIPT%
```

### Linux / macOS

```bash
#!/usr/bin/env bash
set -e
SCRIPT=labCE_app.py
APPNAME=labCE

python3 -m venv .venv || true
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

pyinstaller   --name "$APPNAME"   --windowed   --add-data "logo_labce.png:."   --add-data "logo_labce.ico:."   --add-data "config.ini:."   "$SCRIPT"
```

## Notes

- L'application détecte automatiquement le dossier d'exécution PyInstaller via `sys._MEIPASS` pour retrouver les logos et `config.ini`.
- Si `NI.has_ni=false`, l'appli démarre en mode "NI indisponible" (utile pour démonstrations sans carte).

## Support

Consultez le PDF `Guide_installation_labCE.pdf` et vérifiez NI MAX si la carte n'apparaît pas.
