# Script PowerShell pour nettoyer immédiatement tous les logs Java
Write-Host "Nettoyage des logs Java..." -ForegroundColor Yellow

$backendDir = $PSScriptRoot
$parentDir = Split-Path -Parent $backendDir

$deleted = 0

# Nettoyer dans le répertoire backend
Write-Host "Recherche dans: $backendDir" -ForegroundColor Cyan
Get-ChildItem -Path $backendDir -Filter "hs_err_pid*.log" -ErrorAction SilentlyContinue | ForEach-Object {
    Remove-Item $_.FullName -Force -ErrorAction SilentlyContinue
    Write-Host "  Supprime: $($_.Name)" -ForegroundColor Green
    $deleted++
}
Get-ChildItem -Path $backendDir -Filter "replay_pid*.log" -ErrorAction SilentlyContinue | ForEach-Object {
    Remove-Item $_.FullName -Force -ErrorAction SilentlyContinue
    Write-Host "  Supprime: $($_.Name)" -ForegroundColor Green
    $deleted++
}

# Nettoyer dans le répertoire parent
Write-Host "Recherche dans: $parentDir" -ForegroundColor Cyan
Get-ChildItem -Path $parentDir -Filter "hs_err_pid*.log" -ErrorAction SilentlyContinue | ForEach-Object {
    Remove-Item $_.FullName -Force -ErrorAction SilentlyContinue
    Write-Host "  Supprime: $($_.Name)" -ForegroundColor Green
    $deleted++
}
Get-ChildItem -Path $parentDir -Filter "replay_pid*.log" -ErrorAction SilentlyContinue | ForEach-Object {
    Remove-Item $_.FullName -Force -ErrorAction SilentlyContinue
    Write-Host "  Supprime: $($_.Name)" -ForegroundColor Green
    $deleted++
}

if ($deleted -gt 0) {
    Write-Host "`n[OK] $deleted fichier(s) de log supprime(s)" -ForegroundColor Green
} else {
    Write-Host "`n[OK] Aucun fichier de log trouve" -ForegroundColor Green
}

Write-Host "`nNettoyage termine!" -ForegroundColor Yellow
Read-Host "Appuyez sur Entree pour continuer"

