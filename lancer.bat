@echo off
rem ============================================================================
rem  Simulation du programme " Ecologie de droite " - lanceur Windows
rem  Double-cliquer sur ce fichier. Premiere fois : installe un environnement
rem  Python local (dossier .venv) et les bibliotheques necessaires.
rem ============================================================================
setlocal EnableExtensions
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"

rem --- 1. Trouver Python (3.10 ou plus) ---------------------------------------
set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY (
    where python >nul 2>nul && set "PY=python"
)
if not defined PY (
    echo.
    echo Python n'est pas installe.
    echo Installez-le depuis https://www.python.org/downloads/ ^(cochez " Add python.exe to PATH "^),
    echo puis relancez ce fichier.
    echo.
    pause
    exit /b 1
)

rem --- 2. Environnement local .venv (une seule fois) --------------------------
if not exist ".venv\Scripts\python.exe" (
    echo Premiere utilisation : creation de l'environnement Python local...
    %PY% -m venv .venv
    if errorlevel 1 (
        echo Echec de la creation de l'environnement. Verifiez votre installation de Python.
        pause
        exit /b 1
    )
    echo Installation des bibliotheques ^(quelques minutes^)...
    ".venv\Scripts\python.exe" -m pip install --upgrade pip >nul
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo Echec de l'installation des bibliotheques ^(connexion internet ?^).
        pause
        exit /b 1
    )
)
set "VPY=.venv\Scripts\python.exe"

rem --- 3. Menu ----------------------------------------------------------------
:menu
cls
echo ============================================================
echo   Simulation du programme - que voulez-vous lancer ?
echo ============================================================
echo.
echo   1. Resume rapide : deficits des quatre scenarios   (~30 s)
echo   2. Tableau de bord : recalculer et l'ouvrir       (~5 min)
echo   3. Tout recalculer : sensibilite, incertitude, leviers,
echo      IS progressif, puis tableau de bord            (~1 h)
echo   4. Verifier le moteur : lancer les tests          (~10 min)
echo   5. Ouvrir le dernier tableau de bord (sans recalcul)
echo   6. Installer OpenFisca (facultatif : regenerer les tables
echo      du systeme actuel ; gros telechargement)
echo   0. Quitter
echo.
set "CHOIX="
set /p CHOIX="Votre choix : "

if "%CHOIX%"=="1" goto resume
if "%CHOIX%"=="2" goto tableau
if "%CHOIX%"=="3" goto tout
if "%CHOIX%"=="4" goto tests
if "%CHOIX%"=="5" goto ouvrir
if "%CHOIX%"=="6" goto openfisca
if "%CHOIX%"=="0" exit /b 0
goto menu

:resume
"%VPY%" -m moteur.simulation
goto fin

:tableau
echo Calcul du tableau de bord...
"%VPY%" -m outils.tableau_de_bord
if errorlevel 1 goto erreur
goto ouvrir

:tout
echo [1/5] Sensibilite...
"%VPY%" -m moteur.sensibilite || goto erreur
echo [2/5] Incertitude...
"%VPY%" -m moteur.incertitude || goto erreur
echo [3/5] Leviers...
"%VPY%" -m outils.leviers || goto erreur
echo [4/5] IS progressif...
"%VPY%" -m outils.is_progressif || goto erreur
echo [5/5] Tableau de bord...
"%VPY%" -m outils.tableau_de_bord || goto erreur
goto ouvrir

:tests
"%VPY%" -m pytest -q
goto fin

:ouvrir
if exist "sorties\tableau_de_bord.html" (
    start "" "sorties\tableau_de_bord.html"
) else (
    echo Pas encore de tableau de bord : lancez le choix 2.
)
goto fin

:openfisca
"%VPY%" -m pip install "openfisca-france>=176"
goto fin

:erreur
echo.
echo *** Une etape a echoue : voir le message ci-dessus. ***

:fin
echo.
pause
goto menu
