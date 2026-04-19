"""
labCE v5.1 - Core utilities, guide system, welcome window
"""
import tkinter as tk
from tkinter import messagebox
import os, logging
from PIL import Image, ImageTk
from config import THEME, FONTS, GUIDE_SEQUENCES, KISTLER_RANGES, BASE_DIR
from translations import TRANSLATIONS


class ToolTip:
    def __init__(self, widget, text_func):
        self.widget, self.text_func, self.tip_window = widget, text_func, None
        widget.bind("<Enter>", self.show); widget.bind("<Leave>", self.hide)

    def show(self, event=None):
        text = self.text_func()
        if not text: return
        x = self.widget.winfo_rootx() + 30
        y = self.widget.winfo_rooty() + 25
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True); tw.wm_geometry(f"+{x}+{y}")
        tk.Label(tw, text=text, justify="left", bg="#333", fg="white",
            relief="solid", borderwidth=1, font=FONTS["tooltip"],
            padx=8, pady=4, wraplength=300).pack()

    def hide(self, event=None):
        if self.tip_window:
            self.tip_window.destroy(); self.tip_window = None


def modern_card(parent, title=None):
    f = tk.LabelFrame(parent, bg=THEME["panel"], fg=THEME["text"],
        bd=1, relief="groove", padx=10, pady=8)
    if title: f.config(text=title, font=FONTS["label"])
    return f


class InteractiveGuide:
    """Guide interactif: clignotement séquentiel des boutons."""

    def __init__(self, app):
        self.app = app
        self.active = False
        self.sequence = []
        self.current_idx = 0
        self._blink_id = None
        self._banner = None
        self._original_bg = None
        self._bound_btn = None

    def start(self, method_num):
        seq = GUIDE_SEQUENCES.get(method_num, [])
        if not seq: return
        self.sequence = seq
        self.current_idx = 0
        self.active = True
        self._show_banner()
        messagebox.showinfo(
            self.app.t("guide_popup_title"),
            self.app.t("guide_popup_text"))
        self._start_current_blink()

    def stop(self):
        self._stop_blink()
        self._hide_banner()
        self.active = False
        self.sequence = []
        self.current_idx = 0

    def _show_banner(self):
        if self._banner: return
        self._banner = tk.Frame(self.app.main_frame, bg=THEME["guide_banner"], height=30)
        self._banner.grid(row=2, column=0, columnspan=2, sticky="ew")
        tk.Label(self._banner, text=self.app.t("guide_banner_text"),
            bg=THEME["guide_banner"], fg=THEME["guide_banner_text"],
            font=("Segoe UI", 9, "bold")).pack(side="left", padx=10)
        tk.Button(self._banner, text=self.app.t("guide_disable"),
            command=self.stop, bg=THEME["danger"], fg="white",
            font=("Segoe UI", 8, "bold"), relief="flat", cursor="hand2",
            padx=8, pady=2).pack(side="right", padx=10)

    def _hide_banner(self):
        if self._banner:
            self._banner.destroy(); self._banner = None

    def _get_btn(self):
        if self.current_idx >= len(self.sequence): return None
        return getattr(self.app, self.sequence[self.current_idx], None)

    def _start_current_blink(self):
        btn = self._get_btn()
        if not btn: self.stop(); return
        self._original_bg = btn.cget("bg")
        self._bound_btn = btn
        btn.bind("<Button-1>", self._on_click, add="+")
        self._blink()

    def _blink(self):
        if not self.active: return
        btn = self._get_btn()
        if not btn: self.stop(); return
        cur = btn.cget("bg")
        btn.config(bg="#FFEB3B" if cur != "#FFEB3B" else self._original_bg)
        self._blink_id = self.app.root.after(400, self._blink)

    def _stop_blink(self):
        if self._blink_id:
            self.app.root.after_cancel(self._blink_id)
            self._blink_id = None
        if self._bound_btn and self._original_bg:
            try:
                self._bound_btn.config(bg=self._original_bg)
                self._bound_btn.unbind("<Button-1>")
            except: pass
        self._bound_btn = None

    def _on_click(self, event=None):
        self._stop_blink()
        self.current_idx += 1
        if self.current_idx >= len(self.sequence):
            self.stop()
        else:
            self.app.root.after(300, self._start_current_blink)


def show_welcome_window(root, app_callback, icon_img=None):
    """Fenêtre d'accueil bilingue, centrée, avec scroll fluide."""
    lang_var = {"lang": "fr"}

    def t(k):
        return TRANSLATIONS.get(lang_var["lang"], TRANSLATIONS["fr"]).get(k, k)

    win = tk.Toplevel(root)
    win.title(t("welcome_title"))
    win.configure(bg=THEME["panel"])
    win.grab_set()
    win.focus_force()
    win.protocol("WM_DELETE_WINDOW", lambda: None)  # Empêcher fermeture sans cliquer Commencer

    # Centrer
    ww, wh = 740, 700
    sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
    win.geometry(f"{ww}x{wh}+{(sw-ww)//2}+{(sh-wh)//2}")
    win.resizable(True, True)

    # Icon
    try:
        ico = os.path.join(BASE_DIR, "logo_labce.ico")
        png = os.path.join(BASE_DIR, "logo_labce.png")
        if os.name == "nt" and os.path.isfile(ico): win.iconbitmap(ico)
        elif os.path.isfile(png) and icon_img: win.iconphoto(True, icon_img)
    except: pass

    # Container for rebuild
    container = tk.Frame(win, bg=THEME["panel"])
    container.pack(fill="both", expand=True)

    name_var = tk.StringVar(value="Essai_01")

    def build_content():
        for w in container.winfo_children(): w.destroy()

        # Scrollable canvas
        canvas = tk.Canvas(container, bg=THEME["panel"], highlightthickness=0)
        sb = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        sf = tk.Frame(canvas, bg=THEME["panel"])
        sf.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=sf, anchor="nw", tags="sf_inner")
        canvas.configure(yscrollcommand=sb.set)

        def resize_inner(event):
            canvas.itemconfig("sf_inner", width=event.width)
        canvas.bind("<Configure>", resize_inner)

        # Mousewheel scroll
        def _mw(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            return "break"
        canvas.bind_all("<MouseWheel>", _mw)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        # Langue button top right
        top_bar = tk.Frame(sf, bg=THEME["panel"])
        top_bar.pack(fill="x", padx=20, pady=(10, 0))
        tk.Button(top_bar, text="🌐 FR" if lang_var["lang"] == "fr" else "🌐 EN",
            command=lambda: toggle_lang_welcome(),
            bg=THEME["info"], fg="white", font=("Segoe UI", 9),
            relief="groove", bd=1, cursor="hand2").pack(side="right")

        # Logo
        try:
            png_path = os.path.join(BASE_DIR, "logo_labce.png")
            if os.path.isfile(png_path):
                img = Image.open(png_path); img.thumbnail((90, 90), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                lbl = tk.Label(sf, image=photo, bg=THEME["panel"]); lbl.image = photo; lbl.pack(pady=(5, 5))
        except: pass

        tk.Label(sf, text=t("welcome_title"), font=("Segoe UI", 15, "bold"),
            bg=THEME["panel"], fg=THEME["primary"]).pack(pady=(5, 10))

        # Prérequis
        pf = tk.LabelFrame(sf, text="📋 " + t("welcome_prereq_title"),
            bg=THEME["panel"], fg=THEME["text"], font=("Segoe UI", 10, "bold"), padx=10, pady=8)
        pf.pack(fill="x", padx=20, pady=5)
        tk.Label(pf, text=t("welcome_prereq_text"), bg=THEME["panel"], fg=THEME["text"],
            font=("Segoe UI", 9), justify="left", wraplength=640, anchor="w").pack(anchor="w")

        # Connexion
        cf = tk.LabelFrame(sf, text="🔌 " + t("welcome_conn_title"),
            bg=THEME["panel"], fg=THEME["text"], font=("Segoe UI", 10, "bold"), padx=10, pady=8)
        cf.pack(fill="x", padx=20, pady=5)
        tk.Label(cf, text=t("welcome_conn_text"), bg=THEME["panel"], fg=THEME["text"],
            font=("Segoe UI", 9), justify="left", wraplength=640, anchor="w").pack(anchor="w")

        # Plages
        rf = tk.LabelFrame(sf, text="📏 " + t("welcome_ranges_title"),
            bg=THEME["panel"], fg=THEME["text"], font=("Segoe UI", 10, "bold"), padx=10, pady=8)
        rf.pack(fill="x", padx=20, pady=5)
        tk.Label(rf, text="⬆ " + t("welcome_push") + " :", font=("Segoe UI", 9, "bold"),
            bg=THEME["panel"], fg=THEME["success"]).pack(anchor="w")
        for r in KISTLER_RANGES["push"]:
            tk.Label(rf, text=f"  • {r['label']}  →  {r['sensitivity_pCN']} pC/N",
                bg=THEME["panel"], fg=THEME["text"], font=("Segoe UI", 9)).pack(anchor="w")
        tk.Label(rf, text="⬇ " + t("welcome_pull") + " :", font=("Segoe UI", 9, "bold"),
            bg=THEME["panel"], fg=THEME["danger"]).pack(anchor="w", pady=(5, 0))
        for r in KISTLER_RANGES["pull"]:
            tk.Label(rf, text=f"  • {r['label']}  →  {r['sensitivity_pCN']} pC/N",
                bg=THEME["panel"], fg=THEME["text"], font=("Segoe UI", 9)).pack(anchor="w")

        # Paramètres
        prf = tk.LabelFrame(sf, text="⚙️ " + t("welcome_params_title"),
            bg=THEME["panel"], fg=THEME["text"], font=("Segoe UI", 10, "bold"), padx=10, pady=8)
        prf.pack(fill="x", padx=20, pady=5)
        tk.Label(prf, text=t("welcome_params_text"), bg=THEME["panel"], fg=THEME["text"],
            font=("Segoe UI", 9), justify="left", wraplength=640, anchor="w").pack(anchor="w")

        # Section Tutoriels — indication pour les nouveaux utilisateurs
        tf = tk.LabelFrame(sf, text="📖 " + t("welcome_tutorials_title"),
            bg=THEME["panel"], fg=THEME["text"], font=("Segoe UI", 10, "bold"), padx=10, pady=8)
        tf.pack(fill="x", padx=20, pady=5)
        tk.Label(tf, text=t("welcome_tutorials_text"), bg=THEME["panel"], fg=THEME["text"],
            font=("Segoe UI", 9), justify="left", wraplength=640, anchor="w").pack(anchor="w")

        # Nom essai
        nf = tk.Frame(sf, bg=THEME["panel"]); nf.pack(fill="x", padx=20, pady=10)
        tk.Label(nf, text="📝 " + t("welcome_test_name"),
            font=("Segoe UI", 11, "bold"), bg=THEME["panel"], fg=THEME["primary"]).pack(side="left")
        tk.Entry(nf, textvariable=name_var, width=25, font=("Segoe UI", 11),
            relief="groove", bd=2).pack(side="left", padx=10)

        # Bouton commencer
        def commence():
            canvas.unbind_all("<MouseWheel>")
            app_callback(name_var.get())
            win.destroy()
        tk.Button(sf, text=t("welcome_start"), command=commence,
            bg=THEME["success"], fg="white", font=("Segoe UI", 13, "bold"),
            padx=30, pady=10, cursor="hand2", relief="groove", bd=2).pack(pady=20)

    def toggle_lang_welcome():
        lang_var["lang"] = "en" if lang_var["lang"] == "fr" else "fr"
        win.title(t("welcome_title"))
        build_content()

    build_content()


def show_splash_then_start(app_class):
    """Splash screen → Welcome (toujours) → App."""
    root = tk.Tk(); root.withdraw()
    ico = os.path.join(BASE_DIR, "logo_labce.ico")
    png = os.path.join(BASE_DIR, "logo_labce.png")
    icon_img = None
    try:
        if os.name == "nt" and os.path.isfile(ico): root.iconbitmap(ico)
        elif os.path.isfile(png):
            icon_img = tk.PhotoImage(file=png)
            root.iconphoto(True, icon_img)
    except: pass

    splash = tk.Toplevel(root); splash.overrideredirect(True); splash.configure(bg=THEME["panel"])
    try:
        if os.path.isfile(png):
            img = tk.PhotoImage(file=png)
            tk.Label(splash, image=img, bg=THEME["panel"]).pack(padx=16, pady=16)
        else:
            tk.Label(splash, text="labCE", font=FONTS["title"],
                bg=THEME["panel"], fg=THEME["primary"]).pack(padx=24, pady=24)
    except:
        tk.Label(splash, text="labCE", font=FONTS["title"],
            bg=THEME["panel"], fg=THEME["primary"]).pack(padx=24, pady=24)

    splash.update_idletasks()
    sw, sh = splash.winfo_screenwidth(), splash.winfo_screenheight()
    ww = max(260, splash.winfo_reqwidth())
    hh = max(260, splash.winfo_reqheight())
    splash.geometry(f"{ww}x{hh}+{(sw-ww)//2}+{(sh-hh)//2}")

    def _start_app(test_name="Essai_01"):
        root.deiconify()
        sw2, sh2 = root.winfo_screenwidth(), root.winfo_screenheight()
        ww2, hh2 = int(sw2 * 0.85), int(sh2 * 0.9)
        root.geometry(f"{ww2}x{hh2}+{(sw2-ww2)//2}+{(sh2-hh2)//2}")
        root.minsize(int(sw2 * 0.5), int(sh2 * 0.5))
        app = app_class(root)
        app.test_name_user.set(test_name)
        app.update_plot()

    def _after_splash():
        splash.destroy()
        # Welcome s'affiche TOUJOURS à chaque lancement
        show_welcome_window(root, _start_app, icon_img)

    root.after(1500, _after_splash)
    root.mainloop()