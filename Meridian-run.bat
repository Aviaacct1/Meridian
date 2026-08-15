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
