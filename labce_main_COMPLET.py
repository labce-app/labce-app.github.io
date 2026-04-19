"""
labCE v5.3 - Application principale
Auteur: Kuhlich Arsène | 2026
"""
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, simpledialog, colorchooser
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import logging, time, os, sys, subprocess
from datetime import datetime
from PIL import Image, ImageTk
import numpy as np, openpyxl
from config import (THEME, FONTS, SOFTWARE_VERSION, AUTHOR, BASE_DIR, COLOR_PALETTE,
    AcquisitionConfig, load_config_file, save_config_file, configure_logging, SUBPLOT_PARAMS,
    KISTLER_RANGES, ENCODER_CONFIG, KISTLER_POPUP_THRESHOLD_N,
    FIXED_EFFORT_SENSITIVITY, FIXED_COURSE_SENSITIVITY, FIXED_FREQUENCY,
    FIXED_EFFORT_CHANNEL, FIXED_COURSE_CHANNEL)
from data_manager import DataManager, interpolate_data
from acquisition import NIDeviceManager, AcquisitionThread
from plotting import PlotManager, CustomToolbar, configure_matplotlib_style
from export_excel import export_complete
from translations import TRANSLATIONS
from labce_core import (ToolTip, modern_card, InteractiveGuide,
    show_welcome_window, show_splash_then_start)
configure_logging(); configure_matplotlib_style()


class BancEssaiApp:
    def __init__(self, root):
        self.root = root; self.lang = "fr"
        self.root.title(self.t("app_title")); self.root.state('zoomed')
        self.root.configure(bg=THEME["bg"])
        self.ICO = os.path.join(BASE_DIR, "logo_labce.ico")
        self.PNG = os.path.join(BASE_DIR, "logo_labce.png")
        self._icon_img = self._icon_small = None
        self.has_ni_flag = NIDeviceManager.is_available()
        self.set_window_icon(self.root)
        self.data_manager = DataManager(max_samples=AcquisitionConfig.MAX_SAMPLES)
        self.is_connected = self.is_acquiring = False
        self.preconfig_applied = False
        self.start_time = self.offset_effort = self.offset_course = 0.0
        self.save_directory = ""
        self.acquisition_thread = None
        self.crosshair_line_x = self.crosshair_line_y = None
        self.curve_color = THEME["primary"]
        now = datetime.now()
        self.date_str_display = now.strftime("%d/%m/%Y")
        self.date_str_file = now.strftime("%d-%m-%Y")
        self.mode_key = tk.StringVar(value="full")
        self.mode_display = tk.StringVar(value=self.t("mode_full"))
        self.test_name_user = tk.StringVar(value="Essai_01")
        self._tooltips = []; self._tut_blink_id = None
        self.guide = InteractiveGuide(self)
        # Fixed params
        self.sensitivity_effort = FIXED_EFFORT_SENSITIVITY
        self.sensitivity_course = tk.DoubleVar(value=FIXED_COURSE_SENSITIVITY)
        self.frequency = FIXED_FREQUENCY
        self.create_ui(); self.create_graph(); self.load_initial_config()
        if not self.has_ni_flag:
            self.label_status.config(text=self.t("status_ni_unavailable"), fg=THEME["warning"])
        self.update_ui_texts(); self.refresh_devices(); self._start_tut_blink()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        """Sauvegarde la config puis ferme proprement."""
        if self.acquisition_thread and self.acquisition_thread.is_running():
            self.acquisition_thread.stop()
        self._save_config()
        self.root.destroy()

    def t(self, k): return TRANSLATIONS.get(self.lang, TRANSLATIONS["fr"]).get(k, k)
    def add_tooltip(self, w, k): self._tooltips.append(ToolTip(w, lambda kk=k: self.t(kk)))

    def set_window_icon(self, w):
        try:
            if os.name == "nt" and os.path.isfile(self.ICO): w.iconbitmap(self.ICO)
            elif os.path.isfile(self.PNG):
                if not self._icon_img: self._icon_img = tk.PhotoImage(file=self.PNG)
                w.iconphoto(True, self._icon_img)
        except: pass

    def get_small_logo(self, sz=(120, 120)):
        if self._icon_small: return self._icon_small
        try:
            if os.path.isfile(self.PNG):
                img = Image.open(self.PNG)
                if img.mode not in ("RGB", "RGBA"): img = img.convert("RGBA")
                img.thumbnail(sz, Image.Resampling.LANCZOS)
                self._icon_small = ImageTk.PhotoImage(img); return self._icon_small
        except: pass
        return None

    def full_test_title(self): return f"{self.date_str_display}_{self.test_name_user.get()}"
    def full_test_name(self): return f"{self.date_str_file}_{self.test_name_user.get()}"
    def get_graph_title(self):
        m, t = self.mode_key.get(), self.full_test_title()
        if m == "sensor": return self.t("plot_title_effort_time").format(title=t)
        elif m == "bench": return self.t("plot_title_course_time").format(title=t)
        return self.t("plot_title_effort_course").format(title=t)

    def load_initial_config(self):
        c = load_config_file(os.path.join(BASE_DIR, 'config.ini'))
        self.device_var.set(c['device'])
        try: self.sensitivity_course.set(float(c['sensitivity_course']))
        except: pass
        mm = {"full": "full", "sensor": "sensor", "bench": "bench",
              "Essai complet": "full", "Test Capteur": "sensor", "Test Banc": "bench"}
        self.mode_key.set(mm.get(c['default_mode'], "full"))
        # Restaurer le dossier de sauvegarde
        saved_dir = c.get('save_directory', '')
        if saved_dir and os.path.isdir(saved_dir):
            self.save_directory = saved_dir
            self.label_path.config(text=f"📂 {saved_dir}", fg=THEME["text"])

    def _save_config(self):
        """Persiste les paramètres dans config.ini à la fermeture."""
        try:
            save_config_file(
                os.path.join(BASE_DIR, 'config.ini'),
                device=self.device_var.get(),
                sensitivity_course=self.sensitivity_course.get(),
                default_mode=self.mode_key.get(),
                save_directory=self.save_directory,
            )
        except Exception as e:
            logging.error(f"Erreur sauvegarde config: {e}")

    # =================== UI ===================
    def create_ui(self):
        mf = tk.Frame(self.root, bg=THEME["bg"]); mf.pack(fill="both", expand=True)
        mf.grid_rowconfigure(1, weight=1); mf.grid_columnconfigure(0, weight=0, minsize=380)
        mf.grid_columnconfigure(1, weight=1); self.main_frame = mf
        # === TOP BAR ===
        top = tk.Frame(mf, bg=THEME["bg"], pady=6)
        top.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10)
        top.grid_columnconfigure(7, weight=1)
        tk.Label(top, text="📝", bg=THEME["bg"], fg=THEME["primary"], font=("Segoe UI", 11)).grid(row=0, column=0, padx=(0, 3))
        tk.Entry(top, textvariable=self.test_name_user, width=20, bg=THEME["panel"], fg=THEME["text"], relief="groove", bd=1, font=("Segoe UI", 10)).grid(row=0, column=1, padx=3)
        self.test_name_user.trace_add('write', lambda *a: self.refresh_plot_title_only())
        tk.Label(top, text="📊", bg=THEME["bg"], fg=THEME["primary"], font=("Segoe UI", 11)).grid(row=0, column=2, padx=(10, 3))
        self.optionmenu = tk.OptionMenu(top, self.mode_display, self.t("mode_full"), self.t("mode_sensor"), self.t("mode_bench"), command=self._on_mode_select)
        self.optionmenu.config(bg=THEME["panel"], fg=THEME["text"], activebackground=THEME["highlight"], font=("Segoe UI", 10), bd=1, relief="groove", width=13)
        self.optionmenu.grid(row=0, column=3, padx=3)
        self.btn_lang = tk.Button(top, text=self.t("lang_button"), command=self.toggle_language, bg=THEME["info"], fg="white", font=("Segoe UI", 10), relief="groove", bd=1, width=5, cursor="hand2")
        self.btn_lang.grid(row=0, column=4, padx=3); self.add_tooltip(self.btn_lang, "tooltip_lang")
        self.btn_tutorials = tk.Button(top, text="📖 " + self.t("tutorials_button"), command=self.show_tutorials, bg="#FF6B00", fg="white", font=("Segoe UI", 10, "bold"), relief="groove", bd=2, cursor="hand2")
        self.btn_tutorials.grid(row=0, column=5, padx=3); self.add_tooltip(self.btn_tutorials, "tooltip_tutorials")
        self.btn_help = tk.Button(top, text="❓ " + self.t("help_button"), command=self.show_help, bg=THEME["info"], fg="white", font=("Segoe UI", 10), relief="groove", bd=1, cursor="hand2")
        self.btn_help.grid(row=0, column=6, padx=3); self.add_tooltip(self.btn_help, "tooltip_help")
        self.timer_label = tk.Label(top, text="⏱ 0.0 s", bg=THEME["bg"], fg=THEME["success"], font=("Segoe UI", 13, "bold"))
        self.timer_label.grid(row=0, column=7, sticky="e", padx=15)
        # === LEFT PANEL (scrollable) ===
        lc = tk.Frame(mf, bg=THEME["bg"], width=380); lc.grid(row=1, column=0, sticky="nsew", padx=(10, 0), pady=5); lc.grid_propagate(False)
        self.ctrl_canvas = tk.Canvas(lc, bg=THEME["bg"], highlightthickness=0)
        lsb = tk.Scrollbar(lc, orient="vertical", command=self.ctrl_canvas.yview)
        self.controls_frame = tk.Frame(self.ctrl_canvas, bg=THEME["bg"])
        self.controls_frame.bind("<Configure>", lambda e: self.ctrl_canvas.configure(scrollregion=self.ctrl_canvas.bbox("all")))
        self.ctrl_canvas.create_window((0, 0), window=self.controls_frame, anchor="nw", tags="ci")
        self.ctrl_canvas.configure(yscrollcommand=lsb.set)
        self.ctrl_canvas.bind("<Configure>", lambda e: self.ctrl_canvas.itemconfig("ci", width=e.width))
        self.ctrl_canvas.pack(side="left", fill="both", expand=True); lsb.pack(side="right", fill="y")
        def _mw(e):
            try:
                lx, lw = lc.winfo_rootx(), lc.winfo_width()
                if lx <= e.x_root <= lx + lw: self.ctrl_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"); return "break"
            except: pass
        self.root.bind_all("<MouseWheel>", _mw)
        self._build_right_panel(mf)
        cf = self.controls_frame

        # ===== CARD 1: CONNEXION (simplifié) =====
        self.conn_card = modern_card(cf, "🔌 " + self.t("conn_title")); self.conn_card.pack(fill="x", pady=(0, 5), padx=5)
        ci = tk.Frame(self.conn_card, bg=THEME["panel"]); ci.pack(fill="x", padx=5, pady=5)
        cl = tk.Frame(ci, bg=THEME["panel"]); cl.pack(fill="x")
        tk.Label(cl, text=self.t("device_label"), bg=THEME["panel"], fg=THEME["text"], font=("Segoe UI", 9)).pack(side="left")
        self.device_var = tk.StringVar()
        self.device_combobox = ttk.Combobox(cl, textvariable=self.device_var, width=11, font=("Segoe UI", 9)); self.device_combobox.pack(side="left", padx=(5, 2))
        self.btn_refresh = tk.Button(cl, text="🔄", command=self.refresh_devices, bg=THEME["info"], fg="white", font=("Segoe UI", 8), relief="groove", bd=1, width=2, cursor="hand2"); self.btn_refresh.pack(side="left", padx=1); self.add_tooltip(self.btn_refresh, "tooltip_refresh")
        self.btn_test_conn = tk.Button(cl, text=self.t("btn_test"), command=self.test_connexion, bg=THEME["success"], fg="white", font=("Segoe UI", 9, "bold"), relief="groove", bd=1, cursor="hand2"); self.btn_test_conn.pack(side="left", padx=2, fill="x", expand=True); self.add_tooltip(self.btn_test_conn, "tooltip_test_conn")
        stxt = self.t("status_ni_unavailable") if not self.has_ni_flag else self.t("status_not_connected")
        self.label_status = tk.Label(ci, text=stxt, fg=THEME["danger"] if not self.has_ni_flag else THEME["warning"], bg=THEME["panel"], font=("Segoe UI", 8, "bold")); self.label_status.pack(anchor="w", pady=(4, 0))

        # ===== CARD 2: PARAMÈTRES (Pré-configuration simplifiée) =====
        self.param_card = modern_card(cf, "⚙️ " + self.t("params_title")); self.param_card.pack(fill="x", pady=5, padx=5)
        pi = tk.Frame(self.param_card, bg=THEME["panel"]); pi.pack(fill="x", padx=5, pady=5)
        self.preconfig_frame = tk.LabelFrame(pi, text=self.t("preconfig_title"), bg=THEME["panel"], fg=THEME["preconfig_pending"], font=("Segoe UI", 9, "bold"), bd=2, highlightbackground=THEME["preconfig_pending"], highlightcolor=THEME["preconfig_pending"], highlightthickness=2)
        self.preconfig_frame.pack(fill="x", pady=(0, 5))
        # Plage de mesure
        rf = tk.Frame(self.preconfig_frame, bg=THEME["panel"]); rf.pack(fill="x", padx=5, pady=2)
        tk.Label(rf, text=self.t("range_label"), bg=THEME["panel"], fg=THEME["text"], font=FONTS["small"]).pack(anchor="w")
        ar = [f"⬆ {r['label']} ({r['sensitivity_pCN']} pC/N)" for r in KISTLER_RANGES["push"]]
        ar += [f"⬇ {r['label']} ({r['sensitivity_pCN']} pC/N)" for r in KISTLER_RANGES["pull"]]
        self.range_combo = ttk.Combobox(rf, values=ar, width=35, font=FONTS["small"], state="readonly"); self.range_combo.set(ar[0]); self.range_combo.pack(fill="x", pady=2)
        self.range_combo.bind("<<ComboboxSelected>>", self._on_range_selected)
        # Sensibilité course éditable
        scf = tk.Frame(self.preconfig_frame, bg=THEME["panel"]); scf.pack(fill="x", padx=5, pady=2)
        tk.Label(scf, text=self.t("sens_course_label"), bg=THEME["panel"], fg=THEME["text"], font=FONTS["small"]).pack(side="left")
        self.course_sens_entry = tk.Entry(scf, textvariable=self.sensitivity_course, width=8, font=FONTS["small"], relief="groove", bd=1)
        self.course_sens_entry.pack(side="left", padx=3)
        tk.Label(scf, text="mm/pas", bg=THEME["panel"], fg=THEME["text_light"], font=FONTS["small"]).pack(side="left")
        # Info button
        tk.Button(scf, text="ℹ", command=self._show_preconfig_info, bg=THEME["panel"], fg=THEME["info"], font=("Segoe UI", 8, "bold"), relief="flat", cursor="hand2", width=2).pack(side="right", padx=2)
        # Résumé fixe
        sumf = tk.Frame(self.preconfig_frame, bg=THEME["panel"]); sumf.pack(fill="x", padx=5, pady=2)
        tk.Label(sumf, text=f"Effort : {FIXED_EFFORT_SENSITIVITY} N/V  |  Fréquence : {FIXED_FREQUENCY} Hz  |  Canal : {FIXED_COURSE_CHANNEL}", bg=THEME["panel"], fg=THEME["text_light"], font=("Segoe UI", 7, "italic")).pack(anchor="w")
        # Bouton Appliquer
        self.btn_apply_preconfig = tk.Button(self.preconfig_frame, text="✅ " + self.t("apply_preconfig"), command=self.apply_preconfig, bg=THEME["preconfig_pending"], fg="white", font=FONTS["small"], relief="groove", bd=2, cursor="hand2")
        self.btn_apply_preconfig.pack(fill="x", padx=5, pady=(2, 5)); self.add_tooltip(self.btn_apply_preconfig, "tooltip_preconfig")

        # ===== CARD 3: ACQUISITION =====
        self.acq_card = modern_card(cf, "🎬 " + self.t("acq_title")); self.acq_card.pack(fill="x", pady=5, padx=5)
        ai = tk.Frame(self.acq_card, bg=THEME["panel"]); ai.pack(fill="x", padx=5, pady=5)
        self.btn_tare = tk.Button(ai, text="🔄 " + self.t("btn_tare"), command=self.tare, bg=THEME["warning"], fg="white", relief="groove", bd=2, font=("Segoe UI", 10, "bold"), cursor="hand2"); self.btn_tare.pack(fill="x", pady=2); self.add_tooltip(self.btn_tare, "tooltip_tare")
        sf = tk.Frame(ai, bg=THEME["panel"]); sf.pack(fill="x", pady=2)
        self.btn_start = tk.Button(sf, text="▶ " + self.t("btn_start"), command=self.start, bg=THEME["success"], fg="white", relief="groove", bd=2, font=("Segoe UI", 10, "bold"), cursor="hand2"); self.btn_start.pack(side="left", fill="x", expand=True); self.add_tooltip(self.btn_start, "tooltip_start")
        self.btn_stop = tk.Button(ai, text="⏹ " + self.t("btn_stop"), command=self.stop, bg=THEME["danger"], fg="white", relief="groove", bd=2, font=("Segoe UI", 10, "bold"), cursor="hand2"); self.btn_stop.pack(fill="x", pady=2); self.add_tooltip(self.btn_stop, "tooltip_stop")
        self.btn_new_measure = tk.Button(ai, text="🔄 " + self.t("btn_new_measure"), command=self.refresh_for_new_measurement, bg="#E67E22", fg="white", font=("Segoe UI", 9), relief="groove", bd=1, cursor="hand2"); self.btn_new_measure.pack(fill="x", pady=(5, 0)); self.add_tooltip(self.btn_new_measure, "tooltip_new_measure")

        # ===== CARD 4: ACTIONS =====
        self.actions_card = modern_card(cf, "💾 " + self.t("actions_title")); self.actions_card.pack(fill="x", pady=5, padx=5)
        aci = tk.Frame(self.actions_card, bg=THEME["panel"]); aci.pack(fill="x", padx=5, pady=5)
        sb = tk.Frame(aci, bg=THEME["panel"]); sb.pack(fill="x", pady=2)
        self.btn_choose_dir = tk.Button(sb, text="📁", command=self.choose_directory, bg=THEME["disabled"], fg="white", font=("Segoe UI", 9), relief="groove", bd=1, cursor="hand2", width=3); self.btn_choose_dir.pack(side="left", padx=1); self.add_tooltip(self.btn_choose_dir, "tooltip_choose_dir")
        self.btn_export = tk.Button(sb, text="📊 " + self.t("btn_excel"), command=self.export_excel, bg=THEME["success"], fg="white", font=("Segoe UI", 9), relief="groove", bd=1, cursor="hand2"); self.btn_export.pack(side="left", fill="x", expand=True, padx=1); self.add_tooltip(self.btn_export, "tooltip_export")
        self.btn_save_figure = tk.Button(aci, text="📸 " + self.t("btn_save_figure"), command=self.save_figure, bg="#9B59B6", fg="white", font=("Segoe UI", 9), relief="groove", bd=1, cursor="hand2"); self.btn_save_figure.pack(fill="x", pady=(3, 0)); self.add_tooltip(self.btn_save_figure, "tooltip_save_figure")
        self.label_path = tk.Label(aci, text="📂 " + self.t("no_dir_selected"), bg=THEME["panel"], fg=THEME["text_light"], padx=5, pady=3, anchor="w", font=("Segoe UI", 8), wraplength=340, justify="left"); self.label_path.pack(fill="x", pady=(3, 0))

        # ===== CARD 5: ANALYSE =====
        self.analyse_card = modern_card(cf, "🔬 " + self.t("analysis_title")); self.analyse_card.pack(fill="x", pady=5, padx=5)
        anai = tk.Frame(self.analyse_card, bg=THEME["panel"]); anai.pack(fill="x", padx=5, pady=5)
        self.btn_add_curve = tk.Button(anai, text="➕ " + self.t("btn_add_curve"), command=self.add_curve, bg=THEME["primary"], fg="white", font=("Segoe UI", 9), relief="groove", bd=1, cursor="hand2"); self.btn_add_curve.pack(fill="x", pady=2); self.add_tooltip(self.btn_add_curve, "tooltip_add_curve")
        pb = tk.Frame(anai, bg=THEME["panel"]); pb.pack(fill="x", pady=2)
        self.btn_point_course = tk.Button(pb, text="🔵 " + self.t("btn_add_point_course"), command=self.add_point_at_course_interactive, bg=THEME["secondary"], fg="white", font=("Segoe UI", 9), relief="groove", bd=1, cursor="hand2"); self.btn_point_course.pack(side="left", fill="x", expand=True, padx=1); self.add_tooltip(self.btn_point_course, "tooltip_add_point_course")
        self.btn_point_effort = tk.Button(pb, text="🔺 " + self.t("btn_add_point_effort"), command=self.add_point_at_effort_interactive, bg=THEME["secondary"], fg="white", font=("Segoe UI", 9), relief="groove", bd=1, cursor="hand2"); self.btn_point_effort.pack(side="left", fill="x", expand=True, padx=1); self.add_tooltip(self.btn_point_effort, "tooltip_add_point_effort")
        self.btn_smooth = tk.Button(anai, text="〰 " + self.t("btn_smooth"), command=self.show_smooth_dialog, bg="#17A2B8", fg="white", font=("Segoe UI", 9), relief="groove", bd=1, cursor="hand2"); self.btn_smooth.pack(fill="x", pady=2); self.add_tooltip(self.btn_smooth, "tooltip_smooth")
        self.btn_manage = tk.Button(anai, text="🗂 " + self.t("btn_manage"), command=self.manage_graph_elements, bg="#8A2BE2", fg="white", font=("Segoe UI", 9, "bold"), relief="groove", bd=1, cursor="hand2"); self.btn_manage.pack(fill="x", pady=(3, 0)); self.add_tooltip(self.btn_manage, "tooltip_manage")
        abf = tk.Frame(cf, bg=THEME["bg"], pady=5); abf.pack(fill="x", side="bottom", padx=5)
        self.btn_about = tk.Button(abf, text="ℹ " + self.t("about_button"), command=self.show_about, bg=THEME["info"], fg="white", relief="groove", font=("Segoe UI", 8), cursor="hand2"); self.btn_about.pack(fill="x"); self.add_tooltip(self.btn_about, "tooltip_about")

    def _build_right_panel(self, mf):
        right = tk.Frame(mf, bg=THEME["bg"]); right.grid(row=1, column=1, sticky="nsew", padx=(5, 10), pady=5)
        right.grid_rowconfigure(0, weight=1); right.grid_columnconfigure(0, weight=1); right.grid_columnconfigure(1, weight=0)
        self.frame_graph = modern_card(right, "📈 " + self.t("graph_title")); self.frame_graph.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        self.acq_indicator = tk.Label(self.frame_graph, text="", bg=THEME["panel"], fg=THEME["acquisition_active"], font=("Segoe UI", 10, "bold")); self.acq_indicator.pack(anchor="ne", padx=10, pady=(5, 0))
        self.points_panel = modern_card(right, self.t("points_panel_title")); self.points_panel.grid(row=0, column=1, sticky="nsew"); self.points_panel.config(width=180); self.points_panel.grid_propagate(False)
        self.points_listbox = tk.Listbox(self.points_panel, font=("Consolas", 8), bg=THEME["panel"], fg=THEME["text"], selectbackground=THEME["primary"], width=22, height=20); self.points_listbox.pack(fill="both", expand=True, padx=3, pady=3)

    def create_graph(self):
        self.fig = plt.figure(figsize=(8, 5), facecolor=THEME["panel"], edgecolor=THEME["border"], linewidth=0.5)
        self.ax = self.fig.add_subplot(111)
        self.mpl_canvas = FigureCanvasTkAgg(self.fig, master=self.frame_graph)
        # TOOLBAR EN PREMIER — packée side=bottom AVANT le canvas pour que tkinter lui réserve la place
        toolbar_frame = tk.Frame(self.frame_graph, bg="#E8E8E8", bd=1, relief="raised", height=36)
        toolbar_frame.pack(side="bottom", fill="x", padx=2, pady=(0, 2))
        toolbar_frame.pack_propagate(True)
        self.toolbar = CustomToolbar(self.mpl_canvas, toolbar_frame, app_ref=self)
        self.toolbar.config(bg="#E8E8E8")
        for child in self.toolbar.winfo_children():
            try: child.config(bg="#E8E8E8")
            except: pass
        self.toolbar.pack(side="left", fill="x", expand=True)
        self.toolbar.update()
        # CANVAS EN SECOND — prend le reste de l'espace
        self.mpl_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.plot_manager = PlotManager(self.ax); self.update_plot()

    # =================== PRECONFIG ===================
    def _on_range_selected(self, event=None):
        sel = self.range_combo.get()
        if not sel: return
        for direction in ("push", "pull"):
            for r in KISTLER_RANGES[direction]:
                if r['label'] in sel:
                    max_force = abs(r['max'])
                    if max_force > KISTLER_POPUP_THRESHOLD_N:
                        messagebox.showwarning(self.t("kistler_popup_title"), self.t("kistler_popup_text"))
                    return

    def apply_preconfig(self):
        """Applique la pré-configuration. Passe le cadre et bouton de rouge à vert."""
        try:
            sc = self.sensitivity_course.get()
            if sc <= 0: raise ValueError
        except:
            messagebox.showerror(self.t("invalid_sensitivity_title"), self.t("invalid_sensitivity_body"))
            return
        self.preconfig_applied = True
        self.preconfig_frame.config(fg=THEME["preconfig_applied"], highlightbackground=THEME["preconfig_applied"], highlightcolor=THEME["preconfig_applied"])
        self.btn_apply_preconfig.config(bg=THEME["preconfig_applied"])
        logging.info(f"Pré-config appliquée: effort={self.sensitivity_effort} N/V, course={sc} mm/pas, freq={self.frequency} Hz")

    def _show_preconfig_info(self):
        dev = self.device_var.get() or "Dev1"
        info = (f"ℹ️ Récapitulatif pré-configuration\n\n"
                f"━━ Effort ━━\n"
                f"  Sensibilité : {FIXED_EFFORT_SENSITIVITY} N/V (fixe)\n"
                f"  Canal : {FIXED_EFFORT_CHANNEL} (RSE ±10V)\n\n"
                f"━━ Course ━━\n"
                f"  Sensibilité : {self.sensitivity_course.get()} mm/pas (éditable)\n"
                f"  Encodeur : {ENCODER_CONFIG['name']}\n"
                f"  Décodage : {ENCODER_CONFIG['decoding']}\n"
                f"  Compteur : {dev}/{ENCODER_CONFIG['counter']}\n"
                f"  PFI : A={ENCODER_CONFIG['pfi_a']} B={ENCODER_CONFIG['pfi_b']}\n\n"
                f"━━ Acquisition ━━\n"
                f"  Fréquence : {FIXED_FREQUENCY} Hz (fixe)\n"
                f"  Synchronisation : {ENCODER_CONFIG['sync_source']}")
        messagebox.showinfo(self.t("preconfig_info_title"), info)

    # =================== LANGUAGE / MODE ===================
    def toggle_language(self):
        self.lang = "en" if self.lang == "fr" else "fr"
        self.update_ui_texts(); self.update_plot()

    def update_ui_texts(self):
        self.root.title(self.t("app_title")); self.btn_lang.config(text=self.t("lang_button"))
        self.btn_help.config(text="❓ " + self.t("help_button"))
        self.btn_tutorials.config(text="📖 " + self.t("tutorials_button"))
        self.btn_about.config(text="ℹ " + self.t("about_button"))
        self.conn_card.config(text="🔌 " + self.t("conn_title"))
        self.btn_test_conn.config(text=self.t("btn_test"))
        if self.has_ni_flag and not self.is_connected:
            self.label_status.config(text=self.t("status_not_connected"), fg=THEME["danger"])
        elif not self.has_ni_flag:
            self.label_status.config(text=self.t("status_ni_unavailable"), fg=THEME["warning"])
        self.param_card.config(text="⚙️ " + self.t("params_title"))
        self.preconfig_frame.config(text=self.t("preconfig_title"))
        self.btn_apply_preconfig.config(text="✅ " + self.t("apply_preconfig"))
        self.acq_card.config(text="🎬 " + self.t("acq_title"))
        self.btn_tare.config(text="🔄 " + self.t("btn_tare"))
        self.btn_start.config(text="▶ " + self.t("btn_start"))
        self.btn_stop.config(text="⏹ " + self.t("btn_stop"))
        self.btn_new_measure.config(text="🔄 " + self.t("btn_new_measure"))
        self.actions_card.config(text="💾 " + self.t("actions_title"))
        self.btn_export.config(text="📊 " + self.t("btn_excel"))
        self.btn_save_figure.config(text="📸 " + self.t("btn_save_figure"))
        if not self.save_directory: self.label_path.config(text="📂 " + self.t("no_dir_selected"), fg=THEME["text_light"])
        self.analyse_card.config(text="🔬 " + self.t("analysis_title"))
        self.btn_add_curve.config(text="➕ " + self.t("btn_add_curve"))
        self.btn_point_course.config(text="🔵 " + self.t("btn_add_point_course"))
        self.btn_point_effort.config(text="🔺 " + self.t("btn_add_point_effort"))
        self.btn_smooth.config(text="〰 " + self.t("btn_smooth"))
        self.btn_manage.config(text="🗂 " + self.t("btn_manage"))
        self.frame_graph.config(text="📈 " + self.t("graph_title"))
        self.points_panel.config(text=self.t("points_panel_title"))
        if self.is_acquiring: self.acq_indicator.config(text=self.t("acquisition_active"))
        else: self.acq_indicator.config(text=self.t("acquisition_idle"))
        el = (time.time() - self.start_time) if (self.acquisition_thread and self.acquisition_thread.is_running()) else 0.0
        self.timer_label.config(text=f"⏱ {self.t('timer_prefix')} {el:.1f} s")
        self.rebuild_mode_menu()

    def _on_mode_select(self, lbl):
        m = {self.t("mode_full"): "full", self.t("mode_sensor"): "sensor", self.t("mode_bench"): "bench"}
        self.mode_key.set(m.get(lbl, "full")); self.mode_display.set(lbl); self.update_plot()

    def rebuild_mode_menu(self):
        ls = {"full": self.t("mode_full"), "sensor": self.t("mode_sensor"), "bench": self.t("mode_bench")}
        self.mode_display.set(ls[self.mode_key.get()]); menu = self.optionmenu["menu"]; menu.delete(0, "end")
        for k in ("full", "sensor", "bench"): menu.add_command(label=ls[k], command=lambda ll=ls[k]: self._on_mode_select(ll))

    # =================== CONNEXION / ACQUISITION ===================
    def refresh_devices(self):
        ds = NIDeviceManager.detect_devices()
        if ds: ns = [d.name for d in ds]; self.device_combobox['values'] = ns; self.device_var.set(ns[0] if ns else "")
        else: self.device_combobox['values'] = []; self.device_var.set("")

    def test_connexion(self):
        if not self.has_ni_flag: messagebox.showwarning(self.t("msg_conn_warning_title"), self.t("msg_conn_warning_body")); return
        dn = self.device_var.get()
        if NIDeviceManager.test_connection(dn, FIXED_EFFORT_CHANNEL, FIXED_COURSE_CHANNEL):
            self.is_connected = True; self.label_status.config(text=self.t("status_connected_fmt").format(dev=dn), fg=THEME["success"])
        else: self.is_connected = False; self.label_status.config(text=self.t("status_not_connected"), fg=THEME["danger"])

    def tare(self):
        if not self.is_connected: messagebox.showerror("Tare", self.t("msg_conn_warning_body")); return
        offs = NIDeviceManager.perform_tare(self.device_var.get(), FIXED_EFFORT_CHANNEL, FIXED_COURSE_CHANNEL)
        if offs: self.offset_effort, self.offset_course = offs; messagebox.showinfo(self.t("msg_tare_ok_title"), self.t("msg_tare_ok_body"))

    def start(self):
        if self.acquisition_thread and self.acquisition_thread.is_running(): return
        if not self.is_connected: messagebox.showwarning(self.t("msg_conn_warning_title"), self.t("msg_conn_warning_body")); return
        if not self.preconfig_applied: messagebox.showwarning(self.t("preconfig_warning_title"), self.t("preconfig_warning_text")); return
        sc = self.sensitivity_course.get()
        if sc <= 0: messagebox.showerror("Erreur", self.t("invalid_sensitivity_body")); return
        messagebox.showinfo(self.t("start_popup_title"), self.t("start_popup_text"))
        if self.save_directory: self.data_manager.start_csv_writer(self.save_directory, self.full_test_name())
        self.start_time = time.time(); self.is_acquiring = True
        self.acq_indicator.config(text=self.t("acquisition_active"), fg=THEME["acquisition_active"]); self.update_timer()
        if self.data_manager.is_empty: self.data_manager.clear_main_data()
        self.acquisition_thread = AcquisitionThread(
            device_name=self.device_var.get(),
            effort_channel=FIXED_EFFORT_CHANNEL,
            course_channel=FIXED_COURSE_CHANNEL,
            frequency=self.frequency,
            sens_effort=self.sensitivity_effort,
            sens_course=sc,
            offset_effort=self.offset_effort,
            offset_course=self.offset_course,
            data_manager=self.data_manager,
            update_callback=lambda v: self.root.after_idle(self.update_plot),
            error_callback=lambda msg: self.root.after_idle(lambda: messagebox.showerror(self.t("msg_acq_err_title"), msg)),
            pfi_a=ENCODER_CONFIG["pfi_a"],
            pfi_b=ENCODER_CONFIG["pfi_b"])
        self.acquisition_thread.start()

    def stop(self):
        was_acquiring = self.is_acquiring
        if self.acquisition_thread: self.acquisition_thread.stop()
        self.is_acquiring = False; self.acq_indicator.config(text=self.t("acquisition_idle")); self.update_plot()
        # Détection d'offset UNIQUEMENT après une vraie acquisition
        if was_acquiring and not self.data_manager.is_empty:
            self.root.after(300, self._check_offset_after_acquisition)

    def _check_offset_after_acquisition(self):
        """Vérifie si la courbe a un offset initial et propose de le corriger."""
        offsets = self.data_manager.detect_initial_offset(n_samples=20)
        if offsets is None:
            logging.debug("Offset check: pas de données")
            return
        eff_off = offsets['effort']
        crs_off = offsets['course']
        logging.info(f"Offset détecté — Effort: {eff_off:+.4f} N, Course: {crs_off:+.4f} mm")
        # Seuils : si l'offset est significatif (> 0.5% de la plage ou > seuil absolu)
        data = self.data_manager.get_data_copy()
        if not data['effort'] or not data['course']:
            logging.debug("Offset check: listes vides après get_data_copy")
            return
        eff_range = max(data['effort']) - min(data['effort']) if data['effort'] else 1.0
        crs_range = max(data['course']) - min(data['course']) if data['course'] else 1.0
        eff_significant = abs(eff_off) > max(0.05, eff_range * 0.005)
        crs_significant = abs(crs_off) > max(0.01, crs_range * 0.005)
        logging.info(f"Offset seuils — Effort significant: {eff_significant} (|{eff_off:.4f}| > {max(0.05, eff_range*0.005):.4f}), "
                     f"Course significant: {crs_significant} (|{crs_off:.4f}| > {max(0.01, crs_range*0.005):.4f})")
        if not eff_significant and not crs_significant:
            logging.info("Offset non significatif — pas de popup")
            return
        # Construire le message
        details = []
        if eff_significant:
            details.append(f"Effort : {eff_off:+.3f} N")
        if crs_significant:
            details.append(f"Course : {crs_off:+.3f} mm")
        msg = self.t("offset_detected_msg").format(details="\n".join(details))
        answer = messagebox.askyesno(self.t("offset_detected_title"), msg)
        if answer:
            apply_eff = eff_off if eff_significant else 0.0
            apply_crs = crs_off if crs_significant else 0.0
            self.data_manager.apply_offset(effort_offset=apply_eff, course_offset=apply_crs)
            self.update_plot()

    def update_timer(self):
        if self.acquisition_thread and self.acquisition_thread.is_running():
            self.timer_label.config(text=f"⏱ {self.t('timer_prefix')} {time.time() - self.start_time:.1f} s"); self.root.after(100, self.update_timer)

    # =================== PLOT ===================
    def refresh_plot_title_only(self):
        if not hasattr(self, "ax"): return
        self.ax.set_title(self.get_graph_title(), fontsize=13, fontweight="bold", pad=15); self.mpl_canvas.draw_idle()

    def update_plot(self):
        self.crosshair_line_x = self.crosshair_line_y = None
        data = self.data_manager.get_data_copy(); mode, title = self.mode_key.get(), self.full_test_title()
        self.plot_manager.clear()
        if mode == "sensor":
            self.plot_manager.set_labels(self.t("plot_x_time"), self.t("plot_y_effort"), self.t("plot_title_effort_time").format(title=title))
            if data['time'] and data['effort']:
                self.plot_manager.plot_main_curve(data['time'], data['effort'], label=self.t("legend_effort"), color=self.curve_color)
        elif mode == "bench":
            self.plot_manager.set_labels(self.t("plot_x_time"), self.t("plot_y_course"), self.t("plot_title_course_time").format(title=title))
            if data['time'] and data['course']:
                self.plot_manager.plot_main_curve(data['time'], data['course'], label=self.t("legend_course"), color=self.curve_color)
        else:
            self.plot_manager.set_labels(self.t("plot_y_course"), self.t("plot_y_effort"), self.t("plot_title_effort_course").format(title=title))
            if data['course'] and data['effort']:
                ds = sorted(zip(data['course'], data['effort']), key=lambda x: x[0]); cs, es = zip(*ds) if ds else ([], [])
                self.plot_manager.plot_main_curve(cs, es, label=self.t("legend_essai"), color=self.curve_color)
        self.plot_manager.draw_additional_curves(data['additional_curves'], mode)
        # Filtrer les points pour n'afficher que ceux du mode actif
        mode_points = [p for p in data['points'] if p.get('mode') == mode or p.get('mode') is None]
        self.plot_manager.draw_points(mode_points); self._update_points_panel(mode_points)
        self.plot_manager.finalize(); self.mpl_canvas.draw()

    def _update_points_panel(self, points):
        self.points_listbox.delete(0, tk.END)
        for p in points:
            pt = "C" if p.get('type') == 'course' else "E"
            self.points_listbox.insert(tk.END, f"{p.get('name', '')} [{pt}] ({p.get('x', 0):.2f}, {p.get('y', 0):.2f})")

    # =================== ACTIONS ===================
    def choose_directory(self):
        path = filedialog.askdirectory()
        if path: self.save_directory = path; self.label_path.config(text=f"📂 {path}", fg=THEME["text"])

    def export_excel(self):
        ok, fp = export_complete(self.data_manager, self.save_directory, self.full_test_name(), self.date_str_display, self.mode_display.get(), graph_title=self.get_graph_title())
        if ok:
            if messagebox.askyesno(self.t("export_open_title"), f"{self.t('msg_export_ok_body').format(path=fp)}\n\n{self.t('export_open_question')}"):
                try:
                    if sys.platform == "win32": os.startfile(fp)
                    elif sys.platform == "darwin": subprocess.call(["open", fp])
                    else: subprocess.call(["xdg-open", fp])
                except: pass
        elif self.data_manager.is_empty and not self.data_manager.get_curve_names(): messagebox.showwarning(self.t("msg_export_warn_title"), self.t("msg_export_warn_nodata"))
        elif not self.save_directory: messagebox.showwarning(self.t("msg_export_warn_title"), self.t("msg_export_warn_nodir"))

    def save_figure(self):
        if not self.save_directory: messagebox.showwarning("Export", self.t("msg_export_warn_nodir")); return
        try:
            p = os.path.join(self.save_directory, f"{self.full_test_name()}_figure_{time.strftime('%H-%M-%S')}.png")
            self.fig.savefig(p, dpi=150, bbox_inches="tight"); messagebox.showinfo("Export", f"Figure sauvegardée :\n{p}")
        except Exception as e: messagebox.showerror("Erreur", str(e))

    def get_next_available_color(self):
        data = self.data_manager.get_data_copy(); used = {self.curve_color.upper()}
        for cd in data['additional_curves'].values():
            c = cd.get('color', '')
            if c: used.add(c.upper())
        for c in COLOR_PALETTE:
            if c.upper() not in used: return c
        import random; return f"#{random.randint(0, 0xFFFFFF):06x}"

    def refresh_for_new_measurement(self):
        if self.acquisition_thread and self.acquisition_thread.is_running(): messagebox.showwarning("Acquisition", self.t("msg_new_measure_running")); return
        if not self.data_manager.is_empty:
            r = messagebox.askyesnocancel("Nouvelle mesure", self.t("msg_new_measure_save"))
            if r is None: return
            elif r: self.export_excel()
            archive_name = f"Mesure {self.date_str_display}_{self.test_name_user.get()}"
            existing = self.data_manager.get_curve_names(); idx = 1; base_name = archive_name
            while archive_name in existing: idx += 1; archive_name = f"{base_name} ({idx})"
            self.data_manager.archive_main_as_curve(archive_name, self.curve_color)
        self.curve_color = self.get_next_available_color(); self.data_manager.clear_main_data()
        self.start_time = 0.0; self.timer_label.config(text=f"⏱ {self.t('timer_prefix')} 0.0 s"); self.update_plot()

    # =================== ANALYSE: COURBES ===================
    def add_curve(self):
        name = simpledialog.askstring(self.t("btn_add_curve"), self.t("curve_name_prompt"))
        if not name: return
        path = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx"), ("CSV", "*.csv")])
        if not path: return
        try:
            rows = []
            if path.endswith('.csv'):
                import csv
                with open(path, 'r', encoding="utf-8") as f:
                    for r in csv.reader(f, delimiter=';'):
                        try: rows.append([float(r[0]), float(r[1])])
                        except: pass
            else:
                wb = openpyxl.load_workbook(path, data_only=True)
                ws = wb[wb.sheetnames[1]] if len(wb.sheetnames) >= 2 else wb.active
                for r in ws.iter_rows(values_only=True):
                    if r and len(r) >= 2:
                        try: rows.append([float(r[0]), float(r[1])])
                        except: pass
            if not rows: messagebox.showerror("Erreur", "Aucune donnée valide."); return
            mode = self.mode_key.get(); color = self.get_next_available_color()
            if mode == "sensor": cd = {"time": [r[0] for r in rows], "effort": [r[1] for r in rows]}
            elif mode == "bench": cd = {"time": [r[0] for r in rows], "course": [r[1] for r in rows]}
            else: cd = {"course": [r[0] for r in rows], "effort": [r[1] for r in rows]}
            self.data_manager.add_curve(name, cd, color); self.update_plot()
        except Exception as e: messagebox.showerror("Erreur", str(e))

    # =================== ANALYSE: POINTS (multi-point detection) ===================
    def add_point_at_course_interactive(self): self._add_point_interactive("course")
    def add_point_at_effort_interactive(self): self._add_point_interactive("effort")

    def _add_point_interactive(self, point_type="course"):
        win = tk.Toplevel(self.root); tk_key = "add_point_title_course" if point_type == "course" else "add_point_title_effort"
        win.title(self.t(tk_key)); win.geometry("460x380"); win.resizable(True, True); win.minsize(400, 300); self.set_window_icon(win)
        mf = tk.Frame(win, bg=THEME["panel"], padx=20, pady=15); mf.pack(fill="both", expand=True)
        tk.Label(mf, text=f"📍 {self.t(tk_key)}", font=("Segoe UI", 12, "bold"), bg=THEME["panel"], fg=THEME["primary"]).pack(pady=(0, 10))
        crf = tk.LabelFrame(mf, text=self.t("select_curve_label"), bg=THEME["panel"], fg=THEME["text"], font=FONTS["label"]); crf.pack(fill="x", pady=5)
        cnames = [self.t("main_curve_label")] + list(self.data_manager.get_curve_names()); sv = tk.StringVar(value=cnames[0])
        ttk.Combobox(crf, textvariable=sv, values=cnames, state="readonly", font=FONTS["label"], width=30).pack(padx=10, pady=5)
        vf = tk.LabelFrame(mf, text=self.t("value_label_course") if point_type == "course" else self.t("value_label_effort"), bg=THEME["panel"], fg=THEME["text"], font=FONTS["label"]); vf.pack(fill="x", pady=5)
        ve = tk.Entry(vf, width=15, font=FONTS["label"]); ve.pack(padx=10, pady=5); ve.focus()
        default_color = "#0D6EFD" if point_type == "course" else "#FD7E14"
        clf = tk.LabelFrame(mf, text=self.t("color_optional"), bg=THEME["panel"], fg=THEME["text"], font=FONTS["label"]); clf.pack(fill="x", pady=5)
        cv = tk.StringVar(value=default_color); cdisp = tk.Label(clf, text="   ", bg=cv.get(), width=3, relief="solid", bd=1); cdisp.pack(side="left", padx=10, pady=5)
        def cc():
            c = colorchooser.askcolor(initialcolor=cv.get())[1]
            if c: cv.set(c); cdisp.config(bg=c)
        tk.Button(clf, text=self.t("btn_choose_color"), command=cc, bg=THEME["info"], fg="white", font=FONTS["small"]).pack(side="left", padx=5, pady=5)
        bf = tk.Frame(mf, bg=THEME["panel"]); bf.pack(fill="x", pady=15)

        def val():
            try: value = float(ve.get())
            except ValueError: messagebox.showerror("Erreur", self.t("msg_numeric_error")); return
            data = self.data_manager.get_data_copy(); cn = None if sv.get() == self.t("main_curve_label") else sv.get()
            # Get curve data
            if cn is None:
                if point_type == "course":
                    x_data, y_data = data.get('course', []), data.get('effort', [])
                else:
                    x_data, y_data = data.get('effort', []), data.get('course', [])
            else:
                crv = data['additional_curves'].get(cn, {})
                if not crv: messagebox.showerror("Erreur", self.t("msg_curve_no_data")); return
                if point_type == "course":
                    x_data = crv.get('course', []); y_data = crv.get('effort', [])
                else:
                    x_data = crv.get('effort', []); y_data = crv.get('course', [])
            if not x_data or not y_data: messagebox.showerror("Erreur", self.t("msg_no_data_curve")); return
            # Find ALL matching points (crossings)
            matches = self._find_all_crossings(x_data, y_data, value, point_type)
            if not matches:
                messagebox.showwarning("Attention", self.t("msg_out_of_range")); return
            if len(matches) == 1:
                # Single match: add directly
                mx, my = matches[0]
                if point_type == "course":
                    px, py = mx, my
                else:
                    px, py = my, mx
                pname = f"P{len(data['points'])+1}"
                self.data_manager.add_point(px, py, point_type=point_type, curve_name=cn, color=cv.get(), name=pname, mode=self.mode_key.get())
                self.update_plot(); win.destroy()
                messagebox.showinfo("Point", self.t("msg_point_added"))
            else:
                # Multiple matches: let user choose
                self._show_multi_point_chooser(matches, point_type, cn, cv.get(), data, win)

        tk.Button(bf, text="✅ " + self.t("btn_apply"), command=val, bg=THEME["success"], fg="white", font=FONTS["button"], padx=15).pack(side="left", padx=5)
        tk.Button(bf, text=self.t("btn_close"), command=win.destroy, bg=THEME["disabled"], fg="white", font=FONTS["button"]).pack(side="left", padx=5)

    def _find_all_crossings(self, x_data, y_data, value, point_type):
        """Trouve tous les points où x_data croise 'value'. Retourne liste de (x, y)."""
        x_arr = np.array(x_data, dtype=float)
        y_arr = np.array(y_data, dtype=float)
        matches = []
        for i in range(len(x_arr) - 1):
            if (x_arr[i] <= value <= x_arr[i+1]) or (x_arr[i] >= value >= x_arr[i+1]):
                if x_arr[i+1] == x_arr[i]: continue
                t = (value - x_arr[i]) / (x_arr[i+1] - x_arr[i])
                y_interp = y_arr[i] + t * (y_arr[i+1] - y_arr[i])
                matches.append((value, y_interp))
        return matches

    def _show_multi_point_chooser(self, matches, point_type, curve_name, color, data, parent_win):
        """Preview interactive : sélection dans la liste → zoom + marqueur sur le point sélectionné."""
        win = tk.Toplevel(self.root)
        win.title(self.t("multi_point_title"))
        win.geometry("520x380"); self.set_window_icon(win)
        tk.Label(win, text=self.t("multi_point_text"), font=FONTS["label"], bg=THEME["panel"], fg=THEME["text"], wraplength=480).pack(padx=10, pady=10)

        # Listbox avec tous les matches
        listbox = tk.Listbox(win, font=("Consolas", 10), height=min(len(matches), 8), selectmode=tk.SINGLE)
        for i, (mx, my) in enumerate(matches):
            if point_type == "course":
                listbox.insert(tk.END, f"#{i+1}  Course={mx:.3f} mm  →  Effort={my:.3f} N")
            else:
                listbox.insert(tk.END, f"#{i+1}  Effort={mx:.3f} N  →  Course={my:.3f} mm")
        listbox.pack(fill="x", padx=15, pady=5)

        # Sauvegarder les limites originales du graphe pour restauration
        orig_xlim = self.ax.get_xlim()
        orig_ylim = self.ax.get_ylim()
        temp_artists = []  # marqueurs temporaires à nettoyer

        def _clear_temp():
            """Supprime tous les marqueurs temporaires."""
            for art in temp_artists:
                try: art.remove()
                except: pass
            temp_artists.clear()

        def _on_select(event):
            """Preview interactive : zoom + marqueur quand l'utilisateur sélectionne un point."""
            sel = listbox.curselection()
            if not sel:
                return
            idx = sel[0]
            mx, my = matches[idx]
            _clear_temp()

            # Déterminer les coordonnées selon le mode de tracé actuel
            mode = self.mode_key.get()
            if mode == "full":
                # Course/Effort → x=course, y=effort
                if point_type == "course":
                    plot_x, plot_y = mx, my
                else:
                    plot_x, plot_y = my, mx
            elif mode == "sensor":
                # Temps/Effort — on ne peut pas bien positionner sans le temps, marqueur approximatif
                plot_x, plot_y = mx, my
            else:
                plot_x, plot_y = mx, my

            # Dessiner le marqueur de preview (gros cercle rouge)
            sc = self.ax.scatter([plot_x], [plot_y], s=200, color="red", marker="X",
                                edgecolor="white", linewidth=2, zorder=15)
            temp_artists.append(sc)
            # Lignes de repère
            vl = self.ax.axvline(plot_x, color="red", linestyle=":", alpha=0.7, linewidth=1.5, zorder=14)
            hl = self.ax.axhline(plot_y, color="red", linestyle=":", alpha=0.7, linewidth=1.5, zorder=14)
            temp_artists.append(vl)
            temp_artists.append(hl)
            # Annotation
            ann = self.ax.annotate(f"#{idx+1}", (plot_x, plot_y), textcoords="offset points",
                xytext=(12, 12), fontsize=10, color="red", fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="red", alpha=0.9), zorder=16)
            temp_artists.append(ann)

            # Zoom centré sur le point sélectionné
            x_range = orig_xlim[1] - orig_xlim[0]
            y_range = orig_ylim[1] - orig_ylim[0]
            zoom_margin_x = max(x_range * 0.15, 0.5)
            zoom_margin_y = max(y_range * 0.15, 0.5)
            self.ax.set_xlim(plot_x - zoom_margin_x, plot_x + zoom_margin_x)
            self.ax.set_ylim(plot_y - zoom_margin_y, plot_y + zoom_margin_y)
            self.mpl_canvas.draw()

        listbox.bind("<<ListboxSelect>>", _on_select)
        # Sélectionner le premier par défaut et trigger la preview
        if matches:
            listbox.select_set(0)
            listbox.event_generate("<<ListboxSelect>>")

        def confirm():
            sel = listbox.curselection()
            if not sel:
                return
            idx = sel[0]
            mx, my = matches[idx]
            if point_type == "course":
                px, py = mx, my
            else:
                px, py = my, mx
            pname = f"P{len(data['points'])+1}"
            _clear_temp()
            self.ax.set_xlim(orig_xlim)
            self.ax.set_ylim(orig_ylim)
            self.data_manager.add_point(px, py, point_type=point_type, curve_name=curve_name,
                                        color=color, name=pname, mode=self.mode_key.get())
            self.update_plot()
            win.destroy()
            parent_win.destroy()
            messagebox.showinfo("Point", self.t("msg_point_added"))

        def cancel():
            _clear_temp()
            self.ax.set_xlim(orig_xlim)
            self.ax.set_ylim(orig_ylim)
            self.mpl_canvas.draw()
            win.destroy()

        bf = tk.Frame(win, bg=THEME["panel"]); bf.pack(fill="x", padx=15, pady=10)
        tk.Button(bf, text="✅ " + self.t("btn_apply"), command=confirm, bg=THEME["success"], fg="white", font=FONTS["button"]).pack(side="left", padx=5)
        tk.Button(bf, text=self.t("btn_close"), command=cancel, bg=THEME["disabled"], fg="white", font=FONTS["button"]).pack(side="left", padx=5)
        win.protocol("WM_DELETE_WINDOW", cancel)

    # =================== SMOOTH ===================
    def show_smooth_dialog(self):
        win = tk.Toplevel(self.root); win.title(self.t("smooth_title")); win.geometry("420x200"); self.set_window_icon(win)
        mf = tk.Frame(win, bg=THEME["panel"], padx=15, pady=15); mf.pack(fill="both", expand=True)
        tk.Label(mf, text=self.t("smooth_select_curve"), font=FONTS["label"], bg=THEME["panel"]).pack(anchor="w")
        cnames = [self.t("main_curve_label")] + list(self.data_manager.get_curve_names()); sv = tk.StringVar(value=cnames[0])
        ttk.Combobox(mf, textvariable=sv, values=cnames, state="readonly", font=FONTS["label"]).pack(fill="x", pady=5)
        info_label = tk.Label(mf, text="", font=("Segoe UI", 8), bg=THEME["panel"], fg=THEME["text_dim"] if "text_dim" in THEME else THEME["text"]); info_label.pack(anchor="w", pady=(5, 0))
        def apply():
            cn = "main" if sv.get() == self.t("main_curve_label") else sv.get()
            result = self.data_manager.smooth_curve(cn, smooth_color="#17A2B8")
            if result:
                smooth_name, degree = result
                self.update_plot()
                messagebox.showinfo(self.t("smooth_title"), self.t("smooth_done").format(deg=degree))
                win.destroy()
            else:
                messagebox.showerror("Erreur", self.t("msg_no_data_curve"))
        tk.Button(mf, text=self.t("smooth_apply"), command=apply, bg=THEME["success"], fg="white", font=FONTS["button"], cursor="hand2").pack(pady=12)

    # =================== MANAGE (with reset_all and clear main) ===================
    def manage_graph_elements(self):
        win = tk.Toplevel(self.root); win.title(self.t("manage_title")); win.geometry("550x650"); win.resizable(True, True); self.set_window_icon(win)
        canvas = tk.Canvas(win, bg=THEME["panel"], highlightthickness=0); sb_mg = tk.Scrollbar(win, orient="vertical", command=canvas.yview)
        sf = tk.Frame(canvas, bg=THEME["panel"]); sf.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=sf, anchor="nw", tags="mi"); canvas.configure(yscrollcommand=sb_mg.set)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig("mi", width=e.width))
        canvas.pack(side="left", fill="both", expand=True); sb_mg.pack(side="right", fill="y")

        # === Section Courbes ===
        sc = tk.LabelFrame(sf, text=self.t("section_curves"), bg=THEME["panel"], fg=THEME["primary"], font=("Segoe UI", 10, "bold"), padx=8, pady=5); sc.pack(fill="x", padx=5, pady=5)
        # Courbe principale
        tk.Label(sc, text=self.t("main_curve_current"), font=("Segoe UI", 9, "bold"), bg=THEME["panel"]).pack(anchor="w")
        mcf = tk.Frame(sc, bg=THEME["panel"]); mcf.pack(fill="x", pady=3)
        cdisp = tk.Label(mcf, text="   ", bg=self.curve_color, width=3, relief="solid", bd=1); cdisp.pack(side="left", padx=5)
        def rc_main():
            c = colorchooser.askcolor(initialcolor=self.curve_color)[1]
            if c: self.curve_color = c; cdisp.config(bg=c); self.update_plot()
        tk.Button(mcf, text=self.t("btn_recolor"), command=rc_main, bg=THEME["info"], fg="white", font=("Segoe UI", 9)).pack(side="left", padx=2)
        # Effacer courbe principale
        def clear_main():
            if messagebox.askyesno(self.t("msg_confirm_delete"), self.t("msg_clear_main_confirm")):
                self.data_manager.clear_main_data(); self.start_time = 0.0
                self.timer_label.config(text=f"⏱ {self.t('timer_prefix')} 0.0 s"); self.update_plot()
        tk.Button(mcf, text=self.t("btn_clear_main"), command=clear_main, bg=THEME["danger"], fg="white", font=("Segoe UI", 9)).pack(side="left", padx=2)

        tk.Frame(sc, height=1, bg=THEME["border"]).pack(fill="x", pady=5)
        tk.Label(sc, text=self.t("imported_curves"), font=("Segoe UI", 9, "bold"), bg=THEME["panel"]).pack(anchor="w")
        clf = tk.Frame(sc, bg=THEME["panel"]); clf.pack(fill="x", pady=3)
        clb = tk.Listbox(clf, height=3, font=FONTS["label"]); clb.pack(side="left", fill="x", expand=True, padx=(0, 3))
        data = self.data_manager.get_data_copy()
        for n in self.data_manager.get_curve_names(): clb.insert(tk.END, n); clb.itemconfig(tk.END, bg=data['additional_curves'][n].get('color', THEME["primary"]), fg="white")
        cbf = tk.Frame(sc, bg=THEME["panel"]); cbf.pack(fill="x", pady=3)
        def rc():
            s = clb.curselection()
            if not s: return
            c = colorchooser.askcolor()[1]
            if c: self.data_manager.update_curve_color(clb.get(s[0]), c); clb.itemconfig(s[0], bg=c); self.update_plot()
        def dc():
            s = clb.curselection()
            if not s: return
            if messagebox.askyesno(self.t("msg_confirm_delete"), f"Supprimer '{clb.get(s[0])}' ?"): self.data_manager.remove_curve(clb.get(s[0])); clb.delete(s[0]); self.update_plot()
        tk.Button(cbf, text=self.t("btn_recolor"), command=rc, bg=THEME["info"], fg="white", font=("Segoe UI", 9)).pack(side="left", padx=2)
        tk.Button(cbf, text=self.t("btn_delete"), command=dc, bg=THEME["danger"], fg="white", font=("Segoe UI", 9)).pack(side="left", padx=2)

        # === Section Points ===
        sp = tk.LabelFrame(sf, text=self.t("section_points"), bg=THEME["panel"], fg=THEME["secondary"], font=("Segoe UI", 10, "bold"), padx=8, pady=5); sp.pack(fill="both", expand=True, padx=5, pady=5)
        tk.Label(sp, text=self.t("legend_points"), font=("Segoe UI", 8, "italic"), bg=THEME["panel"], fg=THEME["text_light"]).pack(anchor="w")
        plf = tk.Frame(sp, bg=THEME["panel"]); plf.pack(fill="both", expand=True, pady=3)
        plb = tk.Listbox(plf, height=5, font=("Segoe UI", 9)); plb.pack(side="left", fill="both", expand=True, padx=(0, 3))
        for i, pt in enumerate(self.data_manager.get_points()):
            sym = "🔵" if pt.get('type') == 'course' else "🔺"; cn_pt = pt.get('curve') or "Principale"
            plb.insert(tk.END, f"{sym} #{i+1} | x={pt['x']:.2f} y={pt['y']:.2f} | {cn_pt}"); plb.itemconfig(tk.END, fg=pt.get('color', THEME["secondary"]))
        pbf = tk.Frame(sp, bg=THEME["panel"]); pbf.pack(fill="x", pady=5)
        def rp():
            s = plb.curselection()
            if s:
                c = colorchooser.askcolor()[1]
                if c: self.data_manager.update_point_color(s[0], c); plb.itemconfig(s[0], fg=c); self.update_plot()
        def dp():
            s = plb.curselection()
            if s: self.data_manager.remove_point(s[0]); plb.delete(s[0]); self.update_plot()
        def cap():
            if messagebox.askyesno(self.t("msg_confirm_delete"), self.t("btn_delete_all") + " ?"): self.data_manager.clear_points(); plb.delete(0, tk.END); self.update_plot()
        tk.Button(pbf, text=self.t("btn_recolor"), command=rp, bg=THEME["info"], fg="white", font=("Segoe UI", 9)).pack(side="left", padx=2)
        tk.Button(pbf, text=self.t("btn_delete"), command=dp, bg=THEME["danger"], fg="white", font=("Segoe UI", 9)).pack(side="left", padx=2)
        tk.Button(pbf, text=self.t("btn_delete_all"), command=cap, bg=THEME["danger"], fg="white", font=("Segoe UI", 9)).pack(side="left", padx=2)

        # === Effacer tout (déplacé ici) ===
        tk.Frame(sf, height=1, bg=THEME["border"]).pack(fill="x", padx=5, pady=5)
        def reset_all():
            if self.is_acquiring: messagebox.showwarning("Reset", self.t("msg_new_measure_running")); return
            if not messagebox.askyesno(self.t("msg_confirm_delete"), self.t("msg_reset_all_confirm")): return
            self.data_manager.clear_main_data(); self.data_manager.clear_curves(); self.data_manager.clear_points()
            self.curve_color = THEME["primary"]; self.start_time = 0.0
            self.timer_label.config(text=f"⏱ {self.t('timer_prefix')} 0.0 s"); self.update_plot(); win.destroy()
        tk.Button(sf, text="🗑 " + self.t("btn_reset_all_full"), command=reset_all, bg="#8B0000", fg="white", font=("Segoe UI", 10, "bold"), relief="groove", bd=2, cursor="hand2").pack(fill="x", padx=10, pady=5)
        tk.Button(sf, text="✅ " + self.t("btn_close"), command=win.destroy, bg=THEME["success"], fg="white", font=("Segoe UI", 10, "bold"), padx=15, pady=5).pack(pady=8)

    # =================== HELP / ABOUT / TUTORIALS ===================
    def show_help(self):
        win = tk.Toplevel(self.root); win.title(self.t("help_title")); win.geometry("700x600"); win.resizable(True, True); self.set_window_icon(win)
        frm = tk.Frame(win, bg=THEME["panel"]); frm.pack(fill="both", expand=True, padx=16, pady=16)
        txt = tk.Text(frm, wrap="word", font=FONTS["label"], bg=THEME["panel"], fg=THEME["text"])
        txt.insert("1.0", self.t("help_text").format(version=SOFTWARE_VERSION)); txt.config(state="disabled")
        sb_h = ttk.Scrollbar(frm, command=txt.yview); txt.config(yscrollcommand=sb_h.set); sb_h.pack(side="right", fill="y"); txt.pack(side="left", fill="both", expand=True)
        tk.Button(win, text=self.t("about_close"), command=win.destroy, bg=THEME["info"], fg="white", font=FONTS["button"]).pack(pady=8)

    def show_tutorials(self):
        self._stop_tut_blink()
        win = tk.Toplevel(self.root); win.title(self.t("tutorials_title")); win.geometry("750x680"); win.resizable(True, True); self.set_window_icon(win)
        canvas = tk.Canvas(win, bg=THEME["panel"], highlightthickness=0); sb_t = tk.Scrollbar(win, orient="vertical", command=canvas.yview)
        sf = tk.Frame(canvas, bg=THEME["panel"]); sf.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=sf, anchor="nw", tags="ti"); canvas.configure(yscrollcommand=sb_t.set)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig("ti", width=e.width))
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))
        canvas.pack(side="left", fill="both", expand=True); sb_t.pack(side="right", fill="y")
        tk.Label(sf, text="📖 " + self.t("tutorials_title"), font=("Segoe UI", 14, "bold"), bg=THEME["panel"], fg=THEME["primary"]).pack(pady=(15, 10))
        for i in range(1, 7):
            tt = f"tutorials_text_{i}_title"; tx = f"tutorials_text_{i}"
            lf = tk.LabelFrame(sf, text=self.t(tt), bg=THEME["panel"], fg=THEME["text"], font=("Segoe UI", 10, "bold"), padx=10, pady=8); lf.pack(fill="x", padx=20, pady=5)
            tk.Label(lf, text=self.t(tx), bg=THEME["panel"], fg=THEME["text"], font=("Segoe UI", 9), justify="left", wraplength=660, anchor="w").pack(anchor="w")
            num = i
            tk.Button(lf, text=self.t("tutorial_go_button"), command=lambda n=num, w=win: (w.destroy(), self.guide.start(n)), bg=THEME["success"], fg="white", font=("Segoe UI", 9, "bold"), cursor="hand2", relief="groove", bd=1).pack(anchor="e", pady=(5, 0))
        mlf = tk.LabelFrame(sf, text="GESTION AVANCÉE", bg=THEME["panel"], fg=THEME["text"], font=("Segoe UI", 10, "bold"), padx=10, pady=8); mlf.pack(fill="x", padx=20, pady=5)
        tk.Label(mlf, text=self.t("tutorials_manage_text"), bg=THEME["panel"], fg=THEME["text"], font=("Segoe UI", 9), justify="left", wraplength=660, anchor="w").pack(anchor="w")
        tk.Button(sf, text=self.t("about_close"), command=win.destroy, bg=THEME["info"], fg="white", font=FONTS["button"]).pack(pady=10)

    def show_about(self):
        win = tk.Toplevel(self.root); win.title(self.t("about_title")); win.geometry("380x260"); win.resizable(False, False); self.set_window_icon(win)
        frm = tk.Frame(win, bg=THEME["panel"]); frm.pack(fill="both", expand=True, padx=16, pady=16)
        logo = self.get_small_logo(sz=(100, 100))
        if logo: l = tk.Label(frm, image=logo, bg=THEME["panel"]); l.image = logo; l.pack(pady=(0, 6))
        tk.Label(frm, text="labCE", font=("Segoe UI", 14, "bold"), bg=THEME["panel"], fg=THEME["primary"]).pack()
        tk.Label(frm, text=self.t("about_version"), bg=THEME["panel"], fg=THEME["text"], font=("Segoe UI", 10)).pack(pady=(2, 0))
        tk.Label(frm, text=self.t("about_author"), bg=THEME["panel"], fg=THEME["text"], font=("Segoe UI", 10, "italic")).pack(pady=(2, 0))
        tk.Label(frm, text=f"Date : {self.date_str_display}", bg=THEME["panel"], fg=THEME["text_light"], font=("Segoe UI", 9)).pack(pady=(2, 8))
        tk.Button(frm, text=self.t("about_close"), command=win.destroy, bg=THEME["primary"], fg="white", font=FONTS["button"]).pack(pady=4)

    def _start_tut_blink(self):
        self._tut_blink_id = self.root.after(500, self._blink_tut)
    def _blink_tut(self):
        try:
            cur = self.btn_tutorials.cget("bg")
            self.btn_tutorials.config(bg="#FF6B00" if cur == "#FFFFFF" else "#FFFFFF", fg="white" if cur == "#FFFFFF" else "#FF6B00")
            self._tut_blink_id = self.root.after(600, self._blink_tut)
        except: pass
    def _stop_tut_blink(self):
        if self._tut_blink_id: self.root.after_cancel(self._tut_blink_id); self._tut_blink_id = None
        self.btn_tutorials.config(bg="#FF6B00", fg="white")


if __name__ == "__main__":
    try: show_splash_then_start(BancEssaiApp)
    except KeyboardInterrupt: sys.exit(0)
    except Exception as e: logging.error(f"Erreur fatale: {e}"); import traceback; traceback.print_exc(); sys.exit(1)