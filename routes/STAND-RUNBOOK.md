# Meridian stand runbook

Written by W2 and rewritten as rulings land. Version 1, 27 September 2026. Author: Avia Solutions.
For the person at the workstation and the host at the stand. The host manual
(STAND-HOST-MANUAL.md, W4) is what the host reads to talk to a visitor; this is what either of
them reads when something has to be started, checked or recovered.

Every line here comes from a controller ruling or a measured fault, and each says which.

## 1. Starting the server (donatello)

Order matters and each step has a reason.

1. Connect by remote desktop over Tailscale. FIRST check for an existing session and DISCONNECT
   it; never sign out. A stale session holds the console and a sign-out kills the servers with it
   (ruling, 25 September).
2. In a NON-ELEVATED PowerShell window: set QSI_PASSWORD with `Read-Host`, never a pasted
   placeholder; then AVIA_OPT_WORKERS; then run the launcher. A server started from an elevated
   window can only be stopped from one (ruling, 24 September).
3. If a server is already running, stop it first. `Meridian-run.bat` re-warms a running server
   rather than replacing it, so a second run does not pick up new code or new variables
   (ruling 18).
4. The server runs in its own PowerShell window which stays open after an exit and tees every
   line to `app\logs\server-<stamp>.log`. MINIMISE IT AND NEVER CLICK OR TYPE INTO IT. The host
   works only in the browser (ruling, 24 September evening).

## 2. What the console must say before the stand opens

Read these five lines every start. Any one of them wrong is a stop, not a note for later.

| Line | Must read | If it does not |
|---|---|---|
| MCT master | `[cortex] MCT master: N rows from ...` | Never `NOT LOADED`. Every connection falls back to a flat 90-minute minimum connect time and multi-airport metro forecasts differ from the live tool. Fix the path, restart. |
| Catchment distance | `[cortex] catchment distance: ROAD TIME from ...` | `STRAIGHT LINE` contradicts the launcher's own "road drive times on" echo. The raster is at `%AVIA_ROOT%\2020_motorized_friction_surface.geotiff`; check it is there and that rasterio and scikit-image are in the machine Python. |
| Economics view | `[cortex] economics view: WITHHELD pending the margin basis check` | `ON` means a margin figure can reach a visitor while pre-mortem 33 is open. Clear `AVIA_SHOW_ECONOMICS` and restart. |
| scikit-learn | `scikit-learn: 1.9.0  user site-packages: ignored` | Anything else is a stop. A roaming 1.7.2 unpickles the calibrated model with a version warning (24 September). |
| Stand mode | The stand build runs with `AVIA_STAND_MODE` on | It refuses to start without the MCT master, deliberately, so the stand never demonstrates a silent difference from the live tool. |

## 3. During the show

- "Failed to fetch" on the dashboard means the server is down. Run the launcher block from
  section 1 and nothing else (ruling, 24 September evening).
- After ANY incident, the last server log under `app\logs` is the evidence. Copy it to
  `E:\Avia\probe` BEFORE anything is relaunched (ruling, 24 September evening).
- The catchment page draws road drive times. The forecast's own catchment share uses the same
  raster, so the two agree; if the console says STRAIGHT LINE they do not, and the page says which
  it used. Check the console line before telling a visitor what the circles mean.

## 4. The same-day pack

- The host types the visitor's email at the foot of the run they have just watched. That queues
  the pack for THAT run, with its own inputs, so what arrives is what was on the screen.
- Two speeds. Leave it alone and the pack sends itself after the hold, which a reviewer can stop.
  Tick "send as soon as it is built" only for a visitor who needs it for a meeting today.
- The reviewer works from `/demo/queue`: newest first, the countdown visible, two actions, PAUSE
  and SEND NOW. A pause needs a one-line reason because the next person reads it.
- A build that fails its own checks is PAUSED automatically and never sends. That is the safety
  net on the jobs nobody looks at.
- A paused job triggers a short holding note to the visitor the same day, so nothing arrives late
  in silence.
- THE HOLD IS A SETTING, in minutes, changed at the top of the queue page without a restart. Zero
  means send as soon as the build passes.
- OFFLINE FALLBACK, for the day the queue is down: take the email and the route on a card and run
  it later. Say so to the visitor rather than promising a time the stand cannot keep.

## 5. A named route arriving by email (W6 risk 1, W2 owns the step)

An invitation reply that names a route is forwarded by John to the person at the stand build the
SAME DAY. That route is warmed and run before the meeting, and inside 48 hours it runs live. This
is in force before the first invitation goes out.

## 6. The freeze

No store refresh of any kind from 10 October until after 23 October. `refresh_weekly` is disabled
on the workstation from 10 October and re-enabled by John after Routes (ruling, 25 September).

## 7. What is not settled yet

- Which tablet the capture front end runs on, and how it reaches the form under Plan B, where the
  laptop serves only itself and there is no venue network.
- The named reviewer for the pack queue and their hours for 21-23 October (John, umbrella item 62).
- The laptop build procedure, which waits on the external drive and John's two spec blocks.
