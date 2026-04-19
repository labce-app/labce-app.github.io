# ============================================================
#  labCE v5.3 - Installateur automatique 100% autonome
#  Auto-élévation admin, NIPM bootstrap, feed offline, raccourci
# ============================================================
#Requires -Version 5.1

$APP_NAME    = "labCE"
$APP_VERSION = "v5.3"
$EXE_NAME    = "labCE_app.exe"

# --- Auto-élévation si non admin ---
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
        ).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    $args_str = '-ExecutionPolicy Bypass -File "{0}"' -f $MyInvocation.MyCommand.Path
    Start-Process powershell -Verb RunAs -ArgumentList $args_str
    exit
}

$ScriptDir      = Split-Path -Parent $MyInvocation.MyCommand.Path
$FeedDir        = Join-Path $ScriptDir "NI-DAQmx\feed"
$BootstrapDir   = Join-Path $ScriptDir "NI-DAQmx\nipm_bootstrap"
# preinstall\Install.exe est le vrai installateur silencieux de NIPM
# (bin\Install.exe est le wrapper GUI — flags différents)
$BootstrapBin   = Join-Path $BootstrapDir "preinstall\Install.exe"

Clear-Host
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  $APP_NAME $APP_VERSION  -  Installation automatique"    -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================
# ÉTAPE 1 : Trouver nipkg.exe (NI Package Manager CLI)
# ============================================================
Write-Host "[1/4] Recherche de NI Package Manager..." -ForegroundColor Yellow

function Find-Nipkg {
    $candidates = @(
        "C:\Program Files\National Instruments\NI Package Manager\nipkg.exe",
        "C:\Program Files (x86)\National Instruments\NI Package Manager\nipkg.exe"
    )
    foreach ($c in $candidates) { if (Test-Path $c) { return $c } }
    # Recherche élargie
    $found = Get-ChildItem "C:\Program Files*\National Instruments" -Recurse -Filter "nipkg.exe" -ErrorAction SilentlyContinue |
             Select-Object -First 1
    if ($found) { return $found.FullName }
    return $null
}

$nipkg = Find-Nipkg

if ($nipkg) {
    Write-Host "   [OK] nipkg.exe trouvé : $nipkg" -ForegroundColor Green
} else {
    # ============================================================
    # ÉTAPE 1b : NIPM absent → essayer le bootstrap s'il est présent
    # ============================================================
    Write-Host "   NI Package Manager absent." -ForegroundColor Yellow

    if (Test-Path $BootstrapBin) {
        Write-Host "   Lancement du bootstrap NIPM..." -ForegroundColor Yellow
        Write-Host "   Cela peut prendre 5 à 10 minutes..." -ForegroundColor Gray

        $proc = Start-Process -FilePath $BootstrapBin `
            -ArgumentList "--passive", "--accept-eulas" `
            -WorkingDirectory (Split-Path $BootstrapBin) `
            -Wait -PassThru

        Start-Sleep -Seconds 3
        $nipkg = Find-Nipkg
        if ($nipkg) {
            Write-Host "   [OK] NIPM installé : $nipkg" -ForegroundColor Green
        } else {
            Write-Host "   [ATTENTION] NIPM bootstrap terminé mais nipkg.exe introuvable." -ForegroundColor Yellow
        }
    } else {
        # Bootstrap absent : nipkg reste $null, on continue sans lui.
        # L'étape 2 utilisera directement l'installateur .exe si disponible.
        Write-Host "   Bootstrap NIPM non inclus dans ce package — NI-DAQmx sera" -ForegroundColor Gray
        Write-Host "   installé via l'installateur .exe s'il est présent." -ForegroundColor Gray
    }
}

# ============================================================
# ÉTAPE 2 : Vérifier si NI-DAQmx est déjà installé
# ============================================================
Write-Host ""
Write-Host "[2/4] Vérification NI-DAQmx..." -ForegroundColor Yellow

$ni_installed = $false
$regPaths = @(
    "HKLM:\SOFTWARE\National Instruments\NI-DAQmx\CurrentVersion",
    "HKLM:\SOFTWARE\WOW6432Node\National Instruments\NI-DAQmx\CurrentVersion"
)
foreach ($reg in $regPaths) {
    if (Test-Path $reg) {
        try { $ver = (Get-ItemProperty $reg).ProductVersion } catch { $ver = "?" }
        if ($ver) { $ni_installed = $true; Write-Host "   [OK] NI-DAQmx déjà installé ($ver) — installation ignorée." -ForegroundColor Green; break }
    }
}

if (-not $ni_installed) {
    Write-Host "   NI-DAQmx non trouvé. Recherche d'un installateur..." -ForegroundColor Yellow

    $NiDaqmxDir = Join-Path $ScriptDir "NI-DAQmx"

    # --- Priorité 1 : ISO offline (Install.exe intégré) ---
    $niIso = $null
    if (Test-Path $NiDaqmxDir) {
        $niIso = Get-ChildItem $NiDaqmxDir -Filter "*.iso" -ErrorAction SilentlyContinue |
                 Select-Object -First 1
    }

    # --- Priorité 2 : installateur .exe classique ---
    $niExe = $null
    if (-not $niIso -and (Test-Path $NiDaqmxDir)) {
        $niExe = Get-ChildItem $NiDaqmxDir -Filter "*.exe" -ErrorAction SilentlyContinue |
                 Select-Object -First 1
    }

    # --- Priorité 3 : package .nipkg via nipkg.exe ---
    $niPkg = $null
    if (-not $niIso -and -not $niExe -and (Test-Path $NiDaqmxDir)) {
        $niPkg = Get-ChildItem $NiDaqmxDir -Filter "*.nipkg" -ErrorAction SilentlyContinue |
                 Select-Object -First 1
    }

    if ($niIso) {
        Write-Host "   ISO trouvée : $($niIso.Name)" -ForegroundColor Gray
        Write-Host "   Montage de l'image disque..." -ForegroundColor Yellow
        try {
            $mountResult = Mount-DiskImage -ImagePath $niIso.FullName -PassThru -ErrorAction Stop
            $driveLetter  = ($mountResult | Get-Volume).DriveLetter
            $setupExe     = "${driveLetter}:\Install.exe"

            if (Test-Path $setupExe) {
                Write-Host "   Installation NI-DAQmx en cours... (5 à 20 min)" -ForegroundColor Yellow
                Write-Host "   (Une fenêtre de progression NI peut apparaître)" -ForegroundColor Gray
                $proc = Start-Process -FilePath $setupExe `
                    -ArgumentList "--passive", "--accept-eulas", "--no-cancel" `
                    -WorkingDirectory "${driveLetter}:\" `
                    -Wait -PassThru
                $installCode = if ($proc) { $proc.ExitCode } else { -1 }
            } else {
                Write-Host "   [ERREUR] Install.exe introuvable dans l'ISO." -ForegroundColor Red
                $installCode = -1
            }
        } catch {
            Write-Host "   [ERREUR] Impossible de monter l'ISO : $_" -ForegroundColor Red
            $installCode = -1
        } finally {
            # Toujours démonter l'ISO, même en cas d'erreur
            Dismount-DiskImage -ImagePath $niIso.FullName -ErrorAction SilentlyContinue | Out-Null
            Write-Host "   Image disque démontée." -ForegroundColor Gray
        }

        if ($installCode -eq 0 -or $installCode -eq 3010) {
            Write-Host "   [OK] NI-DAQmx installé avec succès." -ForegroundColor Green
            if ($installCode -eq 3010) {
                Write-Host "   [INFO] Un redémarrage sera nécessaire avant la première utilisation." -ForegroundColor Yellow
            }
        } elseif ($installCode -ne -1) {
            Write-Host "   [ATTENTION] Code retour : $installCode" -ForegroundColor Yellow
        }

    } elseif ($niExe) {
        Write-Host "   Installateur trouvé : $($niExe.Name)" -ForegroundColor Gray
        Write-Host "   Installation en cours... (5 à 15 min)" -ForegroundColor Yellow
        $proc = Start-Process -FilePath $niExe.FullName `
            -ArgumentList "--passive", "--accept-eulas", "--no-cancel" `
            -Wait -PassThru -ErrorAction SilentlyContinue
        $installCode = if ($proc) { $proc.ExitCode } else { -1 }

        if ($installCode -eq 0 -or $installCode -eq 3010) {
            Write-Host "   [OK] NI-DAQmx installé avec succès." -ForegroundColor Green
            if ($installCode -eq 3010) {
                Write-Host "   [INFO] Un redémarrage sera nécessaire avant la première utilisation." -ForegroundColor Yellow
            }
        } else {
            Write-Host "   [ATTENTION] Code retour : $installCode" -ForegroundColor Yellow
            Write-Host "   Si l'installation a bien démarré, attendez qu'elle se termine." -ForegroundColor Gray
        }

    } elseif ($niPkg -and $nipkg) {
        Write-Host "   Package .nipkg trouvé : $($niPkg.Name)" -ForegroundColor Gray
        Write-Host "   Installation via NI Package Manager..." -ForegroundColor Yellow
        $installOut = & $nipkg install $niPkg.FullName --accept-eulas --yes 2>&1
        $installCode = $LASTEXITCODE
        if ($installCode -eq 0 -or $installCode -eq 3010) {
            Write-Host "   [OK] NI-DAQmx installé avec succès." -ForegroundColor Green
        } else {
            Write-Host "   [ATTENTION] Code retour : $installCode" -ForegroundColor Yellow
            Write-Host "   $installOut" -ForegroundColor Gray
        }

    } else {
        Write-Host "" -ForegroundColor Yellow
        Write-Host "   [ATTENTION] Aucun installateur NI-DAQmx trouvé dans :" -ForegroundColor Yellow
        Write-Host "   $NiDaqmxDir" -ForegroundColor Gray
        Write-Host "" -ForegroundColor Yellow
        Write-Host "   Si le matériel NI est déjà branché et que les drivers sont" -ForegroundColor Gray
        Write-Host "   installés sur ce PC, vous pouvez ignorer ce message." -ForegroundColor Gray
        Write-Host "   Sinon, téléchargez NI-DAQmx sur ni.com et installez-le" -ForegroundColor Gray
        Write-Host "   manuellement avant de lancer labCE." -ForegroundColor Gray
        Write-Host "" -ForegroundColor Yellow
    }
}

# ============================================================
# ÉTAPE 3 : Installer l'application
# ============================================================
Write-Host ""
Write-Host "[3/4] Installation de $APP_NAME..." -ForegroundColor Yellow

$installDir = Join-Path $env:LOCALAPPDATA "labCE"
New-Item -ItemType Directory -Path $installDir -Force | Out-Null

$exeSrc = Join-Path $ScriptDir $EXE_NAME
if (-not (Test-Path $exeSrc)) {
    Write-Host "   [ERREUR] $EXE_NAME introuvable dans : $ScriptDir" -ForegroundColor Red
    Read-Host "Appuyez sur Entrée pour quitter"
    exit 1
}

Copy-Item $exeSrc (Join-Path $installDir $EXE_NAME) -Force

$cfgSrc = Join-Path $ScriptDir "config.ini"
$cfgDst = Join-Path $installDir "config.ini"
if ((Test-Path $cfgSrc) -and (-not (Test-Path $cfgDst))) {
    Copy-Item $cfgSrc $cfgDst -Force
}

foreach ($asset in @("Logo_LabCE.ico","Logo_LabCE.png")) {
    $src = Join-Path $ScriptDir $asset
    if (Test-Path $src) { Copy-Item $src (Join-Path $installDir $asset) -Force }
}

Write-Host "   [OK] Application installée dans : $installDir" -ForegroundColor Green

# ============================================================
# ÉTAPE 4 : Raccourci bureau
# ============================================================
Write-Host ""
Write-Host "[4/4] Création du raccourci bureau..." -ForegroundColor Yellow

$exeDst       = Join-Path $installDir $EXE_NAME
$shortcutPath = Join-Path ([Environment]::GetFolderPath("Desktop")) "$APP_NAME $APP_VERSION.lnk"
$iconDst      = Join-Path $installDir "Logo_LabCE.ico"

$wsh  = New-Object -ComObject WScript.Shell
$link = $wsh.CreateShortcut($shortcutPath)
$link.TargetPath       = $exeDst
$link.WorkingDirectory = $installDir
$link.Description      = "labCE - Banc d'essai $APP_VERSION"
if (Test-Path $iconDst) { $link.IconLocation = $iconDst }
$link.Save()

Write-Host "   [OK] Raccourci : $shortcutPath" -ForegroundColor Green

# ============================================================
# FIN
# ============================================================
Write-Host ""
Write-Host "========================================================" -ForegroundColor Green
Write-Host "  Installation terminée !" -ForegroundColor Green
Write-Host "  Double-cliquez sur '$APP_NAME $APP_VERSION' sur le bureau." -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Green
Write-Host ""
Read-Host "Appuyez sur Entrée pour fermer"
