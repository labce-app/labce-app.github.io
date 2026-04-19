"""
Configuration centralisée pour labCE v5.3
"""
import os, sys, configparser, logging

SOFTWARE_VERSION = "v5.3"
AUTHOR = "Kuhlich Arsène"

# Encodeur ASM PMIS3-20-1-50KHZ-HTL-Z1-2M-S
ENCODER_CONFIG = {
    "name": "ASM PMIS3-20-1-50KHZ-HTL-Z1-2M-S",
    "decoding": "X4",
    "counter": "ctr0",
    "pfi_a": "PFI8",
    "pfi_b": "PFI9",
    "pfi_z": "PFI10",
    "sync_source": "ai/SampleClock",
    "distance_per_step": 1.0,
}

# Valeurs fixes du système
FIXED_EFFORT_SENSITIVITY = 1.0      # N/V
FIXED_COURSE_SENSITIVITY = 0.01     # mm/pas (éditable par utilisateur)
FIXED_FREQUENCY = 50                # Hz
FIXED_EFFORT_CHANNEL = "ai0"
FIXED_COURSE_CHANNEL = "ctr0"
KISTLER_POPUP_THRESHOLD_N = 10

BASE_DIR = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))

THEME = {
    "bg": "#F8F9FA", "panel": "#FFFFFF", "text": "#212529", "text_light": "#6C757D",
    "primary": "#0D6EFD", "secondary": "#FD7E14", "success": "#198754",
    "danger": "#DC3545", "warning": "#FFC107", "info": "#0DCAF0",
    "border": "#DEE2E6", "grid": "#E9ECEF", "disabled": "#ADB5BD",
    "highlight": "#0B5ED7", "acquisition_active": "#00E676",
    "guide_banner": "#FFF3CD", "guide_banner_text": "#856404",
    "preconfig_pending": "#DC3545",
    "preconfig_applied": "#198754",
}
FONTS = {
    "title": ("Segoe UI", 14, "bold"), "label": ("Segoe UI", 10),
    "button": ("Segoe UI", 10, "bold"), "data": ("Consolas", 9),
    "debug": ("Courier New", 10), "small": ("Segoe UI", 8),
    "tooltip": ("Segoe UI", 9),
}
SUBPLOT_PARAMS = {
    "left": 0.071, "bottom": 0.173, "right": 0.883,
    "top": 0.929, "wspace": 0.197, "hspace": 0.2,
}

class AcquisitionConfig:
    MAX_SAMPLES = 100000; AUTOSAVE_INTERVAL = 30; PLOT_UPDATE_INTERVAL = 0.1
    MIN_FREQUENCY = 1; MAX_FREQUENCY = 100; SAMPLES_PER_READ_DIVISOR = 2

KISTLER_RANGES = {
    "push": [
        {"label": "0 → 5 N", "max": 5, "sensitivity_pCN": -104.6},
        {"label": "0 → 10 N", "max": 10, "sensitivity_pCN": -104.5},
        {"label": "0 → 50 N", "max": 50, "sensitivity_pCN": -104.3},
        {"label": "0 → 500 N", "max": 500, "sensitivity_pCN": -104.5},
    ],
    "pull": [
        {"label": "0 → -50 N", "max": -50, "sensitivity_pCN": -104.6},
        {"label": "0 → -500 N", "max": -500, "sensitivity_pCN": -104.6},
    ],
}
GUIDE_SEQUENCES = {
    1: ["btn_refresh", "btn_test_conn", "btn_apply_preconfig", "btn_tare", "btn_start", "btn_stop", "btn_choose_dir", "btn_export"],
    2: ["btn_refresh", "btn_test_conn", "btn_apply_preconfig", "btn_tare", "btn_start", "btn_stop", "btn_point_course", "btn_choose_dir", "btn_export"],
    3: ["btn_refresh", "btn_test_conn", "btn_apply_preconfig", "btn_tare", "btn_start", "btn_stop", "btn_new_measure", "btn_start", "btn_stop", "btn_choose_dir", "btn_export"],
    4: ["btn_refresh", "btn_test_conn", "btn_apply_preconfig", "btn_tare", "btn_start", "btn_stop", "btn_point_course", "btn_new_measure", "btn_start", "btn_stop", "btn_point_course", "btn_choose_dir", "btn_export"],
    5: ["btn_refresh", "btn_test_conn", "btn_apply_preconfig", "btn_tare", "btn_start", "btn_stop", "btn_add_curve", "btn_choose_dir", "btn_export"],
    6: ["btn_refresh", "btn_test_conn", "btn_apply_preconfig", "btn_tare", "btn_start", "btn_stop", "btn_add_curve", "btn_point_course", "btn_choose_dir", "btn_export"],
}
COLOR_PALETTE = [
    "#0D6EFD", "#DC3545", "#198754", "#FD7E14", "#6610f2", "#20c997",
    "#6f42c1", "#d63384", "#0dcaf0", "#ffc107", "#495057", "#e83e8c",
]

def load_config_file(path="config.ini"):
    cfg = configparser.ConfigParser()
    d = {'device': '', 'effort_channel': FIXED_EFFORT_CHANNEL,
         'course_channel': FIXED_COURSE_CHANNEL,
         'frequency': str(FIXED_FREQUENCY),
         'sensitivity_effort': str(FIXED_EFFORT_SENSITIVITY),
         'sensitivity_course': str(FIXED_COURSE_SENSITIVITY),
         'default_mode': 'full',
         'save_directory': ''}
    if not os.path.isfile(path): return d
    try:
        cfg.read(path, encoding='utf-8')
        d['device'] = cfg.get('NI', 'device', fallback='')
        d['sensitivity_course'] = cfg.get('Sensors', 'sensitivity_course_mm_pas',
                                          fallback=str(FIXED_COURSE_SENSITIVITY))
        d['default_mode'] = cfg.get('UI', 'default_mode', fallback='full')
        d['save_directory'] = cfg.get('UI', 'save_directory', fallback='')
    except Exception as e: logging.error(f"Erreur config.ini: {e}")
    return d

def save_config_file(path, device='', sensitivity_course=None, default_mode='full', save_directory=''):
    """Persiste les paramètres utilisateur dans config.ini."""
    cfg = configparser.ConfigParser()
    if os.path.isfile(path):
        cfg.read(path, encoding='utf-8')
    if not cfg.has_section('NI'): cfg.add_section('NI')
    if not cfg.has_section('Sensors'): cfg.add_section('Sensors')
    if not cfg.has_section('UI'): cfg.add_section('UI')
    cfg.set('NI', 'device', device)
    cfg.set('Sensors', 'sensitivity_course_mm_pas',
            str(sensitivity_course) if sensitivity_course is not None else str(FIXED_COURSE_SENSITIVITY))
    cfg.set('UI', 'default_mode', default_mode)
    cfg.set('UI', 'save_directory', save_directory)
    try:
        with open(path, 'w', encoding='utf-8') as f:
            cfg.write(f)
    except Exception as e:
        logging.error(f"Erreur écriture config.ini: {e}")

def configure_logging():
    # Chemin du log : à côté de l'exe (PyInstaller) ou dans BASE_DIR (développement)
    log_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else BASE_DIR
    log_path = os.path.join(log_dir, 'labce.log')
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_path, encoding='utf-8'),
            logging.StreamHandler()
        ])