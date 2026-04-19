"""
Gestionnaire de données avec protection thread-safe, limite mémoire et CSV continu
labCE v5.0
"""
import threading
import numpy as np
import logging
import csv
import os
from datetime import datetime
from config import AcquisitionConfig


class ContinuousCSVWriter:
    """Écrit les données en continu dans un fichier CSV pendant l'acquisition."""

    def __init__(self, directory, test_name):
        """
        Args:
            directory: Dossier de sauvegarde
            test_name: Nom de l'essai
        """
        self._lock = threading.Lock()
        self._file = None
        self._writer = None
        self._sample_count = 0
        self._flush_counter = 0
        self.filepath = None

        if not directory or not os.path.isdir(directory):
            logging.warning("CSV continu : dossier invalide, écriture désactivée")
            return

        date_str = datetime.now().strftime("%d-%m-%Y")
        filename = f"{date_str}_{test_name}_live.csv"
        self.filepath = os.path.join(directory, filename)

        try:
            self._file = open(self.filepath, 'w', newline='', encoding='utf-8')
            self._writer = csv.writer(self._file, delimiter=';')
            self._writer.writerow([
                "Temps (s)", "Course (mm)", "Effort (N)",
                "Tension Effort (V)", "Tension Course (V)"
            ])
            self._file.flush()
            logging.info(f"CSV continu ouvert : {self.filepath}")
        except Exception as e:
            logging.error(f"Impossible d'ouvrir le CSV continu : {e}")
            self._file = None
            self._writer = None

    def write_sample(self, time_val, course, effort, raw_effort, raw_course):
        """Écrit un échantillon dans le CSV."""
        if self._writer is None:
            return
        with self._lock:
            try:
                self._writer.writerow([
                    f"{time_val:.4f}", f"{course:.4f}", f"{effort:.4f}",
                    f"{raw_effort:.6f}", f"{raw_course:.6f}"
                ])
                self._flush_counter += 1
                self._sample_count += 1
                # Flush périodique (tous les 50 échantillons)
                if self._flush_counter >= 50:
                    self._file.flush()
                    self._flush_counter = 0
            except Exception as e:
                logging.error(f"Erreur écriture CSV : {e}")

    def close(self):
        """Ferme le fichier CSV."""
        with self._lock:
            if self._file:
                try:
                    self._file.flush()
                    self._file.close()
                    logging.info(
                        f"CSV continu fermé : {self._sample_count} échantillons écrits"
                    )
                except Exception as e:
                    logging.error(f"Erreur fermeture CSV : {e}")
                finally:
                    self._file = None
                    self._writer = None

    @property
    def is_active(self):
        return self._writer is not None


class DataManager:
    """
    Gestionnaire thread-safe pour les données d'acquisition.
    Implémente une limite de mémoire pour éviter les fuites.
    """

    def __init__(self, max_samples=AcquisitionConfig.MAX_SAMPLES):
        self.max_samples = max_samples
        self._lock = threading.Lock()

        # Données principales
        self._time = []
        self._effort = []
        self._course = []
        self._raw_effort = []
        self._raw_course = []

        # Courbes additionnelles et points
        self._additional_curves = {}
        self._points = []

        # Courbes lissées (stockées séparément pour ne pas modifier les données brutes)
        self._smoothed_curves = {}

        # CSV continu
        self._csv_writer = None

        logging.info(f"DataManager initialisé avec limite de {max_samples} échantillons")

    # =================== CSV CONTINU ===================

    def start_csv_writer(self, directory, test_name):
        """Démarre l'écriture CSV continue."""
        self._csv_writer = ContinuousCSVWriter(directory, test_name)
        return self._csv_writer.is_active

    def stop_csv_writer(self):
        """Arrête l'écriture CSV continue."""
        if self._csv_writer:
            self._csv_writer.close()
            self._csv_writer = None

    def get_csv_filepath(self):
        """Retourne le chemin du CSV en cours."""
        if self._csv_writer and self._csv_writer.filepath:
            return self._csv_writer.filepath
        return None

    # =================== DONNÉES PRINCIPALES ===================

    def add_sample(self, time_val, effort, course, raw_effort, raw_course):
        """Ajoute un échantillon de manière thread-safe."""
        with self._lock:
            if len(self._time) >= self.max_samples:
                remove_count = self.max_samples // 10
                self._time = self._time[remove_count:]
                self._effort = self._effort[remove_count:]
                self._course = self._course[remove_count:]
                self._raw_effort = self._raw_effort[remove_count:]
                self._raw_course = self._raw_course[remove_count:]
                logging.warning(f"Limite mémoire atteinte. {remove_count} échantillons supprimés.")

            self._time.append(time_val)
            self._effort.append(effort)
            self._course.append(course)
            self._raw_effort.append(raw_effort)
            self._raw_course.append(raw_course)

        # Écriture CSV (hors du lock principal pour éviter les deadlocks)
        if self._csv_writer and self._csv_writer.is_active:
            self._csv_writer.write_sample(time_val, course, effort, raw_effort, raw_course)

    def get_data_copy(self):
        """Retourne une copie thread-safe de toutes les données."""
        with self._lock:
            return {
                'time': self._time.copy(),
                'effort': self._effort.copy(),
                'course': self._course.copy(),
                'raw_effort': self._raw_effort.copy(),
                'raw_course': self._raw_course.copy(),
                'additional_curves': {k: v.copy() for k, v in self._additional_curves.items()},
                'points': [p.copy() for p in self._points],
                'smoothed_curves': {k: v.copy() for k, v in self._smoothed_curves.items()},
            }

    def get_latest_values(self):
        """Retourne les dernières valeurs."""
        with self._lock:
            if not self._time:
                return None
            return (
                self._time[-1], self._effort[-1], self._course[-1],
                self._raw_effort[-1], self._raw_course[-1]
            )

    def archive_main_as_curve(self, name, color):
        """
        Archive la courbe principale comme courbe additionnelle.
        Permet de la conserver pour comparaison après Nouvelle mesure.
        """
        with self._lock:
            if not self._time or not self._effort:
                return False
            curve_data = {
                'time': self._time.copy(),
                'effort': self._effort.copy(),
                'course': self._course.copy(),
                'color': color,
            }
            self._additional_curves[name] = curve_data
            logging.info(f"Courbe principale archivée sous '{name}'")
            return True

    def clear_main_data(self):
        """Efface les données principales."""
        with self._lock:
            self._time.clear()
            self._effort.clear()
            self._course.clear()
            self._raw_effort.clear()
            self._raw_course.clear()
            self._smoothed_curves.pop("main", None)
            logging.info("Données principales effacées")

    def set_data_from_file(self, time_data, effort, course, raw_effort, raw_course):
        """Définit les données à partir d'un fichier chargé."""
        with self._lock:
            self._time = list(time_data)[:self.max_samples]
            self._effort = list(effort)[:self.max_samples]
            self._course = list(course)[:self.max_samples]
            self._raw_effort = list(raw_effort)[:self.max_samples]
            self._raw_course = list(raw_course)[:self.max_samples]
            if len(time_data) > self.max_samples:
                logging.warning(f"Fichier tronqué à {self.max_samples} échantillons")

    # =================== COURBES ADDITIONNELLES ===================

    def add_curve(self, name, data, color):
        """Ajoute une courbe supplémentaire."""
        with self._lock:
            curve_data = data.copy()
            curve_data['color'] = color
            self._additional_curves[name] = curve_data
            logging.info(f"Courbe '{name}' ajoutée")

    def remove_curve(self, name):
        """Supprime une courbe par son nom."""
        with self._lock:
            if name in self._additional_curves:
                del self._additional_curves[name]
                self._smoothed_curves.pop(name, None)
                logging.info(f"Courbe '{name}' supprimée")
                return True
            return False

    def update_curve_color(self, name, color):
        """Met à jour la couleur d'une courbe."""
        with self._lock:
            if name in self._additional_curves:
                self._additional_curves[name]['color'] = color
                return True
            return False

    def clear_curves(self):
        """Efface toutes les courbes additionnelles."""
        with self._lock:
            self._additional_curves.clear()
            # Garder uniquement le lissage de la courbe principale
            main_smooth = self._smoothed_curves.get("main")
            self._smoothed_curves.clear()
            if main_smooth:
                self._smoothed_curves["main"] = main_smooth
            logging.info("Courbes additionnelles effacées")

    def get_curve_names(self):
        """Retourne la liste des noms de courbes."""
        with self._lock:
            return list(self._additional_curves.keys())

    # =================== POINTS ===================

    def add_point(self, x, y, point_type="course", curve_name=None, color=None, name=None, mode=None):
        """Ajoute un point avec métadonnées."""
        with self._lock:
            point_data = {
                'x': x,
                'y': y,
                'type': point_type,
                'curve': curve_name,
                'color': color,
                'name': name or f"P{len(self._points) + 1}",
                'mode': mode,
            }
            self._points.append(point_data)

    def remove_point(self, index):
        """Supprime un point par son index."""
        with self._lock:
            if 0 <= index < len(self._points):
                del self._points[index]
                return True
            return False

    def update_point_color(self, index, color):
        """Met à jour la couleur d'un point."""
        with self._lock:
            if 0 <= index < len(self._points):
                self._points[index]['color'] = color
                return True
            return False

    def clear_points(self):
        """Efface tous les points."""
        with self._lock:
            self._points.clear()
            logging.info("Points effacés")

    def get_points(self):
        """Retourne une copie des points."""
        with self._lock:
            return [p.copy() for p in self._points]

    # =================== LISSAGE ===================

    def _find_optimal_degree(self, x, y, max_degree=15):
        """
        Trouve le degré polynomial optimal par validation croisée BIC.
        Compromis entre fidélité au signal et sur-ajustement.
        Retourne un degré entre 2 et max_degree.
        """
        n = len(x)
        if n < 5:
            return 2
        max_degree = min(max_degree, n - 2)  # pas plus de n-2
        best_degree = 2
        best_bic = np.inf
        for d in range(2, max_degree + 1):
            try:
                coeffs = np.polyfit(x, y, d)
                y_fit = np.polyval(coeffs, x)
                residuals = y - y_fit
                sse = np.sum(residuals ** 2)
                # BIC = n*ln(SSE/n) + k*ln(n), k = d+1 paramètres
                if sse <= 0:
                    bic = -np.inf
                else:
                    bic = n * np.log(sse / n) + (d + 1) * np.log(n)
                if bic < best_bic:
                    best_bic = bic
                    best_degree = d
            except (np.linalg.LinAlgError, ValueError):
                continue
        return best_degree

    def smooth_curve(self, curve_name, poly_degree=None, smooth_color=None):
        """
        Applique un lissage par régression polynomiale (moindres carrés).
        Le degré est déterminé automatiquement si non fourni (BIC optimal).

        Args:
            curve_name: "main" pour la courbe principale, ou nom d'une courbe
            poly_degree: Degré du polynôme (auto si None)
            smooth_color: Couleur de la courbe lissée

        Returns:
            tuple or None: (nom_courbe, degré_utilisé) ou None si échec
        """
        with self._lock:
            try:
                if curve_name == "main":
                    if not self._effort or not self._course:
                        return None
                    course_arr = np.array(self._course, dtype=float)
                    effort_arr = np.array(self._effort, dtype=float)
                    time_arr = np.array(self._time, dtype=float)
                    idx = np.argsort(course_arr)
                    c_sorted = course_arr[idx]
                    e_sorted = effort_arr[idx]
                    if poly_degree is None:
                        poly_degree = self._find_optimal_degree(c_sorted, e_sorted)
                    coeffs = np.polyfit(c_sorted, e_sorted, poly_degree)
                    e_fit = np.polyval(coeffs, c_sorted)
                    smooth_name = f"Lissé (deg={poly_degree})"
                    self._additional_curves[smooth_name] = {
                        'time': list(time_arr),
                        'effort': list(e_fit),
                        'course': list(c_sorted),
                        'color': smooth_color or '#17A2B8',
                    }
                else:
                    if curve_name not in self._additional_curves:
                        return None
                    crv = self._additional_curves[curve_name]
                    if 'course' not in crv or 'effort' not in crv:
                        return None
                    c_arr = np.array(crv['course'], dtype=float)
                    e_arr = np.array(crv['effort'], dtype=float)
                    idx = np.argsort(c_arr)
                    c_sorted = c_arr[idx]
                    e_sorted = e_arr[idx]
                    if poly_degree is None:
                        poly_degree = self._find_optimal_degree(c_sorted, e_sorted)
                    coeffs = np.polyfit(c_sorted, e_sorted, poly_degree)
                    e_fit = np.polyval(coeffs, c_sorted)
                    smooth_name = f"{curve_name} lissé (deg={poly_degree})"
                    smooth_data = {
                        'course': list(c_sorted),
                        'effort': list(e_fit),
                        'color': smooth_color or '#17A2B8',
                    }
                    if 'time' in crv:
                        smooth_data['time'] = list(np.array(crv['time'])[idx])
                    self._additional_curves[smooth_name] = smooth_data

                logging.info(f"Courbe lissée '{smooth_name}' créée (degré auto={poly_degree})")
                return (smooth_name, poly_degree)
            except Exception as e:
                logging.error(f"Erreur lissage : {e}")
                return None

    def remove_smoothing(self, curve_name):
        """Supprime les courbes lissées associées à une courbe."""
        with self._lock:
            to_remove = [k for k in self._additional_curves
                         if k.startswith(f"{curve_name} lissé") or
                            (curve_name == "main" and k.startswith("Lissé ("))]
            for k in to_remove:
                del self._additional_curves[k]
                logging.info(f"Courbe lissée '{k}' supprimée")
            return len(to_remove) > 0

    @staticmethod
    def _moving_average(data, window_size):
        """Calcule la moyenne glissante."""
        if window_size <= 1 or len(data) < window_size:
            return list(data)
        arr = np.array(data, dtype=float)
        kernel = np.ones(window_size) / window_size
        smoothed = np.convolve(arr, kernel, mode='valid')
        return list(smoothed)

    # =================== OFFSET ===================

    def detect_initial_offset(self, n_samples=20):
        """
        Calcule l'offset initial (moyenne des n premiers échantillons).
        Retourne {'effort': float, 'course': float} ou None si pas assez de données.
        """
        with self._lock:
            if len(self._effort) < n_samples:
                return None
            effort_offset = float(np.mean(self._effort[:n_samples]))
            course_offset = float(np.mean(self._course[:n_samples]))
        return {'effort': effort_offset, 'course': course_offset}

    def apply_offset(self, effort_offset=0.0, course_offset=0.0):
        """Soustrait un offset de toutes les données effort et/ou course."""
        with self._lock:
            if effort_offset != 0.0:
                self._effort = [e - effort_offset for e in self._effort]
                for name, crv in self._additional_curves.items():
                    if 'effort' in crv:
                        crv['effort'] = [e - effort_offset for e in crv['effort']]
            if course_offset != 0.0:
                self._course = [c - course_offset for c in self._course]
                for name, crv in self._additional_curves.items():
                    if 'course' in crv:
                        crv['course'] = [c - course_offset for c in crv['course']]
        logging.info(f"Offset appliqué — Effort: {effort_offset:+.4f} N, Course: {course_offset:+.4f} mm")

    # =================== STATISTIQUES ===================

    def get_statistics(self):
        """Calcule les statistiques sur les données."""
        with self._lock:
            if not self._effort:
                return None
            return {
                'effort': {
                    'min': float(np.min(self._effort)),
                    'max': float(np.max(self._effort)),
                    'mean': float(np.mean(self._effort)),
                    'std': float(np.std(self._effort))
                },
                'course': {
                    'min': float(np.min(self._course)),
                    'max': float(np.max(self._course)),
                    'mean': float(np.mean(self._course)),
                    'std': float(np.std(self._course))
                }
            }

    def get_sample_count(self):
        """Retourne le nombre d'échantillons."""
        with self._lock:
            return len(self._time)

    @property
    def is_empty(self):
        """Vérifie si les données sont vides."""
        with self._lock:
            return len(self._time) == 0


def interpolate_data(x_list, y_list, x_value):
    """
    Interpolation linéaire O(log n) via np.searchsorted.
    Prend la PREMIÈRE occurrence si le point apparaît plusieurs fois.
    """
    if not x_list or not y_list or len(x_list) != len(y_list):
        return None

    try:
        x_arr = np.array(x_list, dtype=float)
        y_arr = np.array(y_list, dtype=float)

        if x_value < x_arr[0] or x_value > x_arr[-1]:
            return None  # Hors limites

        idx = int(np.searchsorted(x_arr, x_value, side='left'))

        if idx == 0:
            return float(y_arr[0])
        if idx >= len(x_arr):
            return float(y_arr[-1])

        x1, x2 = x_arr[idx - 1], x_arr[idx]
        y1, y2 = y_arr[idx - 1], y_arr[idx]

        if x1 == x2:
            return float(y1)

        t = (x_value - x1) / (x2 - x1)
        return float(y1 + t * (y2 - y1))

    except Exception as e:
        logging.error(f"Erreur interpolation: {e}")
        return None
        return None