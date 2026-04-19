"""
Gestionnaire de graphiques optimisé - Style LabVIEW
labCE v5.3
"""
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import tkinter as tk
from tkinter import messagebox
import logging, time, os
from config import THEME, FONTS, SUBPLOT_PARAMS


def configure_matplotlib_style():
    """Configure le style matplotlib global - Style LabVIEW."""
    plt.rcParams.update({
        "figure.facecolor": THEME["panel"],
        "axes.facecolor": "#FAFAFA",
        "axes.edgecolor": "#333333",
        "axes.labelcolor": THEME["text"],
        "axes.titlecolor": THEME["text"],
        "axes.titlesize": 14,
        "axes.titleweight": "bold",
        "axes.titlepad": 20,
        "axes.linewidth": 1.2,
        "xtick.color": "#333333", "ytick.color": "#333333",
        "xtick.direction": "in", "ytick.direction": "in",
        "xtick.major.size": 7, "ytick.major.size": 7,
        "xtick.minor.size": 4, "ytick.minor.size": 4,
        "xtick.major.width": 1.2, "ytick.major.width": 1.2,
        "xtick.minor.width": 0.6, "ytick.minor.width": 0.6,
        "xtick.top": True, "xtick.bottom": True,
        "ytick.left": True, "ytick.right": True,
        "xtick.minor.visible": True, "ytick.minor.visible": True,
        "grid.color": "#CCCCCC", "grid.linestyle": "-",
        "grid.linewidth": 0.8, "grid.alpha": 0.7,
        "font.family": "Segoe UI", "font.size": 10,
        "lines.linewidth": 2,
        "figure.autolayout": False,
        "legend.framealpha": 0.95, "legend.facecolor": "#FFFFFF",
        "legend.edgecolor": "#999999",
        "axes.labelsize": 12, "axes.labelweight": "semibold",
        "axes.labelpad": 12,
        "figure.constrained_layout.use": False,
    })


class PlotManager:
    """Gestionnaire de graphiques avec quadrillage style LabVIEW."""

    def __init__(self, ax):
        self.ax = ax
        self._line_main = None
        self.clear()

    def clear(self):
        self.ax.clear()
        self._line_main = None
        self.ax.set_facecolor("#FAFAFA")
        self.ax.grid(True, which='major', linestyle='-', linewidth=0.8, alpha=0.7, color='#CCCCCC')
        self.ax.minorticks_on()
        self.ax.grid(True, which='minor', linestyle='-', linewidth=0.3, alpha=0.4, color='#DDDDDD')
        self.ax.xaxis.set_minor_locator(AutoMinorLocator(5))
        self.ax.yaxis.set_minor_locator(AutoMinorLocator(5))
        for spine in self.ax.spines.values():
            spine.set_edgecolor('#333333'); spine.set_linewidth(1.2)
        self.ax.xaxis.set_ticks_position('both'); self.ax.yaxis.set_ticks_position('both')
        self.ax.tick_params(which='major', direction='in', length=7, width=1.2, colors='#333333', top=True, right=True)
        self.ax.tick_params(which='minor', direction='in', length=4, width=0.6, colors='#666666', top=True, right=True)

    def set_labels(self, xlabel, ylabel, title):
        self.ax.set_xlabel(xlabel, fontsize=12, labelpad=14)
        self.ax.set_ylabel(ylabel, fontsize=12, labelpad=14)
        self.ax.set_title(title, fontsize=13, fontweight="bold", pad=15)

    def update_main_data(self, x, y, label, color=None):
        if color is None: color = THEME["primary"]
        if self._line_main is None:
            self._line_main, = self.ax.plot(x, y, color=color, linewidth=2.5, label=label, zorder=2, alpha=0.9)
        else:
            self._line_main.set_data(x, y); self._line_main.set_color(color)
        self.ax.relim(); self.ax.autoscale_view()

    def plot_main_curve(self, x, y, label, color=None):
        if color is None: color = THEME["primary"]
        return self.ax.plot(x, y, color=color, linewidth=2.5, label=label, zorder=2, alpha=0.9)

    def plot_smoothed_curve(self, x, y, label, color=None):
        if color is None: color = "#FF6600"
        return self.ax.plot(x, y, color=color, linewidth=3.0, label=label, zorder=3, alpha=0.6, linestyle='-')

    def draw_additional_curves(self, curves, mode, smoothed_curves=None):
        for name, crv in curves.items():
            color = crv.get("color", THEME["primary"])
            if mode == "sensor" and "time" in crv and "effort" in crv:
                self.ax.plot(crv["time"], crv["effort"], label=name, color=color)
            elif mode == "bench" and "time" in crv and "course" in crv:
                self.ax.plot(crv["time"], crv["course"], label=name, color=color)
            elif "course" in crv and "effort" in crv:
                self.ax.plot(crv["course"], crv["effort"], label=name, color=color)
            if smoothed_curves and name in smoothed_curves:
                sm = smoothed_curves[name]
                if mode == "sensor" and "time" in sm and "effort" in sm:
                    self.plot_smoothed_curve(sm["time"], sm["effort"], f"{name} (lissé)", color=color)
                elif mode == "bench" and "time" in sm and "course" in sm:
                    self.plot_smoothed_curve(sm["time"], sm["course"], f"{name} (lissé)", color=color)
                elif "course" in sm and "effort" in sm:
                    self.plot_smoothed_curve(sm["course"], sm["effort"], f"{name} (lissé)", color=color)

    def draw_points(self, points):
        for point in points:
            x, y = point['x'], point['y']
            pt = point.get('type', 'course')
            color = point.get('color', THEME["secondary"])
            name = point.get('name', '')
            marker = 'o' if pt == 'course' else '^'
            size = 80 if pt == 'course' else 100
            self.ax.scatter(x, y, s=size, color=color, marker=marker, edgecolor='white', linewidth=1.5, zorder=5)
            self.ax.axvline(x, color=color, linestyle="--", alpha=0.6, linewidth=1.2, zorder=4)
            self.ax.axhline(y, color=color, linestyle="--", alpha=0.6, linewidth=1.2, zorder=4)
            if name:
                self.ax.annotate(name, (x, y), textcoords="offset points", xytext=(8, 8),
                    fontsize=8, color=color, fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor=color, alpha=0.8))

    def finalize(self):
        handles, labels = self.ax.get_legend_handles_labels()
        if handles:
            self.ax.legend(loc="upper right", framealpha=0.95, fontsize=9, fancybox=True, shadow=False)
        fig = self.ax.figure
        fig.set_constrained_layout(False)
        fig.subplots_adjust(**SUBPLOT_PARAMS)


class CustomToolbar(NavigationToolbar2Tk):
    """Barre d'outils matplotlib personnalisée — forcée visible."""

    def __init__(self, canvas, window, app_ref):
        super().__init__(canvas, window)
        self.app = app_ref
        # Forcer visibilité : fond contrasté
        self.configure(bg="#E8E8E8")
        for child in self.winfo_children():
            try: child.configure(bg="#E8E8E8")
            except: pass

    def save_figure(self, *args):
        try:
            save_dir = getattr(self.app, "save_directory", "")
            if save_dir and os.path.isdir(save_dir):
                timestamp = time.strftime("%H-%M-%S")
                filename = f"{self.app.full_test_name()}_figure_{timestamp}.png"
                path = os.path.join(save_dir, filename)
                self.canvas.figure.savefig(path, dpi=150, bbox_inches="tight")
                messagebox.showinfo("Export réussi", f"Figure sauvegardée :\n{path}")
            else:
                messagebox.showwarning("Export", "Choisissez d'abord un dossier de sauvegarde.")
        except Exception as e:
            logging.error(f"Erreur sauvegarde figure: {e}")
            messagebox.showerror("Erreur", str(e))