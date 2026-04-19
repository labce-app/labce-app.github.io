# 📦 INSTALLATION ET UTILISATION - labCE v4.2

## 🎯 Deux Options d'Installation

### Option 1 : Version Modulaire (Recommandé ✅)

**Avantages** : Code organisé, facile à maintenir, meilleure performance

**Structure des fichiers** :
```
ton_projet/
├── config.py
├── data_manager.py
├── acquisition.py
├── plotting.py
├── export_excel.py
├── translations.py
├── labce_main_COMPLET.py   ← Le fichier principal
├── config.ini (optionnel)
└── logo_labce.ico/.png (optionnel)
```

**Étapes** :
1. Télécharge TOUS les fichiers .py ci-dessus
2. Place-les dans le même dossier
3. Installe les dépendances :
```bash
pip install numpy matplotlib openpyxl nidaqmx pillow
```
4. Lance l'application :
```bash
python labce_main_COMPLET.py
```

---

### Option 2 : Version Standalone (1 seul fichier)

**Avantages** : Un seul fichier à gérer

**Inconvénients** : Fichier très long (~2500 lignes), moins facile à maintenir

**Ce fichier sera créé si nécessaire** - dis-moi si tu le veux !

---

## 🔧 Configuration (config.ini)

Crée un fichier `config.ini` dans le même dossier :

```ini
[NI]
device = Dev1

[Channels]
effort_ai = ai0
course_ai = ai1

[Acquisition]
frequency_hz = 100

[Sensors]
sensitivity_effort_nv = 1.0
sensitivity_course_mmv = 10.0

[UI]
default_mode = full
```

---

## 🚀 Premier Lancement

1. **Sans matériel NI** : Le logiciel démarre en mode simulation
2. **Avec matériel NI** :
   - Connecte ton périphérique NI-DAQ
   - Clique sur "🔄 Rafraîchir" pour détecter
   - Clique sur "Tester connexion"

---

## 📊 Utilisation Rapide

### Acquisition Simple
1. Sélectionne le device NI
2. Teste la connexion
3. Choisis un dossier de sauvegarde
4. Clique sur "▶️ Démarrer"
5. Clique sur "⏹ Arrêter"
6. Clique sur "📁 Export Excel"

### Import de Courbes
1. Clique sur "➕ Ajouter courbe"
2. Sélectionne un fichier Excel ou CSV
3. La courbe s'affiche automatiquement

### Ajout de Points
1. Clique sur "➕ Point (course)" ou "➕ Point (effort)"
2. Entre une valeur
3. Le point est interpolé sur TOUTES les courbes

---

## 🐛 Dépannage

### Erreur "Module not found"
```bash
pip install --upgrade numpy matplotlib openpyxl pillow
# Pour NI-DAQmx (seulement si tu as le matériel) :
pip install nidaqmx
```

### Erreur "NI-DAQmx non disponible"
C'est normal si tu n'as pas de périphérique NI. Le logiciel fonctionne quand même pour visualiser des données.

### Le graphique est lent
Vérifie que tu utilises bien la version corrigée (v4.2). La performance devrait être 10x meilleure.

### Les données ne s'enregistrent pas
Vérifie que tu as bien choisi un dossier de sauvegarde avec "📂 Choisir emplacement".

---

## 📝 Fichiers Générés

### Logs
- `labce.log` : Tous les événements sont enregistrés ici

### Exports
- `Date_Essai_comparaison.xlsx` : Export complet avec graphiques
- `Date_Essai_autosave_timestamp.xlsx` : Sauvegardes automatiques

---

## 🎓 Pour Aller Plus Loin

- **README.md** : Documentation technique complète
- **GUIDE_MIGRATION.md** : Guide d'utilisation détaillé
- **CORRECTIONS_DETAILLEES.md** : Explication de toutes les améliorations

---

## 💡 Conseils

1. **Active l'autosave** pour ne jamais perdre de données
2. **Utilise les logs** (`labce.log`) pour debugger
3. **Lis le README.md** pour comprendre l'architecture
4. **Personnalise config.ini** selon tes besoins

---

## ✅ Checklist de Vérification

Avant de commencer :
- [ ] Tous les fichiers .py dans le même dossier
- [ ] Dépendances installées (`pip install ...`)
- [ ] config.ini créé (optionnel)
- [ ] Device NI connecté (si applicable)

---

**Tu es prêt ! Lance `python labce_main_COMPLET.py` et c'est parti ! 🚀**
