#!/usr/bin/env python3
"""Rule-lock for the same-day pack queue (controller rulings, 26 September 2026).

The queue exists so a visitor's own run leaves the stand the same day. These checks hold the
properties that would otherwise be intentions:

  1. HOLD is the default and the hold is a SETTING, read when the build passes, changeable
     while the server runs. Zero is a real value and means send on pass.
  2. NOW ignores the hold. It is the host's choice for a visitor with a meeting today.
  3. A FAILED BUILD CHECK GOES TO PAUSED AND NEVER TO SEND. There is no path from a failed
     check to a delivered pack, which is the whole safety net on the jobs nobody looks at.
  4. A PAUSED JOB IS INVISIBLE TO THE SENDER. due() is the only thing the sender reads.
  5. A SEND IS NOT A SEND WITHOUT THE PROVIDER'S MESSAGE ID (21 September: SMTP acknowledged
     three messages Postmark never received).
  6. A RELEASED JOB RESTARTS ITS CLOCK, so it is not instantly overdue by the time it waited.
  7. Every refusal says what is wrong, and the job stays where it was.

Avia Solutions Limited. All rights reserved.
"""
import os
import sys
import tempfile
from datetime import timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import lead_store as LS
import pack_queue as PQ

CHECKS = []


def check(name, got, want):
    CHECKS.append((name, got == want, got, want))


def refuses(name, fn, *a, **k):
    try:
        fn(*a, **k)
        CHECKS.append((name, False, "no refusal", "PackQueueError"))
    except PQ.PackQueueError as e:
        CHECKS.append((name, bool(str(e).strip()), "refused: %s" % e, "refused with a reason"))


def main():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "leads.duckdb")

        # ---- 1. the default is HOLD, and the hold is a setting ---------------------------
        check("default hold is 30 minutes", PQ.hold_minutes(path=p), 30)
        check("hold can be changed while running", PQ.set_hold_minutes(5, path=p), 5)
        check("the change is what is read back", PQ.hold_minutes(path=p), 5)
        check("zero is a real value", PQ.set_hold_minutes(0, path=p), 0)
        check("zero reads back as zero, not as the default", PQ.hold_minutes(path=p), 0)
        refuses("a negative hold is refused", PQ.set_hold_minutes, -1, path=p)
        refuses("a hold that is not a number is refused", PQ.set_hold_minutes, "soon", path=p)
        PQ.set_hold_minutes(30, path=p)

        # ---- 2. a job carries the run's own inputs ---------------------------------------
        inputs = {"origin": "TIF", "dest": "AUH", "airline": "EY", "freq": 3, "season": "annual"}
        j = PQ.enqueue("planner@airline.com", mode="hold", path=p, route="TIF-AUH",
                       origin="TIF", dest="AUH", airline="EY", run_ref="run-1", inputs=inputs)
        job = PQ.get(j, path=p)
        check("queued on capture", job["state"], "queued")
        check("hold is the default mode", job["mode"], "hold")
        check("the run's inputs travel with the job", '"freq": 3' in job["inputs"], True)
        check("email normalised", job["email"], "planner@airline.com")
        refuses("a free-mail address is refused with the reason",
                PQ.enqueue, "someone@gmail.com", path=p, route="X-Y")
        refuses("an unknown field is named, not ignored",
                PQ.enqueue, "a@airline.com", path=p, nonsense=1)
        refuses("an invented mode is refused",
                PQ.enqueue, "a@airline.com", mode="whenever", path=p)

        # ---- 3. HOLD: the build passes, the clock starts ----------------------------------
        PQ.mark_building(j, path=p)
        check("building", PQ.get(j, path=p)["state"], "building")
        PQ.mark_built(j, True, pack_path="/packs/1.pptx", preview_path="/packs/1.pdf", path=p)
        job = PQ.get(j, path=p)
        check("a passed build is ready, not sent", job["state"], "ready")
        check("the hold in force is recorded on the job", job["hold_minutes"], 30)
        check("the pack path is kept", job["pack_path"], "/packs/1.pptx")
        check("not due yet", PQ.due(path=p), [])
        check("the queue can say how long is left",
              0 < PQ.seconds_to_send(PQ.get(j, path=p)) <= 30 * 60, True)
        later = LS.now() + timedelta(minutes=31)
        check("due once the hold has run out", [x["id"] for x in PQ.due(at=later, path=p)], [j])

        # ---- 4. NOW ignores the hold ------------------------------------------------------
        n = PQ.enqueue("chief@airline.com", mode="now", path=p, route="LHR-JFK")
        PQ.mark_built(n, True, path=p)
        job = PQ.get(n, path=p)
        check("NOW carries no hold", job["hold_minutes"], 0)
        check("NOW is due at once", n in [x["id"] for x in PQ.due(path=p)], True)

        # ---- 5. a failed check pauses and never sends -------------------------------------
        f = PQ.enqueue("ops@airport.com", path=p, route="BHX-DXB")
        PQ.mark_built(f, False, failed_check="forecast year missing from the cover", path=p)
        job = PQ.get(f, path=p)
        check("a failed check goes to paused", job["state"], "paused")
        check("the check that failed is named", job["failed_check"],
              "forecast year missing from the cover")
        check("the pause says who paused it", job["paused_by"], "build checks")
        check("a failed build is never due",
              f in [x["id"] for x in PQ.due(at=LS.now() + timedelta(days=1), path=p)], False)
        refuses("a failed build must name its check", PQ.mark_built, f, False, path=p)
        refuses("a job with no build cannot be sent now", PQ.send_now, f, path=p)

        # ---- 6. pause, release, and the clock restarts ------------------------------------
        refuses("a pause needs a reason", PQ.pause, j, "  ", path=p)
        PQ.pause(j, "check the fare basis on the economics page", path=p)
        job = PQ.get(j, path=p)
        check("paused", job["state"], "paused")
        check("the reason is kept", job["pause_reason"], "check the fare basis on the economics page")
        check("a paused job is invisible to the sender",
              [x["id"] for x in PQ.due(at=LS.now() + timedelta(days=1), path=p)], [n])
        check("time to send does not apply to a paused job", PQ.seconds_to_send(job), None)
        check("it appears on the holding-email list once",
              j in [x["id"] for x in PQ.needs_holding_email(path=p)], True)
        PQ.record_holding_email(j, "hold-msg-1", path=p)
        check("and not twice",
              j in [x["id"] for x in PQ.needs_holding_email(path=p)], False)
        PQ.release(j, path=p)
        job = PQ.get(j, path=p)
        check("released back to ready", job["state"], "ready")
        check("the reason is cleared on release", job["pause_reason"], None)
        check("the clock restarts rather than firing at once",
              PQ.seconds_to_send(job) > 25 * 60, True)
        refuses("releasing a job that is not paused is refused", PQ.release, n, path=p)

        # ---- 7. a send needs the provider's identifier ------------------------------------
        PQ.mark_sending(n, path=p)
        refuses("no message id, no send", PQ.mark_sent, n, "", path=p)
        check("the job did not move on a refused send", PQ.get(n, path=p)["state"], "sending")
        PQ.mark_sent(n, "b1c2-provider-id", path=p)
        job = PQ.get(n, path=p)
        check("sent", job["state"], "sent")
        check("the provider id is the record", job["provider_message_id"], "b1c2-provider-id")
        check("a sent job is no longer due",
              n in [i["id"] for i in PQ.due(at=LS.now() + timedelta(days=1), path=p)], False)
        refuses("a sent job cannot be paused", PQ.pause, n, "too late", path=p)
        refuses("a sent job cannot be sent again", PQ.send_now, n, path=p)

        # ---- 8. failure states say what failed --------------------------------------------
        x = PQ.enqueue("net@airline.com", path=p, route="SOU-JFK")
        PQ.mark_built(x, True, path=p)
        refuses("a failure has to say what failed", PQ.mark_failed, x, "", path=p)
        PQ.mark_failed(x, "Postmark refused: sender signature not confirmed", path=p)
        job = PQ.get(x, path=p)
        check("failed", job["state"], "failed")
        check("the reason is on the job", "sender signature" in job["error"], True)
        check("a failed job is not due",
              x in [i["id"] for i in PQ.due(at=LS.now() + timedelta(days=1), path=p)], False)

        # ---- 9. the reviewer's list, newest first, with the time left ---------------------
        rows = PQ.listing(path=p)
        check("every job is listed", len(rows), 4)
        check("newest first", rows[0]["route"], "SOU-JFK")
        check("the list carries the time to send", "seconds_to_send" in rows[0], True)
        check("filtering by state works", [r["state"] for r in PQ.listing(state="sent", path=p)],
              ["sent"])
        PQ.note(j, "waiting on the fare check", path=p)
        check("a reviewer note is kept", PQ.get(j, path=p)["reviewer_note"],
              "waiting on the fare check")

        # ---- 10. the event log answers what happened afterwards ---------------------------
        events = [e["event"] for e in PQ.events_for(j, path=p)]
        check("the job's history is answerable",
              events[:4], ["queued", "building", "build_passed", "paused"])
        check("and it records the release", "released" in events, True)

        # ---- 11. the lead store is untouched by any of this --------------------------------
        lead = LS.capture("route", path=p, email="planner@airline.com", route="TIF-AUH")
        check("leads and jobs share the store without collision",
              LS.get(lead, path=p)["email"], "planner@airline.com")
        check("the jobs are still there", len(PQ.listing(path=p)), 4)

    failed = [c for c in CHECKS if not c[1]]
    for name, ok, got, want in CHECKS:
        if not ok:
            print("FAIL  %s: got %r, wanted %r" % (name, got, want))
    print("%d checks, %d failed" % (len(CHECKS), len(failed)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
