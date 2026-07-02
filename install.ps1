# install.ps1 - one-command Kuraka setup for Windows (PowerShell). ASCII-only so it
# parses under Windows PowerShell 5.1 (which reads .ps1 as ANSI, not UTF-8).
#
# Brand-new machine, ONE line (PowerShell):
#     irm https://raw.githubusercontent.com/xaman1990/kuraka/main/install.ps1 | iex
#
# Or, if you already downloaded/cloned the repo, from inside it:
#     powershell -ExecutionPolicy Bypass -File .\install.ps1
#
# It (1) uses this copy (or clones to $HOME\.kuraka when piped and not present),
# (2) records KURAKA_VAULT in your USER environment, (3) adds the vault dir to your
# USER PATH so `kuraka` (kuraka.cmd) resolves anywhere. Idempotent; safe to re-run.
# git is only required when it has to clone (not when run from an existing copy).

$ErrorActionPreference = "Stop"
$RepoUrl = if ($env:KURAKA_REPO) { $env:KURAKA_REPO } else { "https://github.com/xaman1990/kuraka.git" }

function Have($name) { [bool](Get-Command $name -ErrorAction SilentlyContinue) }

# --- Python 3 is always required (the mount + CLI are Python) ---
if (-not (Have "python") -and -not (Have "py")) {
    Write-Host "ERROR: Falta Python 3. Instalalo desde https://www.python.org/downloads/" -ForegroundColor Red
    Write-Host "       (marca 'Add python.exe to PATH' en el instalador)." -ForegroundColor Red
    return
}

# --- resolve the vault: use this copy if it has kuraka.py, else clone ---
$selfDir = if ($PSScriptRoot) { $PSScriptRoot } else { (Get-Location).Path }
if (Test-Path (Join-Path $selfDir "kuraka.py")) {
    $Vault = (Resolve-Path $selfDir).Path
    Write-Host "Instalando Kuraka  (copia existente: $Vault)"
} else {
    if (-not (Have "git")) {
        Write-Host "ERROR: Falta git para clonar. Instalalo (https://git-scm.com/download/win)" -ForegroundColor Red
        Write-Host "       o corre install.ps1 desde adentro del repo ya descargado." -ForegroundColor Red
        return
    }
    $Vault = if ($env:KURAKA_DIR) { $env:KURAKA_DIR } else { Join-Path $HOME ".kuraka" }
    Write-Host "Instalando Kuraka  (destino: $Vault)"
    if (Test-Path (Join-Path $Vault ".git")) {
        Write-Host "   ~ ya existe un clon, actualizando..."
        git -C $Vault pull --ff-only 2>$null
        git -C $Vault submodule update --init --recursive 2>$null
    } else {
        git clone --recurse-submodules $RepoUrl $Vault
    }
    $Vault = (Resolve-Path $Vault).Path
}
Write-Host ""

# --- 1) KURAKA_VAULT in the USER environment (persists across sessions) ---
[Environment]::SetEnvironmentVariable("KURAKA_VAULT", $Vault, "User")
$env:KURAKA_VAULT = $Vault
Write-Host "   [ok] KURAKA_VAULT = $Vault"

# --- 2) add the vault dir to the USER PATH (so kuraka.cmd resolves anywhere) ---
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if (-not $userPath) { $userPath = "" }
$parts = $userPath.Split(";") | Where-Object { $_ -ne "" }
if ($parts -notcontains $Vault) {
    $newPath = (@($Vault) + $parts) -join ";"
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    $env:Path = "$Vault;$env:Path"
    Write-Host "   [ok] $Vault agregado al PATH de usuario"
} else {
    Write-Host "   ~ $Vault ya estaba en el PATH de usuario"
}

Write-Host ""
Write-Host "OK. Abri una terminal PowerShell NUEVA (para tomar PATH y variables)." -ForegroundColor Green
Write-Host ""
Write-Host "   Uso:"
Write-Host "     kuraka doctor                          # verifica el setup"
Write-Host "     cd C:\ruta\a\tu\solucion"
Write-Host "     kuraka mount                           # monta Kuraka aca"
Write-Host "     kuraka mount C:\ruta\a\otra\solucion   # o indica la ruta"
Write-Host ""
if (-not (Have "git")) {
    Write-Host "   Nota: git no esta instalado. El mount funciona igual; solo se pierde el"
    Write-Host "   etiquetado por rama. Recomendado instalar git: https://git-scm.com/download/win"
    Write-Host ""
}
if (-not (Have "rtk")) {
    Write-Host "   (recomendado) RTK para ahorrar 70-90% de tokens: ver RECOMMENDED-COMPONENTS.md"
}
