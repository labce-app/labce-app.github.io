# Architecture labCE

## Modules principaux

| Fichier | Rôle |
|---|---|
| `labCE_app.py` | GUI principale PyQt |
| `acquisition.py` | Capture NI-DAQmx + encodeurs |
| `data_manager.py` | Stockage & traitement des données |
| `export_excel.py` | Export vers Excel (openpyxl) |
| `plotting.py` | Graphiques matplotlib |
| `config.py` | Configuration |
| `translations.py` | Internationalisation |
| `mock_nidaqmx.py` | Simulation pour tests |

## Stack technique

- **GUI** : PyQt
- **Acquisition** : nidaqmx, numpy, scipy
- **Export** : openpyxl
- **Build** : PyInstaller → .exe
- **Distribution** : GitHub Releases + GitHub Pages
