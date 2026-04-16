# labCE — Site de présentation & distribution

Site web statique pour présenter et distribuer **labCE v5.3**, logiciel d'acquisition de données mécaniques en temps réel.

- **Hébergement** : GitHub Pages (gratuit, URL stable)
- **Distribution** : GitHub Releases (jusqu'à 2 GB par asset — pour les `.exe` et `.zip`)
- **Mises à jour** : automatiques via GitHub Actions à chaque nouvelle Release

---

## Structure du repo

```
├── index.html               ← Site complet (HTML + CSS + JS, tout-en-un)
├── version.json             ← Généré automatiquement par GitHub Actions
├── logo.png                 ← Logo labCE (optionnel)
├── .github/
│   ├── workflows/
│   │   └── release.yml      ← Workflow déclenchement automatique
│   └── scripts/
│       └── gen_version.py   ← Script de génération version.json
└── .gitignore               ← Exclut .exe, .zip, .iso du repo
```

> **Note** : les fichiers lourds (`.exe`, `.zip`) ne sont **pas** stockés dans le repo Git.  
> Ils sont distribués via les **GitHub Releases** (pièces jointes d'assets).

---

## Première mise en ligne

Voir le guide complet : **[GUIDE_GITHUB.md](GUIDE_GITHUB.md)**

En résumé :
1. Créer un repo GitHub public
2. Pousser ce dossier sur la branche `main`
3. Settings → Pages → Source : `main` / `/ (root)` → Save
4. Dans `index.html`, configurer `const GH = { owner: 'votre-username', repo: 'labce' }`
5. Créer une Release GitHub avec `labCE_app.exe` en pièce jointe

---

## Publier une mise à jour (workflow normal)

1. Aller sur **github.com → votre repo → Releases → New release**
2. Renseigner le tag (ex. `v5.4`) et le titre
3. Écrire les notes de version en **Markdown structuré** :

```markdown
## Nouveautés
- Fonctionnalité X ajoutée
- Interface améliorée

## Corrections
- Bug Y corrigé

## Améliorations
- Performance temps réel ×2
```

4. Joindre `labCE_app.exe` en asset (glisser-déposer)
5. Cliquer **Publish release**

→ GitHub Actions se déclenche, génère `version.json` et le commite sur `main`.  
→ Le site se met à jour automatiquement en **moins de 2 minutes**.

---

## Sections reconnues dans les notes de release

| Titre de section (Markdown)             | Badge affiché  |
|-----------------------------------------|----------------|
| `## Nouveautés` / `## New` / `## Feat`  | 🟡 Nouveau     |
| `## Corrections` / `## Fix` / `## Bug`  | 🔴 Correction  |
| `## Améliorations` / `## Improve`       | 🔵 Amélio.     |
