/* Avia Solutions - Meridian: background job watcher (19 August 2026).
 *
 * WHY THIS EXISTS. An optimise sweep on a cold route runs 600-700s. John's ask: let the
 * presenter leave the forecast page, walk a prospect through Catchment & demand or
 * Economics while it computes, and come back to a finished run rather than standing over
 * a spinner. /api/optimise already runs as a server-side job independent of any page (the
 * background pattern built for the Cloudflare 100-second rule); the gap was purely
 * client-side, nothing told any OTHER page that a job was alive.
 *
 * DESIGN. One shared file, included with a single <script src> line on every page rather
 * than pasted inline five times: Meridian's pages have no shared template, and copying the
 * same logic into five files is exactly the divergent-copy shape the Avia tool standard
 * exists to prevent. This file is deliberately self-contained and defensive: it assumes
 * nothing about the page's own markup beyond a CSS palette that happens to already match
 * (var(--brass) etc.), and does nothing at all if no job is stored, so a page that never
 * sees a job pays zero visible cost.
 *
 * WHAT IT DOES NOT DO. It does not re-render forecast results on another page; only the
 * dashboard's own optimise() knows how to draw a payload. A finished job shows a chip
 * saying so, with a link back to the dashboard, not the numbers themselves. If the
 * dashboard tab itself is reloaded mid-run, this same chip appears there too (so the
 * presenter is not left thinking the run vanished) but the page's own Optimise button
 * does not resume its "Optimising... Ns" state; that is a live gap for a later "resume in
 * place" job, and stated here rather than pretended away.
 */
(function () {
  "use strict";
  var KEY = "avia_active_job";
  var STALE_MS = 20 * 60 * 1000;   // far past the 600-700s worst case measured 19 Aug; a
                                    // job somehow never cleared should not haunt every page forever
  var POLL_MS = 3000;

  function readJob() {
    var raw;
    try { raw = localStorage.getItem(KEY); } catch (e) { return null; }
    if (!raw) return null;
    var job;
    try { job = JSON.parse(raw); } catch (e) { try { localStorage.removeItem(KEY); } catch (e2) {} return null; }
    if (!job || !job.job_id || !job.started || (Date.now() - job.started) > STALE_MS) {
      try { localStorage.removeItem(KEY); } catch (e) {}
      return null;
    }
    return job;
  }
  function clearJob() { try { localStorage.removeItem(KEY); } catch (e) {} }

  function buildChip() {
    var chip = document.createElement("div");
    chip.id = "aviaJobChip";
    chip.style.cssText = "position:fixed;right:18px;bottom:18px;z-index:9999;max-width:320px;"
      + "background:var(--paper,#F3EFE6);border:1px solid var(--brass,#D4A249);border-radius:4px;"
      + "padding:11px 14px;font-family:var(--sans,sans-serif);font-size:11.5px;color:var(--ink,#1B2430);"
      + "box-shadow:0 4px 18px rgba(0,0,0,.18);";
    document.body.appendChild(chip);
    return chip;
  }

  function render(chip, job, st) {
    var route = (job.origin || "?") + " → " + (job.dest || "?");
    if (!st || st.state === "running") {
      var els = st && typeof st.elapsed_s === "number" ? st.elapsed_s
        : Math.round((Date.now() - job.started) / 1000);
      chip.innerHTML = "<div><b>Optimising</b> " + route + "… " + els + "s</div>"
        + "<div style='margin-top:6px;display:flex;gap:10px'>"
        + "<a href='/' style='color:var(--brass-deep,#A97C33);font-weight:600;text-decoration:none'>View on Dashboard</a>"
        + "<a href='#' id='aviaJobStop' style='color:var(--signal,#CE3B2A);font-weight:600;text-decoration:none'>Stop</a>"
        + "</div>";
      var stopEl = chip.querySelector("#aviaJobStop");
      if (stopEl) stopEl.onclick = function (ev) {
        ev.preventDefault();
        fetch("/api/optimise/cancel?job_id=" + encodeURIComponent(job.job_id)).catch(function () {});
        clearJob();
        chip.remove();
      };
      return;
    }
    // Terminal state: say so, point back to the dashboard, stop polling. The dashboard
    // itself renders the numbers; this widget only ever needed to say a run finished.
    var word = st.state === "done" ? "Finished"
      : st.state === "cancelled" ? "Stopped"
      : "Could not complete";
    chip.innerHTML = "<div><b>" + word + ":</b> " + route + "</div>"
      + "<div style='margin-top:6px'><a href='/' style='color:var(--brass-deep,#A97C33);"
      + "font-weight:600;text-decoration:none'>View on Dashboard</a></div>";
    clearJob();
  }

  function watch(job) {
    var chip = buildChip();
    render(chip, job, null);
    var timer = setInterval(function () {
      fetch("/api/optimise/status?job_id=" + encodeURIComponent(job.job_id))
        .then(function (r) { return r.json(); })
        .then(function (st) {
          if (!chip.isConnected) { clearInterval(timer); return; }
          render(chip, job, st);
          if (st.state !== "running") clearInterval(timer);
        })
        .catch(function () { /* a transient poll failure is not a reason to declare the job dead */ });
    }, POLL_MS);
  }

  var job = readJob();
  if (job) watch(job);
})();
