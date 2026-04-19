"""
Traductions FR/EN pour labCE v5.3
"""
from config import SOFTWARE_VERSION, AUTHOR

TRANSLATIONS = {
    "fr": {
        "app_title": "labCE",
        "lang_button": "🌐 FR",
        "mode_full": "Essai complet", "mode_sensor": "Test Capteur", "mode_bench": "Test Banc",
        # Connexion
        "conn_title": "Connexion",
        "btn_test": "Connecter la carte",
        "device_label": "Carte de connexion",
        "status_not_connected": "❌ Non connectée",
        "status_ni_unavailable": "⚠️ NI indisponible",
        "status_connected_fmt": "🟢 {dev} connectée",
        # Params
        "params_title": "Paramètres",
        "preconfig_title": "Pré-configuration",
        "range_label": "Plage de mesure :",
        "sens_course_label": "Sens. Course :",
        "apply_preconfig": "Appliquer pré-config",
        "preconfig_info_title": "Informations pré-configuration",
        "preconfig_warning_title": "Pré-configuration",
        "preconfig_warning_text": "Veuillez appliquer la pré-configuration avant de démarrer l'acquisition.",
        "kistler_popup_title": "⚠️ Changement ampli Kistler",
        "kistler_popup_text": "La plage sélectionnée dépasse 10 N.\n\nVeuillez changer la pré-configuration sur l'ampli Kistler 9217A\navant de lancer l'acquisition.",
        # Acquisition
        "acq_title": "Acquisition",
        "btn_tare": "Tare",
        "btn_start": "Démarrer",
        "btn_stop": "Arrêter",
        "btn_new_measure": "Nouvelle mesure",
        "acquisition_active": "● ACQUISITION EN COURS",
        "acquisition_idle": "",
        "start_popup_title": "Préparation mesure",
        "start_popup_text": "Avant de démarrer :\n\n1. Appuyez 2 fois sur le bouton MESURE (vert)\n   de l'ampli Kistler pour réinitialiser l'effort.\n\n2. Vérifiez que l'afficheur Kistler indique 0.0 N.\n\nCliquez OK pour lancer l'acquisition.",
        # Actions
        "actions_title": "Actions",
        "btn_excel": "Export Excel",
        "btn_save_figure": "Sauvegarder figure",
        "no_dir_selected": "Aucun dossier sélectionné",
        "export_open_question": "Voulez-vous ouvrir le fichier exporté ?",
        "export_open_title": "Fichier exporté",
        # Analyse
        "analysis_title": "Analyse",
        "btn_add_curve": "Ajouter courbe",
        "btn_add_point_course": "+ point (course)",
        "btn_add_point_effort": "+ point (effort)",
        "btn_manage": "Gérer",
        "btn_smooth": "Lisser courbe",
        "smooth_title": "Lissage de courbe",
        "smooth_select_curve": "Courbe à lisser :",
        "smooth_apply": "Appliquer",
        "smooth_done": "Lissage appliqué (degré optimal : {deg})",
        # Visu
        "graph_title": "Visualisation",
        "points_panel_title": "Points",
        # Point dialog
        "select_curve_label": "Choisir la courbe :",
        "main_curve_label": "Courbe principale",
        "value_label_course": "Valeur de course (mm) :",
        "value_label_effort": "Valeur d'effort (N) :",
        "color_optional": "Couleur (optionnel)",
        "btn_apply": "Appliquer",
        "btn_close": "Fermer",
        "btn_choose_color": "Choisir",
        "add_point_title_course": "Ajouter un point (course)",
        "add_point_title_effort": "Ajouter un point (effort)",
        # Multi-point
        "multi_point_title": "Points multiples détectés",
        "multi_point_text": "Plusieurs points correspondent à cette valeur sur la courbe.\nLe graphe a zoomé pour les montrer. Sélectionnez celui que vous souhaitez ajouter :",
        # Manage
        "manage_title": "Gestion des éléments du graphique",
        "section_curves": "COURBES",
        "section_points": "POINTS DE MESURE",
        "main_curve_current": "Courbe Principale (mesure actuelle)",
        "imported_curves": "Courbes Importées / Archivées",
        "btn_recolor": "Recolorer",
        "btn_delete": "Supprimer",
        "btn_delete_all": "Tout effacer",
        "btn_clear_main": "Effacer principale",
        "msg_clear_main_confirm": "Effacer la courbe principale (dernière mesure) ?\nLes courbes archivées ne seront pas touchées.",
        "btn_reset_all_full": "Effacer toutes les courbes et points",
        "msg_reset_all_confirm": "Effacer TOUTES les courbes et points du graphique ?",
        "legend_points": "🔵 = Course  |  🔺 = Effort",
        "color_label": "Couleur :",
        # Timer
        "timer_prefix": "Temps :",
        # About
        "about_title": "À propos de labCE",
        "about_button": "À propos",
        "about_version": f"Version : {SOFTWARE_VERSION}",
        "about_author": f"Créé par {AUTHOR}",
        "about_close": "Fermer",
        # Help
        "help_button": "Aide",
        "help_title": "Aide - labCE",
        "help_text": """Guide d'utilisation de labCE {version}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔌 CONNEXION
Branchez le câble USB A de la carte NI sur votre PC.
Allumez la carte NI (bouton arrière droit) et le Kistler.
Cliquez sur Rafraîchir puis Connecter la carte pour obtenir la pastille verte.

⚙️ PARAMÈTRES
Choisissez votre plage de mesure Kistler.
Si la plage dépasse 10 N, une popup vous rappelle de changer l'ampli.
La sensibilité effort est fixée à 1 N/V.
La sensibilité course est réglable (défaut 1 mm/pas).
La fréquence est fixée à 50 Hz.
Appuyez sur Appliquer pré-config (le cadre passe au vert).

🎬 ACQUISITION
Tare → Démarrer (popup Kistler) → Arrêter.
Le bouton Gérer dans Analyse permet d'effacer la courbe principale
ou toutes les courbes.

💾 ACTIONS
Export Excel : 2 feuilles (Données + Effort/Course XY).
Le nom du fichier indique le nombre de courbes.

🔬 ANALYSE
+ point (course/effort) : si plusieurs points sont détectés,
le logiciel zoome et vous laisse choisir.
Lisser courbe : régression polynomiale.
Gérer : modifier couleurs, supprimer courbes/points.
""",
        # Tutorials
        "tutorials_button": "Tutoriels",
        "tutorials_title": "Tutoriels - labCE",
        "tutorial_go_button": "▶ Réaliser cette acquisition",
        "tutorials_text_1_title": "1. ACQUISITION STANDARD",
        "tutorials_text_1": """1. Connectez la carte NI.
2. Appliquez la pré-configuration (cadre passe au vert).
3. Faites la Tare.
4. Démarrez l'acquisition.
5. Arrêtez, choisissez un dossier, exportez.""",
        "tutorials_text_2_title": "2. ACQUISITION + ANALYSE",
        "tutorials_text_2": """Même méthode que l'acquisition standard.
Avant d'exporter :
  • + point (course) pour trouver l'effort à une distance.
  • + point (effort) pour trouver la distance à un effort.
Si plusieurs points sont trouvés, le logiciel zoome pour choisir.""",
        "tutorials_text_3_title": "3. ACQUISITION + COMPARAISON MESURÉE",
        "tutorials_text_3": """Après une acquisition, appuyez sur Nouvelle mesure :
  → La courbe est archivée avec une nouvelle couleur.
  → Le timer se réinitialise. Relancez l'acquisition.""",
        "tutorials_text_4_title": "4. ACQUISITION + ANALYSE + COMPARAISON",
        "tutorials_text_4": """Combinez les méthodes 2 et 3 :
  → Tracez, ajoutez des points, puis Nouvelle mesure.
  → Tracez la seconde courbe et ajoutez des points.""",
        "tutorials_text_5_title": "5. ACQUISITION + COMPARAISON IMPORTÉE",
        "tutorials_text_5": """Après une acquisition, appuyez sur Ajouter courbe :
  → Sélectionnez un fichier Excel/CSV déjà exporté.
  → La courbe importée s'affiche en comparaison.""",
        "tutorials_text_6_title": "6. ACQUISITION + ANALYSE + IMPORTÉE",
        "tutorials_text_6": """Combinez les méthodes 2 et 5 :
  → Tracez, importez une référence.
  → Ajoutez des points sur n'importe quelle courbe.""",
        "tutorials_manage_text": """GESTION AVANCÉE (bouton Gérer)
Recolorer, supprimer courbes individuelles et points.
Effacer la courbe principale sans toucher aux archivées.
Effacer tout (courbes + points) en un clic.""",
        # Guide
        "guide_banner_text": "🎯 Guide actif – Suivez le bouton clignotant. ",
        "guide_disable": "✕ Désactiver le guide",
        "guide_popup_text": "Le guide interactif va faire clignoter les boutons à suivre.\nVous pouvez le désactiver à tout moment via le bandeau en haut.",
        "guide_popup_title": "Guide interactif",
        # Welcome
        "welcome_title": "Bienvenue dans labCE",
        "welcome_prereq_title": "Prérequis",
        "welcome_prereq_text": """Pour utiliser labCE, vous devez avoir installé :
• NI MAX (version 14.5 ou supérieure)

Procédure de mise en route :
1. Branchez le câble USB A de la carte d'acquisition NI.
2. Allumez la carte (bouton arrière droit).
3. Allumez le Kistler.
4. Appuyez sur le bouton vert du Kistler pour remettre la force à 0.""",
        "welcome_conn_title": "Connexion",
        "welcome_conn_text": """Dans la partie Connexion :
• Appuyez sur Rafraîchir pour détecter la carte NI.
• Appuyez sur Connecter la carte pour obtenir la pastille verte.""",
        "welcome_ranges_title": "Plages de mesure Kistler 9217A",
        "welcome_push": "Compression", "welcome_pull": "Traction",
        "welcome_params_title": "Paramètres",
        "welcome_params_text": """Dans la partie Paramètres :
• Choisissez la plage Kistler.
• Ajustez la sensibilité course si nécessaire (défaut 1 mm/pas).
• Appuyez sur Appliquer pré-config (le cadre passe au vert).
• Testez votre capteur dans "Test Capteur" et votre course dans "Test Banc".""",
        "welcome_test_name": "Nom de l'essai :",
        "welcome_tutorials_title": "Tutoriels interactifs",
        "welcome_tutorials_text": "Première utilisation ? Appuyez sur le bouton 📖 Tutoriels dans le logiciel.\nChoisissez un type d'acquisition et laissez-vous guider pas à pas\npar le clignotement des boutons à suivre.",
        "welcome_start": "🚀 Commencer",
        # Messages
        "msg_tare_ok_title": "Tare", "msg_tare_ok_body": "Tare appliquée avec succès.",
        "msg_conn_warning_title": "Connexion", "msg_conn_warning_body": "NI désactivé ou module manquant.",
        "msg_export_warn_title": "Export", "msg_export_warn_nodata": "Aucune donnée à exporter.",
        "msg_export_warn_nodir": "Choisissez un dossier.",
        "msg_export_ok_title": "Export réussi", "msg_export_ok_body": "Essai enregistré :\n{path}",
        "msg_acq_err_title": "Erreur acquisition",
        "invalid_sensitivity_title": "Sensibilité invalide", "invalid_sensitivity_body": "La sensibilité doit être positive.",
        "msg_new_measure_running": "Arrêtez l'acquisition avant.",
        "msg_new_measure_save": "Sauvegarder les données actuelles avant ?\n\nOui = Sauvegarder\nNon = Effacer\nAnnuler = Ne rien faire",
        "msg_numeric_error": "Veuillez entrer une valeur numérique valide.",
        "msg_no_data_curve": "Aucune donnée disponible pour cette courbe.",
        "msg_out_of_range": "Valeur hors de la plage des données.",
        "msg_curve_no_data": "Cette courbe ne contient pas les données nécessaires.",
        "msg_point_added": "Point ajouté avec succès.",
        "msg_confirm_delete": "Confirmation",
        "curve_name_prompt": "Nom de la courbe :",
        # Offset post-acquisition
        "offset_detected_title": "Offset initial détecté",
        "offset_detected_msg": "Un offset initial a été détecté sur les données :\n{details}\n\nSouhaitez-vous le corriger automatiquement ?",
        # Plot
        "plot_x_time": "Temps (s)", "plot_y_effort": "Effort (N)", "plot_y_course": "Course (mm)",
        "plot_title_effort_time": "{title} – Effort / Temps",
        "plot_title_course_time": "{title} – Course / Temps",
        "plot_title_effort_course": "{title} – Effort / Course",
        "legend_effort": "Effort (N)", "legend_course": "Course (mm)", "legend_essai": "Essai",
        # Tooltips
        "tooltip_tare": "Réinitialise les capteurs à zéro",
        "tooltip_start": "Démarre l'acquisition",
        "tooltip_stop": "Arrête l'acquisition en cours",
        "tooltip_new_measure": "Conserve la courbe et prépare une nouvelle mesure",
        "tooltip_export": "Exporte les données en Excel",
        "tooltip_save_figure": "Sauvegarde le graphique en PNG",
        "tooltip_choose_dir": "Choisir le dossier de sauvegarde",
        "tooltip_add_curve": "Importe une courbe depuis Excel ou CSV",
        "tooltip_add_point_course": "Ajoute un point à une valeur de course",
        "tooltip_add_point_effort": "Ajoute un point à une valeur d'effort",
        "tooltip_manage": "Gérer courbes et points du graphique",
        "tooltip_smooth": "Lisser la courbe sélectionnée",
        "tooltip_lang": "Basculer français / anglais",
        "tooltip_help": "Afficher l'aide",
        "tooltip_tutorials": "Tutoriels d'utilisation",
        "tooltip_about": "Informations sur le logiciel",
        "tooltip_refresh": "Rafraîchir la liste des périphériques",
        "tooltip_test_conn": "Connecter la carte NI",
        "tooltip_preconfig": "Appliquer la pré-configuration",
    },

    "en": {
        "app_title": "labCE",
        "lang_button": "🌐 EN",
        "mode_full": "Full test", "mode_sensor": "Sensor Test", "mode_bench": "Bench Test",
        "conn_title": "Connection",
        "btn_test": "Connect card",
        "device_label": "Connection card",
        "status_not_connected": "❌ Not connected",
        "status_ni_unavailable": "⚠️ NI unavailable",
        "status_connected_fmt": "🟢 {dev} connected",
        "params_title": "Parameters",
        "preconfig_title": "Pre-configuration",
        "range_label": "Measurement range:",
        "sens_course_label": "Stroke sens.:",
        "apply_preconfig": "Apply pre-config",
        "preconfig_info_title": "Pre-configuration info",
        "preconfig_warning_title": "Pre-configuration",
        "preconfig_warning_text": "Please apply the pre-configuration before starting acquisition.",
        "kistler_popup_title": "⚠️ Kistler amp change",
        "kistler_popup_text": "Selected range exceeds 10 N.\n\nPlease change the pre-configuration on the Kistler 9217A amplifier\nbefore starting acquisition.",
        "acq_title": "Acquisition",
        "btn_tare": "Tare",
        "btn_start": "Start",
        "btn_stop": "Stop",
        "btn_new_measure": "New measurement",
        "acquisition_active": "● ACQUISITION ACTIVE",
        "acquisition_idle": "",
        "start_popup_title": "Measurement preparation",
        "start_popup_text": "Before starting:\n\n1. Press the MEASURE button (green) on the\n   Kistler amplifier twice to reset the force.\n\n2. Check that the Kistler display shows 0.0 N.\n\nClick OK to start acquisition.",
        "actions_title": "Actions",
        "btn_excel": "Export Excel",
        "btn_save_figure": "Save figure",
        "no_dir_selected": "No folder selected",
        "export_open_question": "Open exported file?",
        "export_open_title": "File exported",
        "analysis_title": "Analysis",
        "btn_add_curve": "Add curve",
        "btn_add_point_course": "+ point (stroke)",
        "btn_add_point_effort": "+ point (force)",
        "btn_manage": "Manage",
        "btn_smooth": "Smooth curve",
        "smooth_title": "Curve smoothing",
        "smooth_select_curve": "Curve to smooth:",
        "smooth_apply": "Apply",
        "smooth_done": "Smoothing applied (optimal degree: {deg})",
        "graph_title": "Visualization",
        "points_panel_title": "Points",
        "select_curve_label": "Select curve:",
        "main_curve_label": "Main curve",
        "value_label_course": "Stroke value (mm):",
        "value_label_effort": "Force value (N):",
        "color_optional": "Color (optional)",
        "btn_apply": "Apply",
        "btn_close": "Close",
        "btn_choose_color": "Choose",
        "add_point_title_course": "Add point (stroke)",
        "add_point_title_effort": "Add point (force)",
        "multi_point_title": "Multiple points detected",
        "multi_point_text": "Multiple points match this value on the curve.\nThe graph has zoomed to show them. Select the one you want to add:",
        "manage_title": "Graph elements management",
        "section_curves": "CURVES",
        "section_points": "MEASUREMENT POINTS",
        "main_curve_current": "Main Curve (current measurement)",
        "imported_curves": "Imported / Archived Curves",
        "btn_recolor": "Recolor",
        "btn_delete": "Delete",
        "btn_delete_all": "Delete all",
        "btn_clear_main": "Clear main",
        "msg_clear_main_confirm": "Clear main curve (last measurement)?\nArchived curves will not be affected.",
        "btn_reset_all_full": "Clear all curves and points",
        "msg_reset_all_confirm": "Clear ALL curves and points from the graph?",
        "legend_points": "🔵 = Stroke  |  🔺 = Force",
        "color_label": "Color:",
        "timer_prefix": "Time:",
        "about_title": "About labCE",
        "about_button": "About",
        "about_version": f"Version: {SOFTWARE_VERSION}",
        "about_author": f"Created by {AUTHOR}",
        "about_close": "Close",
        "help_button": "Help",
        "help_title": "Help - labCE",
        "help_text": """labCE User Guide {version}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔌 CONNECTION
Connect the USB A cable from the NI card to your PC.
Turn on the NI card and the Kistler.
Click Refresh then Connect card to get the green indicator.

⚙️ PARAMETERS
Choose your Kistler measurement range.
If range exceeds 10 N, a popup reminds you to change the amp.
Force sensitivity is fixed at 1 N/V.
Stroke sensitivity is adjustable (default 1 mm/step).
Frequency is fixed at 50 Hz.
Press Apply pre-config (frame turns green).

🎬 ACQUISITION
Tare → Start (Kistler popup) → Stop.
The Manage button in Analysis lets you clear the main curve
or all curves.

💾 ACTIONS
Export Excel: 2 sheets (Data + Force/Stroke XY).
Filename shows the number of curves.

🔬 ANALYSIS
+ point (stroke/force): if multiple points detected,
the software zooms and lets you choose.
Smooth curve: polynomial regression.
Manage: modify colors, delete curves/points.
""",
        "tutorials_button": "Tutorials",
        "tutorials_title": "Tutorials - labCE",
        "tutorial_go_button": "▶ Perform this acquisition",
        "tutorials_text_1_title": "1. STANDARD ACQUISITION",
        "tutorials_text_1": """1. Connect the NI card.
2. Apply pre-configuration (frame turns green).
3. Perform Tare.
4. Start acquisition.
5. Stop, choose folder, export.""",
        "tutorials_text_2_title": "2. ACQUISITION + ANALYSIS",
        "tutorials_text_2": """Same as standard acquisition.
Before exporting:
  • + point (stroke) to find force at a distance.
  • + point (force) to find distance at a force.
If multiple points found, software zooms to let you choose.""",
        "tutorials_text_3_title": "3. ACQUISITION + MEASURED COMPARISON",
        "tutorials_text_3": """After acquisition, press New measurement:
  → Curve is archived with a new color.
  → Timer resets. Restart acquisition.""",
        "tutorials_text_4_title": "4. ACQUISITION + ANALYSIS + COMPARISON",
        "tutorials_text_4": """Combine methods 2 and 3:
  → Trace, add points, then New measurement.
  → Trace second curve and add points.""",
        "tutorials_text_5_title": "5. ACQUISITION + IMPORTED COMPARISON",
        "tutorials_text_5": """After acquisition, press Add curve:
  → Select previously exported Excel/CSV file.
  → Imported curve displays alongside.""",
        "tutorials_text_6_title": "6. ACQUISITION + ANALYSIS + IMPORTED",
        "tutorials_text_6": """Combine methods 2 and 5:
  → Trace, import a reference.
  → Add points on any curve.""",
        "tutorials_manage_text": """ADVANCED MANAGEMENT (Manage button)
Recolor, delete individual curves and points.
Clear main curve without affecting archived ones.
Clear all (curves + points) in one click.""",
        "guide_banner_text": "🎯 Guide active – Follow the blinking button. ",
        "guide_disable": "✕ Disable guide",
        "guide_popup_text": "The interactive guide will blink buttons to follow.\nYou can disable it anytime via the banner at the top.",
        "guide_popup_title": "Interactive guide",
        "welcome_title": "Welcome to labCE",
        "welcome_prereq_title": "Prerequisites",
        "welcome_prereq_text": """To use labCE, you must have installed:
• NI MAX (version 14.5 or higher)

Setup procedure:
1. Connect the USB A cable from the NI acquisition card.
2. Turn on the card (back right button).
3. Turn on the Kistler.
4. Press green Kistler button to zero the force.""",
        "welcome_conn_title": "Connection",
        "welcome_conn_text": """In the Connection section:
• Press Refresh to detect the NI card.
• Press Connect card to get the green indicator.""",
        "welcome_ranges_title": "Kistler 9217A measurement ranges",
        "welcome_push": "Compression", "welcome_pull": "Traction",
        "welcome_params_title": "Parameters",
        "welcome_params_text": """In the Parameters section:
• Choose Kistler range.
• Adjust stroke sensitivity if needed (default 1 mm/step).
• Press Apply pre-config (frame turns green).
• Test sensor in "Sensor Test" and stroke in "Bench Test".""",
        "welcome_test_name": "Test name:",
        "welcome_tutorials_title": "Interactive tutorials",
        "welcome_tutorials_text": "First time using labCE? Press the 📖 Tutorials button in the software.\nChoose an acquisition type and follow the step-by-step guide\nwith blinking buttons showing you what to do.",
        "welcome_start": "🚀 Start",
        "msg_tare_ok_title": "Tare", "msg_tare_ok_body": "Tare applied successfully.",
        "msg_conn_warning_title": "Connection", "msg_conn_warning_body": "NI disabled or module missing.",
        "msg_export_warn_title": "Export", "msg_export_warn_nodata": "No data to export.",
        "msg_export_warn_nodir": "Choose a folder.",
        "msg_export_ok_title": "Export successful", "msg_export_ok_body": "Test saved:\n{path}",
        "msg_acq_err_title": "Acquisition error",
        "invalid_sensitivity_title": "Invalid sensitivity", "invalid_sensitivity_body": "Sensitivity must be positive.",
        "msg_new_measure_running": "Stop acquisition first.",
        "msg_new_measure_save": "Save current data?\n\nYes = Save\nNo = Clear\nCancel = Do nothing",
        "msg_numeric_error": "Please enter a valid numeric value.",
        "msg_no_data_curve": "No data available for this curve.",
        "msg_out_of_range": "Value out of data range.",
        "msg_curve_no_data": "This curve does not contain required data.",
        "msg_point_added": "Point added successfully.",
        "msg_confirm_delete": "Confirmation",
        "curve_name_prompt": "Curve name:",
        # Offset post-acquisition
        "offset_detected_title": "Initial offset detected",
        "offset_detected_msg": "An initial offset was detected in the data:\n{details}\n\nDo you want to correct it automatically?",
        "plot_x_time": "Time (s)", "plot_y_effort": "Force (N)", "plot_y_course": "Stroke (mm)",
        "plot_title_effort_time": "{title} – Force / Time",
        "plot_title_course_time": "{title} – Stroke / Time",
        "plot_title_effort_course": "{title} – Force / Stroke",
        "legend_effort": "Force (N)", "legend_course": "Stroke (mm)", "legend_essai": "Test",
        "tooltip_tare": "Zero the sensors", "tooltip_start": "Start acquisition",
        "tooltip_stop": "Stop current acquisition",
        "tooltip_new_measure": "Keep curve and prepare new measurement",
        "tooltip_export": "Export data to Excel",
        "tooltip_save_figure": "Save graph as PNG",
        "tooltip_choose_dir": "Choose save folder",
        "tooltip_add_curve": "Import curve from Excel or CSV",
        "tooltip_add_point_course": "Add point at a stroke value",
        "tooltip_add_point_effort": "Add point at a force value",
        "tooltip_manage": "Manage graph curves and points",
        "tooltip_smooth": "Smooth selected curve",
        "tooltip_lang": "Switch French / English",
        "tooltip_help": "Show help", "tooltip_tutorials": "Usage tutorials",
        "tooltip_about": "Software information",
        "tooltip_refresh": "Refresh NI device list",
        "tooltip_test_conn": "Connect NI card",
        "tooltip_preconfig": "Apply pre-configuration",
    },
}