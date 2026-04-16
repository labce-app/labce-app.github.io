# Guide — Mettre labCE sur GitHub Pages

Ce guide explique comment héberger le site labCE sur GitHub Pages et activer les mises à jour automatiques via GitHub Actions. Il faut environ **15 minutes** pour la première mise en place.

---

## Prérequis

- Un compte GitHub (gratuit sur github.com)
- Git installé sur votre PC, OU utilisation de l'interface web GitHub (pas besoin de ligne de commande)

---

## Étape 1 — Créer le repo GitHub

1. Aller sur **github.com** et se connecter
2. Cliquer **New repository** (bouton vert en haut à droite)
3. Renseigner :
   - **Repository name** : `labce` (en minuscules, pas d'espace)
   - **Visibility** : Public ← obligatoire pour GitHub Pages gratuit
   - Laisser les autres options par défaut
4. Cliquer **Create repository**

> **Votre nom d'utilisateur GitHub** sera noté `{owner}` dans ce guide.  
> Exemple : si votre URL est `github.com/jean-dupont`, votre owner est `jean-dupont`.

---

## Étape 2 — Uploader les fichiers

### Option A — Via l'interface web (plus simple, pas de Git requis)

1. Sur la page du repo, cliquer **uploading an existing file** (ou **Add file → Upload files**)
2. Glisser-déposer tous les fichiers du dossier site :
   - `index.html`
   - `version.json`
   - `README.md`
   - `logo.png` (si disponible)
   - Le dossier `.github/` avec ses sous-dossiers **workflows/** et **scripts/**
3. Laisser le message de commit par défaut
4. Cliquer **Commit changes**

> ⚠️ Ne pas uploader les `.exe`, `.zip`, `.iso` — ils vont dans les Releases (étape 4).

### Option B — Via Git (ligne de commande)

```bash
cd "C:\Users\kuhli\Downloads\labCE - Copy\labCE - Copy"
git init
git remote add origin https://github.com/{owner}/labce.git
git add index.html version.json README.md GUIDE_GITHUB.md .gitignore .github/
git commit -m "init: site labCE v5.3"
git branch -M main
git push -u origin main
```

---

## Étape 3 — Activer GitHub Pages

1. Dans votre repo, cliquer **Settings** (onglet en haut)
2. Dans le menu gauche, cliquer **Pages**
3. Sous **Source**, sélectionner :
   - **Branch** : `main`
   - **Folder** : `/ (root)`
4. Cliquer **Save**

GitHub Pages génère alors une URL de la forme :
```
https://{owner}.github.io/labce/
```

⏳ Attendre 1-2 minutes, puis ouvrir cette URL. Le site est en ligne.

---

## Étape 4 — Configurer index.html

1. Ouvrir `index.html` dans un éditeur de texte (Notepad, VS Code, etc.)
2. Chercher (Ctrl+F) : `const GH`
3. Vous verrez cette ligne tout en haut du bloc `<script>` :

```javascript
const GH = { owner: '', repo: 'labce' };
```

4. Remplacer `''` par votre identifiant GitHub entre guillemets simples :

```javascript
const GH = { owner: 'jean-dupont', repo: 'labce' };
```

5. Sauvegarder le fichier et le re-uploader sur GitHub (même procédure qu'Étape 2)

---

## Étape 5 — Créer la première Release

1. Dans votre repo, cliquer **Releases** (panneau à droite) ou aller dans **Code → Releases**
2. Cliquer **Create a new release** (ou **Draft a new release**)
3. Renseigner :
   - **Choose a tag** : taper `v5.3` → cliquer **Create new tag: v5.3**
   - **Release title** : `labCE v5.3`
   - **Description** : écrire les notes de version en Markdown structuré (voir format ci-dessous)
4. Dans la section **Assets**, cliquer **Attach binaries** et déposer `labCE_app.exe`
5. Cliquer **Publish release**

→ GitHub Actions se déclenche automatiquement (vérifiable dans l'onglet **Actions** du repo).  
→ Après ~1 minute, `version.json` est mis à jour et le site affiche la version correcte.

---

## Format des notes de release (Markdown)

Le workflow GitHub Actions analyse automatiquement les notes de release pour construire le changelog affiché sur le site. Il faut utiliser des titres de sections `##` reconnus :

```markdown
## Nouveautés
- Acquisition hybride NI-DAQmx + encodeur linéaire
- Export Excel multi-courbes avec graphiques

## Corrections
- Performance graphique temps réel améliorée
- Correction zéro automatique sur les deux canaux

## Améliorations
- Déploiement multi-PC via config.ini
- Installateur NI-DAQmx silencieux
```

**Sections reconnues :**

| Section (FR ou EN)                                | Type    |
|---------------------------------------------------|---------|
| `Nouveautés`, `Nouveau`, `Ajout`, `New`, `Feat`   | Nouveau |
| `Corrections`, `Correctif`, `Fix`, `Bug`          | Fix     |
| `Améliorations`, `Amélio`, `Improve`, `Perf`      | Amélio. |

> Les items commençant par `- `, `* ` ou `• ` sont automatiquement extraits.

---

## Publier une mise à jour (workflow répété)

Pour chaque nouvelle version :

1. **Compiler** le nouvel `labCE_app.exe` avec PyInstaller
2. Aller sur github.com → votre repo → **Releases → New release**
3. Nouveau tag : `v5.4` (ou la version suivante)
4. Écrire les notes Markdown structurées
5. Joindre `labCE_app.exe` en asset
6. Cliquer **Publish release**

C'est tout. GitHub Actions fait le reste. Le site est mis à jour en < 2 min.

---

## Vérifier que le workflow a bien tourné

1. Dans votre repo, cliquer l'onglet **Actions**
2. Vous devez voir un workflow **🚀 Release — Mise à jour version.json** avec un ✅ vert
3. Si un ❌ rouge apparaît, cliquer dessus pour voir les logs d'erreur

**Erreur fréquente** : le fichier asset ne s'appelle pas exactement `labCE_app.exe` (sensible à la casse).  
→ Vérifier que le fichier joint lors de la Release s'appelle bien `labCE_app.exe`.

---

## Mettre à jour le QR Code

1. Ouvrir le site → onglet **Présentation** → section **QR Code**
2. Entrer l'URL GitHub Pages : `https://{owner}.github.io/labce/`
3. Cliquer **Générer**
4. Faire un clic-droit sur l'image → **Enregistrer sous** → imprimer et plastifier pour le banc
