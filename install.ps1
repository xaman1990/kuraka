# install.ps1 — one-command Kuraka setup for Windows (PowerShell).
#
# Brand-new machine, ONE line (PowerShell):
#     irm https://raw.githubusercontent.com/xaman1990/kuraka/main/install.ps1 | iex
#   (optional dir:  $env:KURAKA_DIR="D:\dev\kuraka"; irm ...\install.ps1 | iex)
#
# Or, if you already cloned the repo, from inside it:
#     powershell -ExecutionPolicy Bypass -File .\install.ps1
#
# It (1) uses this clone (or clones to $HOME\.kuraka when piped), (2) records
# KURAKA_VAULT in your USER environment, (3) adds the vault dir to your USER PATH
# so `kuraka` (kuraka.cmd) resolves anywhere. Idempotent; safe to re-run.

$ErrorActionPreference = "Stop"
$RepoUrl = if ($env:KURAKA_REPO) { $env:KURAKA_REPO } else { "https://github.com/xaman1990/kuraka.git" }

function Have($name) { [bool](Get-Command $name -ErrorAction SilentlyContinue) }

# --- resolve python + git ---
$python = if (Have "py") { "py -3" } elseif (Have "python") { "python" } else { $null }
if (-not $python) {
    Write-Host "❌ Falta Python 3. Instalalo desde https://www.python.org/downloads/ (marcá 'Add to PATH')." -ForegroundColor Red
    return
}
if (-not (Have "git")) {
    Write-Host "❌ Falta git. Instalalo desde https://git-scm.com/download/win y reintentá." -ForegroundColor Red
    return
}

# --- where is the vault? use the clone we run from, else clone it ---
$selfDir = if ($PSScriptRoot) { $PSScriptRoot } else { $null }
if ($selfDir -and (Test-Path (Join-Path $selfDir "kuraka.py"))) {
    $Vault = (Resolve-Path $selfDir).Path
    Write-Host "🪢 Instalando Kuraka  (clon existente: $Vault)"
} else {
    $Vault = if ($env:KURAKA_DIR) { $env:KURAKA_DIR } else { Join-Path $HOME ".kuraka" }
    Write-Host "🪢 Instalando Kuraka  (destino: $Vault)"
    if (Test-Path (Join-Path $Vault ".git")) {
        Write-Host "   ~ ya existe un clon, actualizando…"
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
Write-Host "   ✓ KURAKA_VAULT = $Vault  (variable de usuario)"

# --- 2) add the vault dir to the USER PATH (so kuraka.cmd resolves anywhere) ---
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if (-not $userPath) { $userPath = "" }
$parts = $userPath.Split(";") | Where-Object { $_ -ne "" }
if ($parts -notcontains $Vault) {
    $newPath = (@($Vault) + $parts) -join ";"
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    $env:Path = "$Vault;$env:Path"
    Write-Host "   ✓ $Vault agregado al PATH de usuario"
} else {
    Write-Host "   ~ $Vault ya estaba en el PATH de usuario"
}

Write-Host ""
Write-Host "✅ Listo. Abrí una terminal PowerShell NUEVA (para tomar PATH/variables)." -ForegroundColor Green
Write-Host ""
Write-Host "   Uso:"
Write-Host "     cd C:\ruta\a\tu\solucion ;  kuraka mount     # monta Kuraka acá"
Write-Host "     kuraka mount C:\ruta\a\otra\solucion          # o indicá la ruta"
Write-Host "     kuraka doctor                                 # verifica el setup"
Write-Host ""
Write-Host "   Requisitos: Python 3 y git (ya verificados)."
if (-not (Have "rtk")) {
    Write-Host ""
    Write-Host "   (recomendado) RTK para ahorrar 70-90% de tokens: ver RECOMMENDED-COMPONENTS.md"
}
