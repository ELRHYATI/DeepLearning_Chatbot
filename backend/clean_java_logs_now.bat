@echo off
REM Script batch pour nettoyer immédiatement tous les logs Java
echo Nettoyage des logs Java...
echo.

cd /d %~dp0

set DELETED=0

REM Nettoyer dans le répertoire backend
echo Recherche dans: %CD%
for %%f in (hs_err_pid*.log) do (
    if exist "%%f" (
        del /Q /F "%%f" 2>nul
        if not exist "%%f" (
            echo   Supprime: %%f
            set /a DELETED+=1
        )
    )
)
for %%f in (replay_pid*.log) do (
    if exist "%%f" (
        del /Q /F "%%f" 2>nul
        if not exist "%%f" (
            echo   Supprime: %%f
            set /a DELETED+=1
        )
    )
)

REM Nettoyer dans le répertoire parent
cd ..
echo Recherche dans: %CD%
for %%f in (hs_err_pid*.log) do (
    if exist "%%f" (
        del /Q /F "%%f" 2>nul
        if not exist "%%f" (
            echo   Supprime: %%f
            set /a DELETED+=1
        )
    )
)
for %%f in (replay_pid*.log) do (
    if exist "%%f" (
        del /Q /F "%%f" 2>nul
        if not exist "%%f" (
            echo   Supprime: %%f
            set /a DELETED+=1
        )
    )
)

echo.
if %DELETED% GTR 0 (
    echo [OK] %DELETED% fichier(s) de log supprime(s)
) else (
    echo [OK] Aucun fichier de log trouve
)

echo.
echo Nettoyage termine!
pause

