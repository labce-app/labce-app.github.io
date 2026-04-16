"""
Génère version.json à partir des informations d'une GitHub Release.
Appelé automatiquement par le workflow release.yml.

Format attendu des notes de release (markdown) :
  ## Nouveautés
  - Nouvelle fonctionnalité X
  - Nouvelle fonctionnalité Y

  ## Corrections
  - Correction bug Z

  ## Améliorations
  - Amélioration W
"""
import json
import os
import re

# ─── Variables injectées par GitHub Actions ───
raw_version = os.environ.get("GH_VERSION", "0.0").lstrip("v")
raw_date    = os.environ.get("GH_DATE",    "")[:10]
body        = os.environ.get("GH_BODY",    "")
repo        = os.environ.get("GH_REPO",    "")
size_bytes  = int(os.environ.get("GH_SIZE", "0"))

size_mb = round(size_bytes / 1024 / 1024) if size_bytes else 0

# ─── URL de téléchargement direct de l'exe ───
exe_url = f"https://github.com/{repo}/releases/latest/download/labCE_app.exe"

# ─── Parsing du changelog markdown ───
TYPE_MAP = {
    "nouveau":      "new",
    "nouveauté":    "new",
    "ajout":        "new",
    "new":          "new",
    "add":          "new",
    "feat":         "new",
    "correction":   "fix",
    "correctif":    "fix",
    "fix":          "fix",
    "bug":          "fix",
    "amélioration": "improve",
    "amélior":      "improve",
    "improve":      "improve",
    "perf":         "improve",
    "optimis":      "improve",
}

def detect_type(heading: str) -> str:
    h = heading.lower()
    for key, val in TYPE_MAP.items():
        if key in h:
            return val
    return "new"

changelog = []
current_type = "new"

for line in body.splitlines():
    s = line.strip()
    if s.startswith("##"):
        heading = re.sub(r"^#+\s*", "", s)
        current_type = detect_type(heading)
    elif s.startswith(("- ", "* ", "• ")):
        text = s[2:].strip()
        if text:
            changelog.append({"type": current_type, "text": text})

if not changelog:
    changelog = [{"type": "new", "text": "Voir les notes de version complètes sur GitHub"}]

# ─── Écriture du fichier ───
data = {
    "version":      raw_version,
    "date":         raw_date,
    "exe_filename": "labCE_app.exe",
    "exe_url":      exe_url,
    "package_url":  exe_url,
    "size_mb":      size_mb,
    "changelog":    changelog,
    "gh_release":   f"https://github.com/{repo}/releases/latest",
}

with open("version.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"✅ version.json généré : v{raw_version} ({raw_date})")
print(f"   {len(changelog)} entrée(s) de changelog")
print(f"   exe_url : {exe_url}")
