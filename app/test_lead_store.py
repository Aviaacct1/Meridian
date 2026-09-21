#!/usr/bin/env python3
r"""Rule-lock for app/lead_store.py, the stand's record of everyone it met.

The checks are grouped around the properties that are load-bearing rather than around the
functions, because it is the properties that will be broken by accident later:

  the record survives the pack      capture happens first and does not depend on a send
  the record is editable after      the useful detail arrives once the visitor has gone
  notes append, never replace       a second thought does not erase the first
  the log is append-only            what happened stays answerable after a correction
  the provider is the authority     our belief that a pack went is not evidence that it did
  the quota is John's 16 Aug rule   first pack free, the rest held, a failure stays free
  migration refuses to lose lines   a silent drop is worse than a refusal

Avia Solutions Limited. All rights reserved.
"""
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import lead_store as LS

CHECKS, FAIL = 0, []


def check(name, ok):
    global CHECKS
    CHECKS += 1
    if not ok:
        FAIL.append(name)
    print("%-58s %s" % (name[:58], "PASS" if ok else "FAIL"))


def main():
    tmp = tempfile.mkdtemp(prefix="lead_store_")
    db = os.path.join(tmp, "leads.duckdb")
    con = LS.connect(db)

    # --- the record survives the pack ---------------------------------------
    rid = LS.capture("route", con=con, name="Jane Doe", company="EVA Air",
                     role="Network Planning", email="  Jane@EvaAir.COM ",
                     origin="BRS", dest="EWR", airline="UA", consent=True,
                     wanted="whether Bristol can hold a daily",
                     questions="what fare basis, and how the connecting feed is built",
                     run_ref="run-123", params={"origin": "BRS", "dest": "EWR"})
    rec = LS.get(rid, con=con)
    check("a captured route record exists at once", rec is not None)
    check("it is pending before any pack is built", rec["status"] == "pending")
    check("the email is normalised", rec["email"] == "jane@evaair.com")
    check("the domain is derived", rec["email_domain"] == "evaair.com")
    check("the route is derived from origin and dest", rec["route"] == "BRS-EWR")
    check("the run shown is carried", rec["run_ref"] == "run-123")
    check("the run params are stored so a pack can be rebuilt",
          rec["params"] and "BRS" in rec["params"])
    check("what they came to look at is kept", "daily" in (rec["wanted"] or ""))

    # --- the other three kinds ----------------------------------------------
    cid = LS.capture("card", con=con, company="Dallas Fort Worth", interest="high")
    nid = LS.capture("note", con=con, notes="third person today asking about APD")
    vid = LS.capture("voice", con=con, captured_by="Suzanna")
    check("a card drop needs no email", LS.get(cid, con=con)["email"] is None)
    check("card and note rest at captured, promising nobody anything",
          LS.get(cid, con=con)["status"] == "captured"
          and LS.get(nid, con=con)["status"] == "captured")
    check("an unattributed note carries no person",
          LS.get(nid, con=con)["name"] is None)
    check("a voice note records who dictated it",
          LS.get(vid, con=con)["captured_by"] == "Suzanna")
    check("all four kinds are listed together", len(LS.listing(con=con)) == 4)
    check("listing filters by kind", len(LS.listing(kind="card", con=con)) == 1)

    # --- editable after the moment ------------------------------------------
    LS.update(rid, con=con, buyer=True, pricing_interest="asked for the year-1 number",
              follow_up_owner="John", follow_up_date="2026-10-24")
    rec = LS.get(rid, con=con)
    check("a record can be edited after the visitor has gone", rec["buyer"] is True)
    check("pricing interest is captured", "year-1" in rec["pricing_interest"])
    check("a follow-up owner and date can be set", rec["follow_up_owner"] == "John")
    check("updated_at moves with the edit", rec["updated_at"] >= rec["created_at"])
    try:
        LS.update(rid, con=con, favourite_colour="blue")
        check("an unknown field is refused, not silently dropped", False)
    except LS.LeadStoreError as e:
        check("an unknown field is refused, not silently dropped",
              "favourite_colour" in str(e))

    # --- notes append --------------------------------------------------------
    LS.add_note(rid, "wants the Tampa comparison too", con=con)
    LS.add_note(rid, "introduce to Nick on methodology", con=con)
    notes = LS.get(rid, con=con)["notes"]
    check("the first note survives the second",
          "Tampa" in notes and "Nick" in notes)

    # --- the log is append-only ---------------------------------------------
    evs = [e["event"] for e in LS.events_for(rid, con=con)]
    check("capture is logged", evs[0] == "captured")
    check("edits and notes are logged", "updated" in evs and "note_added" in evs)
    check("the log keeps every step, not just the last", len(evs) >= 4)

    # --- the provider is the authority --------------------------------------
    LS.record_send(rid, message_id="pm-abc-123", status="sent", con=con)
    rec = LS.get(rid, con=con)
    check("a send records the provider's own identifier",
          rec["provider_message_id"] == "pm-abc-123")
    check("a send is dated", rec["pack_sent_at"] is not None)
    check("the status follows the send", rec["status"] == "sent")

    # the 21 September case: we believe it sent, the provider has never heard of it
    out = LS.reconcile(lambda mid: None, con=con)
    rec = LS.get(rid, con=con)
    check("reconciling checks every message we think we sent", out["checked"] == 1)
    check("a message the provider does not know is flagged, not assumed sent",
          rid in out["disagreed"])
    check("the disagreement is written down",
          "unknown to the provider" in (rec["provider_status"] or ""))
    LS.reconcile(lambda mid: "Delivered", con=con)
    check("a provider confirmation is written down too",
          LS.get(rid, con=con)["provider_status"] == "Delivered")

    # --- the quota, John's 16 August ruling ---------------------------------
    con2 = LS.connect(os.path.join(tmp, "quota.duckdb"))
    a, why = LS.quota_decision("new@airline.com", "SJC-TPE", con=con2)
    check("the first pack for an address sends automatically", a == "send")
    q = LS.capture("route", con=con2, email="new@airline.com", route="SJC-TPE")
    LS.record_send(q, message_id="m1", status="sent", con=con2)
    a, why = LS.quota_decision("new@airline.com", "SJC-TPE", con=con2)
    check("the same address and route is held", a == "pending")
    check("the reason names the route", "SJC-TPE" in why)
    a, why = LS.quota_decision("new@airline.com", "BRS-EWR", con=con2)
    check("a second route from the same address is also held", a == "pending")
    f = LS.capture("route", con=con2, email="unlucky@carrier.com", route="BRS-BOS")
    LS.record_send(f, status="failed", error="provider refused", con=con2)
    a, why = LS.quota_decision("unlucky@carrier.com", "BRS-BOS", con=con2)
    check("a failed send is not a delivered pack, so a retry is free", a == "send")

    # --- files ---------------------------------------------------------------
    LS.add_file(cid, "card_photo", os.path.join(tmp, "card.jpg"), con=con)
    check("a card photo attaches to its record",
          any(e["event"] == "file_added" for e in LS.events_for(cid, con=con)))
    try:
        LS.add_file(cid, "selfie", "x.jpg", con=con)
        check("an unknown file kind is refused", False)
    except LS.LeadStoreError:
        check("an unknown file kind is refused", True)

    # --- migration refuses to lose lines -------------------------------------
    jl = os.path.join(tmp, "demo_leads.jsonl")
    with open(jl, "w", encoding="utf-8") as fh:
        fh.write('{"id":"a1","email":"x@carrier.com","route":"AAA-BBB","status":"sent"}\n')
        fh.write('{"id":"a1","status":"approved+sent","approver":"John"}\n')
        fh.write('{"id":"b2","email":"y@airport.com","route":"CCC-DDD"}\n')
        fh.write('this line is not json\n')
    con3 = LS.connect(os.path.join(tmp, "migrated.duckdb"))
    out = LS.migrate_jsonl(jl, con=con3)
    check("later lines merge onto the same record", out["read"] == 2)
    check("every readable record is written", out["written"] == 2)
    check("unreadable lines are counted, never dropped in silence",
          out["unreadable"] == 1)
    rows = LS.listing(con=con3)
    check("the merged record kept the last status",
          any(r["status"] == "approved+sent" and r["approver"] == "John" for r in rows))
    check("a missing file is reported rather than throwing",
          LS.migrate_jsonl(os.path.join(tmp, "nope.jsonl"), con=con3)["read"] == 0)

    # --- the export ----------------------------------------------------------
    check("the export is one flat sheet of every record",
          len(LS.export_rows(con=con)) == 4)
    check("every column the follow-up needs is present",
          all(c in LS.COLUMN_NAMES for c in
              ("follow_up_owner", "follow_up_date", "notes", "provider_status",
               "pricing_interest", "questions", "arising")))

    # --- the email rule ------------------------------------------------------
    check("a work address passes", LS.email_refusal("jane@evaair.com") is None)
    check("free mail is refused", LS.email_refusal("jane@gmail.com") is not None)
    check("the refusal explains itself",
          "work email" in (LS.email_refusal("j@gmail.com") or ""))

    con.close(); con2.close(); con3.close()
    print("\n%d checks, %d failed%s" % (CHECKS, len(FAIL),
          ": " + ", ".join(FAIL) if FAIL else ""))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
