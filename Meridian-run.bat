@echo off
title Meridian - The Observatory
rem =====================================================================
rem  Meridian portal launcher - WORKSTATION shortcut target.
rem  Lives in the repo (C:\src\meridian\Meridian-run.bat after a pull);
rem  make the desktop shortcut point at that path so a git pull updates
rem  the launcher like everything else. Avia Solutions, 15 August 2026.
rem =====================================================================
cd /d C:\src\meridian\app
rem E: is the mapped product drive over D:\Avia. A session that cannot
rem see the mapping (elevated windows lose per-logon drives) falls back
rem to the same disk by its real letter, so the launcher works in both.
if exist E:\Avia\sabre.duckdb (set AVIA_ROOT=E:\Avia) else (set AVIA_ROOT=D:\Avia)
set AVIA_SABRE=%AVIA_ROOT%\sabre.duckdb
set AVIA_OAG=%AVIA_ROOT%\oag.duckdb
rem The MCT master lives on the product drive too (John, 24 Sep 2026): nothing the
rem server needs may depend on a per-logon network letter such as Z:. Copied from
rem Egnyte by hand when it changes; the server refuses to start in stand mode without it.
set AVIA_MCT_MASTER=%AVIA_ROOT%\Reference Tables\MCT Master List.xlsx
rem Per-user Python package folders are IGNORED (24 Sep 2026): a roaming scikit-learn 1.7.2 in
rem one logon was loading in front of the machine's pinned 1.9.0 (app\requirements.txt) and
rem unpickling the calibrated model with a version warning. Every logon runs the machine install.
set PYTHONNOUSERSITE=1
rem The shipped configuration, stated rather than remembered:
rem   frequency-sensitive capture ON (the deck ladder needs it),
rem   feed level V1 (John's 15 August decision; timing stays QSI).
rem   AVIA_FEED_LEVEL=qsi here is the one-line rollback.
set AVIA_FREQ_SENSITIVE=1
set AVIA_FEED_LEVEL=v1
echo.
echo  Meridian starting. Stores at %AVIA_ROOT%. Feed level V1, timing QSI,
echo  frequency-sensitive on.
echo.
echo  NOTE: if a server is already running, warm_demo re-warms it and it
echo  keeps the environment it was STARTED with. To change settings,
echo  close the old server window first, then run this again.
echo.
py -3.12 warm_demo.py
echo.
echo  Meridian has stopped. This window stays open so any error above
echo  can be read rather than vanishing with the window.
pause
