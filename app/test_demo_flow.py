#!/usr/bin/env python3
"""Offline fixture tests for the demo pack flow (item 7): quota, lead store, domain
check, mail transport against a fake, watermark, and the warned-run refusal. No stores,
no server, no live send.

    py -3.12 test_demo_flow.py

Every address, route and number here is a TEST FIXTURE.

Avia Solutions Limited. All rights reserved.
"""
import base64
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import demo_leads as DL
import demo_mail as DM
import demo_pack as DP

FAIL = []
CHECKS = 0


def check(name, cond, detail=""):
    global CHECKS
    CHECKS += 1
    print("%-58s %s %s" % (name, "PASS" if cond else "FAIL", detail))
    if not cond:
        FAIL.append(name)


# --- the business-email check ----------------------------------------------

def test_domains():
    check("work address passes", DL.email_refusal("jane@evaair.com") is None)
    check("gmail refused", DL.email_refusal("jane@gmail.com") is not None)
    check("proton refused", DL.email_refusal("j@proton.me") is not None)
    check("case and space normalised", DL.email_refusal("  Jane@EvaAir.COM ") is None)
    check("no at sign refused", DL.email_refusal("janeevaair.com") is not None)
    check("no dot in domain refused", DL.email_refusal("jane@localhost") is not None)
    check("blank refused", DL.email_refusal("") is not None)
    check("refusal is polite, not a code",
          "email" in (DL.email_refusal("j@gmail.com") or "").lower())


# --- the lead store ---------------------------------------------------------

def test_store_roundtrip(tmp):
    os.environ["AVIA_DEMO_LEADS"] = os.path.join(tmp, "leads", "demo_leads.jsonl")
    i1 = DL.append_event({"email": "a@b-air.com", "route": "AAA-BBB", "consent": True,
                          "status": "sent", "pack": "p.html"})
    DL.append_event({"id": i1, "email": "a@b-air.com", "route": "AAA-BBB",
                     "status": "failed", "reason": "later event moves the status on"})
    events, bad = DL.read_events()
    check("two events read back", len(events) == 2 and bad == 0)
    rec = DL.merged(events)[i1]
    check("later event wins the status", rec.get("status") == "failed")
    check("first event keeps its fields", rec.get("pack") == "p.html")
    check("ts stamped on every line", all(e.get("ts") for e in events))
    with open(DL.leads_path(), "a", encoding="utf-8") as fh:
        fh.write("this line is not JSON\n")
    events, bad = DL.read_events()
    check("corrupt line counted, not guessed", len(events) == 2 and bad == 1)
    try:
        DL.append_event({"email": "x@y-air.com", "status": "posted"})
        check("unknown status refused", False)
    except ValueError:
        check("unknown status refused", True)


def test_quota(tmp):
    os.environ["AVIA_DEMO_LEADS"] = os.path.join(tmp, "quota.jsonl")

    def decide(email, route):
        events, _ = DL.read_events()
        return DL.quota_decision(email, route, DL.merged(events))

    a, r = decide("new@airline.com", "SJC-TPE")
    check("first ever request is free", a == "send" and r is None)
    DL.append_event({"email": "new@airline.com", "route": "SJC-TPE", "status": "sent"})
    a, r = decide("new@airline.com", "SJC-TPE")
    check("same route again is held", a == "pending")
    check("duplicate reason names the route", "SJC-TPE" in (r or ""))
    a, r = decide("new@airline.com", "GOA-JFK")
    check("a further route is held", a == "pending")
    check("further-route reason shows history", "SJC-TPE" in (r or ""))
    a, _ = decide("other@airport.aero", "SJC-TPE")
    check("quota is per email, not per route", a == "send")
    # a failed send is not a delivered pack
    DL.append_event({"email": "unlucky@carrier.com", "route": "BRS-BOS",
                     "status": "failed", "reason": "smtp down"})
    a, _ = decide("unlucky@carrier.com", "BRS-BOS")
    check("retry after a failure is free", a == "send")
    # an outstanding held request blocks a second automatic send
    DL.append_event({"email": "eager@airline.com", "route": "EDI-AUS",
                     "status": "pending", "held": True})
    a, r = decide("eager@airline.com", "LHR-SJC")
    check("outstanding held request holds the next", a == "pending")
    # approved+sent counts as delivered
    DL.append_event({"email": "vip@airline.com", "route": "LCY-JFK",
                     "status": "approved+sent", "approver": "JC"})
    a, _ = decide("vip@airline.com", "LCY-JFK")
    check("approved+sent counts as delivered", a == "pending")


def test_history(tmp):
    os.environ["AVIA_DEMO_LEADS"] = os.path.join(tmp, "hist.jsonl")
    DL.append_event({"email": "a@x-air.com", "route": "AAA-BBB", "status": "sent"})
    DL.append_event({"email": "b@y-air.com", "route": "CCC-DDD", "status": "sent"})
    DL.append_event({"email": "A@X-AIR.com", "route": "EEE-FFF", "status": "pending",
                     "held": True})
    events, _ = DL.read_events()
    hist = DL.history_for("a@x-air.com", DL.merged(events))
    check("history is per email, case-blind", len(hist) == 2)
    check("history excludes other people",
          all("y-air" not in (h.get("email") or "") for h in hist))


def test_coerce():
    defaults = {"freq": 7, "plan_lf": 0.875, "split_floor": 1, "econ": True,
                "season": "annual", "seats": 0.0}
    out = DL.coerce_params({"freq": "5", "plan_lf": "0.9", "split_floor": "0",
                            "econ": "true", "season": "summer", "seats": "306",
                            "unknown_key": "1"}, defaults)
    check("int cast", out.get("freq") == 5)
    check("float cast", out.get("plan_lf") == 0.9)
    check("bool '0' is False, not truthy", out.get("split_floor") == 0)
    check("bool 'true' is True", out.get("econ") is True)
    check("string passes through", out.get("season") == "summer")
    check("unknown key dropped", "unknown_key" not in out)
    out = DL.coerce_params({"freq": "seven"}, defaults)
    check("junk value falls back by omission", "freq" not in out)


# --- the mail transport -----------------------------------------------------

class FakeTransport:
    sender = "meridian@aviationobservatory.com"

    def __init__(self, fail=False):
        self.fail = fail
        self.sent = []

    def send(self, msg):
        if self.fail:
            raise DM.MailError("fixture transport told to fail")
        self.sent.append(msg)


def test_mail(tmp):
    for var in ("AVIA_SMTP_USER", "AVIA_SMTP_PASS"):
        os.environ.pop(var, None)
    try:
        DM.config()
        check("missing credentials raise", False)
    except DM.MailError as e:
        check("missing credentials raise", True)
        check("the error names the variables", "AVIA_SMTP_USER" in str(e))
    pack = os.path.join(tmp, "pack.html")
    with open(pack, "w", encoding="utf-8") as fh:
        fh.write("<html><body>fixture pack</body></html>")
    t = FakeTransport()
    sender = DM.send_pack(to="jane@evaair.com", subject="Your Meridian route forecast",
                          body="fixture body", attachment_path=pack,
                          attachment_name="Meridian_Forecast_DEMO.html", transport=t)
    check("fake transport got one message", len(t.sent) == 1)
    msg = t.sent[0]
    check("sender is the transport's mailbox", sender == FakeTransport.sender
          and msg["From"] == FakeTransport.sender)
    check("recipient carried", msg["To"] == "jane@evaair.com")
    atts = [p for p in msg.iter_attachments()]
    check("pack attached with its name", len(atts) == 1
          and atts[0].get_filename() == "Meridian_Forecast_DEMO.html")
    try:
        DM.send_pack(to="jane@evaair.com", subject="s", body="b",
                     attachment_path=pack, transport=FakeTransport(fail=True))
        check("a refused send raises, never drops", False)
    except DM.MailError:
        check("a refused send raises, never drops", True)
    try:
        DM.send_pack(to="j@x.com", subject="s", body="b",
                     attachment_path=os.path.join(tmp, "no_such_pack.html"),
                     transport=FakeTransport())
        check("a missing pack file raises", False)
    except DM.MailError:
        check("a missing pack file raises", True)


# --- the pack: refusal and watermark ----------------------------------------

SHELL_FIXTURE = """<!DOCTYPE html>
<html lang="en-GB"><head><meta charset="utf-8">
<title>SJC to TPE</title>
<style>html,body{margin:0;}</style></head>
<body><div class="deck">
<section data-label="cover">fixture cover</section>
<section data-label="summary">fixture summary</section>
</div></body></html>"""



# --- the sender identity (19 September 2026, the Postmark move) --------------
# The credential and the sending address are not the same thing. Under M365 they
# coincided, so demo_mail took the From from the username and nothing noticed. Under
# Postmark the username is a 36-character Server API token, and a token in a From header
# is not a deliverable message. These checks exist because the fixture transport above
# carries its own sender, so the line that broke was the one line the fixtures never
# reached: the first live send would have been the test.

def _clear_smtp_env():
    for var in ("AVIA_SMTP_HOST", "AVIA_SMTP_PORT", "AVIA_SMTP_USER",
                "AVIA_SMTP_PASS", "AVIA_SMTP_FROM"):
        os.environ.pop(var, None)


def test_sender_identity():
    token = "a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d"      # a token shape, not an address

    # Postmark: token as the credential, the sender named separately.
    _clear_smtp_env()
    os.environ["AVIA_SMTP_HOST"] = "smtp.postmarkapp.com"
    os.environ["AVIA_SMTP_USER"] = token
    os.environ["AVIA_SMTP_PASS"] = token
    os.environ["AVIA_SMTP_FROM"] = "john.carter@aviationobservatory.com"
    cfg = DM.config()
    check("postmark: the sender is the FROM, not the token",
          cfg["from"] == "john.carter@aviationobservatory.com")
    check("postmark: the credential is kept separate", cfg["user"] == token)
    check("postmark: a token never reaches the From", "@" in cfg["from"]
          and cfg["from"] != cfg["user"])
    t = DM.SmtpTransport(cfg=cfg)
    check("transport takes its sender from the FROM", t.sender == cfg["from"])

    # Postmark with no FROM: the username cannot stand in, so it must say so.
    os.environ.pop("AVIA_SMTP_FROM", None)
    try:
        DM.config()
        check("a token username with no FROM raises", False)
    except DM.MailError as e:
        check("a token username with no FROM raises", True)
        check("the error names AVIA_SMTP_FROM", "AVIA_SMTP_FROM" in str(e))

    # M365 and anything else where the login is the mailbox: unchanged behaviour.
    _clear_smtp_env()
    os.environ["AVIA_SMTP_HOST"] = "smtp.office365.com"
    os.environ["AVIA_SMTP_USER"] = "meridian@aviationobservatory.com"
    os.environ["AVIA_SMTP_PASS"] = "pw"
    cfg = DM.config()
    check("an address username still stands in as the sender",
          cfg["from"] == "meridian@aviationobservatory.com")

    # The host no longer defaults to Microsoft.
    _clear_smtp_env()
    os.environ["AVIA_SMTP_USER"] = token
    os.environ["AVIA_SMTP_PASS"] = token
    os.environ["AVIA_SMTP_FROM"] = "john.carter@aviationobservatory.com"
    try:
        DM.config()
        check("an unset host raises rather than defaulting to Microsoft", False)
    except DM.MailError as e:
        check("an unset host raises rather than defaulting to Microsoft", True)
        check("the error names AVIA_SMTP_HOST", "AVIA_SMTP_HOST" in str(e))
    _clear_smtp_env()



# --- the API transport (21 September 2026) -----------------------------------
# The regression lock for the day SMTP lied. Postmark's SMTP endpoint accepted three
# messages its own policy forbade, reported success each time, and recorded none. The API
# refused the identical message with ErrorCode 412 and said why. These checks hold the
# behaviour that made the difference: a refusal must raise, and must carry Postmark's own
# words, because those words were the whole diagnosis.

class FakePoster:
    """Stands in for the HTTP call. Records what was posted; returns what it is told to."""

    def __init__(self, status=200, body=None):
        self.status, self.body = status, body or {"ErrorCode": 0, "Message": "OK",
                                                  "MessageID": "fake-message-id"}
        self.calls = []

    def __call__(self, url, body, headers):
        self.calls.append({"url": url, "payload": json.loads(body.decode("utf-8")),
                           "headers": headers})
        raw = self.body if isinstance(self.body, bytes) else json.dumps(self.body).encode()
        return self.status, raw


def _api_env():
    _clear_smtp_env()
    os.environ["AVIA_SMTP_USER"] = "a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d"
    os.environ["AVIA_SMTP_FROM"] = "john.carter@aviationobservatory.com"


def test_api_transport(tmp):
    _api_env()
    pack = os.path.join(tmp, "apipack.html")
    with open(pack, "w", encoding="utf-8") as fh:
        fh.write("<html><body>fixture pack</body></html>")

    # a good send
    poster = FakePoster()
    t = DM.ApiTransport(poster=poster)
    sender = DM.send_pack(to="jane@evaair.com", subject="Your Meridian route forecast",
                          body="fixture body", attachment_path=pack,
                          attachment_name="Meridian_Forecast_DEMO.html", transport=t)
    check("api: sends from AVIA_SMTP_FROM", sender == "john.carter@aviationobservatory.com")
    check("api: one call made", len(poster.calls) == 1)
    sent = poster.calls[0]
    check("api: posts to Postmark's endpoint", sent["url"] == DM.API_ENDPOINT)
    check("api: the token travels in the header",
          sent["headers"].get("X-Postmark-Server-Token") == os.environ["AVIA_SMTP_USER"])
    p = sent["payload"]
    check("api: From carried", p["From"] == "john.carter@aviationobservatory.com")
    check("api: To carried", p["To"] == "jane@evaair.com")
    check("api: subject carried", p["Subject"] == "Your Meridian route forecast")
    check("api: body carried", "fixture body" in p["TextBody"])
    check("api: stream named", p["MessageStream"] == "outbound")
    check("api: attachment carried with its name",
          len(p["Attachments"]) == 1
          and p["Attachments"][0]["Name"] == "Meridian_Forecast_DEMO.html")
    check("api: attachment content is base64 of the file",
          base64.b64decode(p["Attachments"][0]["Content"]).decode() ==
          "<html><body>fixture pack</body></html>")
    check("api: the MessageID is kept", t.last_message_id == "fake-message-id")

    # THE 21 SEPTEMBER FAULT: a refusal must raise, carrying Postmark's own words.
    refusal = {"ErrorCode": 412, "Message": ("While your account is pending approval, all "
                                             "recipient addresses must share the same domain "
                                             "as the 'From' address.")}
    t = DM.ApiTransport(poster=FakePoster(status=422, body=refusal))
    try:
        DM.send_pack(to="jane@evaair.com", subject="s", body="b", transport=t)
        check("api: a refused message raises rather than reporting success", False)
    except DM.MailError as e:
        check("api: a refused message raises rather than reporting success", True)
        check("api: the error carries Postmark's ErrorCode", "412" in str(e))
        check("api: the error carries Postmark's own words",
              "must share the same domain" in str(e))
        check("api: no MessageID is invented on failure", t.last_message_id is None)

    # a body that is not JSON is reported, not swallowed
    t = DM.ApiTransport(poster=FakePoster(status=502, body=b"<html>bad gateway</html>"))
    try:
        DM.send_pack(to="jane@evaair.com", subject="s", body="b", transport=t)
        check("api: a non-JSON answer raises", False)
    except DM.MailError as e:
        check("api: a non-JSON answer raises", True)
        check("api: the error names the HTTP status", "502" in str(e))

    # the selector
    _api_env()
    check("the default transport is the api",
          isinstance(DM.default_transport(), DM.ApiTransport))
    os.environ["AVIA_MAIL_TRANSPORT"] = "smtp"
    os.environ["AVIA_SMTP_HOST"] = "smtp.postmarkapp.com"
    os.environ["AVIA_SMTP_PASS"] = os.environ["AVIA_SMTP_USER"]
    check("smtp is still selectable",
          isinstance(DM.default_transport(), DM.SmtpTransport))
    os.environ["AVIA_MAIL_TRANSPORT"] = "carrier pigeon"
    try:
        DM.default_transport()
        check("an unknown transport raises", False)
    except DM.MailError as e:
        check("an unknown transport raises", True)
        check("the error names the variable", "AVIA_MAIL_TRANSPORT" in str(e))
    _clear_smtp_env()
    os.environ.pop("AVIA_MAIL_TRANSPORT", None)


def test_refusal():
    try:
        DP.refuse_if_warned({"ok": True, "warnings": ["the feed layer crashed"]})
        check("a warned run is refused", False)
    except RuntimeError as e:
        check("a warned run is refused", True)
        check("the refusal names the warning", "feed layer" in str(e))
    try:
        DP.refuse_if_warned({"ok": False, "error": "no such pair"})
        check("a failed run is refused", False)
    except RuntimeError:
        check("a failed run is refused", True)
    try:
        DP.refuse_if_warned({"ok": True, "warnings": []})
        check("a clean run passes", True)
    except RuntimeError:
        check("a clean run passes", False)


def test_run_ref():
    a = DP.run_ref({"origin": "SJC", "dest": "TPE", "freq": "5"})
    b = DP.run_ref({"freq": "5", "dest": "TPE", "origin": "SJC"})
    c = DP.run_ref({"origin": "SJC", "dest": "TPE", "freq": "7"})
    check("run_ref is order-blind", a == b)
    check("run_ref separates different runs", a != c)
    check("run_ref is short and printable", len(a) == 12 and a.isalnum())


def test_watermark():
    out = DP.stamp_demonstration(SHELL_FIXTURE)
    check("stylesheet stamp in the head",
          "DEMONSTRATION" in out.split("</head>")[0])
    check("stamp is CSS generated content, no element to delete",
          "section::after" in out)
    check("banner present after body", "avia-demo-banner" in out.split("<body>")[1])
    check("title amended", "<title>DEMONSTRATION" in out)
    # deleting the one visible element leaves the stylesheet layer standing
    stripped = out.replace(DP._BANNER, "")
    check("watermark survives deleting the banner",
          "section::after" in stripped and "DEMONSTRATION" in stripped.split("</head>")[0])
    # a page with no markers still gets stamped rather than silently passing clean
    bare = DP.stamp_demonstration("<div>no shell markers at all</div>")
    check("markerless page still stamped", "DEMONSTRATION" in bare
          and "avia-demo-banner" in bare)


def test_pack_html_render(tmp):
    """The join the demo flow stands on: a forecast-pack spec renders to Observatory
    HTML and takes the watermark. A thin fixture contract, so thin blocks must drop by
    name rather than throw; this is the path that found _bullets could not take
    forecast_pack's bare-string notes."""
    deck_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "deck")
    if deck_dir not in sys.path:
        sys.path.insert(0, deck_dir)
    import forecast_pack as FP
    import deck_spec as S
    import render_observatory as RO
    contract = {
        "route_metadata": {"origin_airport": "SJC", "destination_airport": "TPE",
                           "airline_name": "Fixture Air", "frequency_per_week": 5,
                           "aircraft_type": "A359", "seats": 306, "service_year": 2027},
        "economics_year1": {"total_load_factor": 0.828},
        "segment_forecast": {"summary": {
            "grand_total": {"forecast": 131812, "base_annual_demand": 100000},
            "point_to_point_total": {"forecast": 60000},
            "connecting_at_hub_total": {"forecast": 50000},
            "connecting_at_destination_total": {"forecast": 21812}}},
        "summary_and_schedule": {"point_to_point_market": 90000},
        "_settings": {"split_floor": True},
    }
    spec, dropped = FP.build_pack(contract, codename="Fixture",
                                  prepared_for="jane@evaair.com",
                                  confidentiality="DEMONSTRATION",
                                  author="The Aviation Observatory")
    spec["meta"]["status"] = "DEMONSTRATION"
    S.paginate(spec)
    out = os.path.join(tmp, "pack.html")
    RO.render(spec, out, embed=True, resolver=None, check=False)
    with open(out, encoding="utf-8") as fh:
        html = fh.read()
    stamped = DP.stamp_demonstration(html)
    check("thin contract renders, pages present", len(spec["slides"]) >= 8)
    check("thin blocks drop by name, not by throw", "competition" in dropped)
    check("plain-string notes render (the _bullets fix)",
          "carried, after the plan load factor cap" in html)
    check("cover carries DEMONSTRATION from the spec", "DEMONSTRATION" in html)
    check("rendered pack takes the watermark",
          "section::after" in stamped and "avia-demo-banner" in stamped)


def main():
    keep = {k: os.environ.get(k) for k in ("AVIA_DEMO_LEADS", "AVIA_SMTP_HOST",
                                           "AVIA_SMTP_PORT", "AVIA_SMTP_USER",
                                           "AVIA_SMTP_PASS", "AVIA_SMTP_FROM",
                                           "AVIA_MAIL_TRANSPORT", "AVIA_POSTMARK_TOKEN")}
    try:
        with tempfile.TemporaryDirectory() as tmp:
            test_domains()
            test_store_roundtrip(tmp)
            test_quota(tmp)
            test_history(tmp)
            test_coerce()
            test_mail(tmp)
            test_sender_identity()
            test_api_transport(tmp)
            test_refusal()
            test_run_ref()
            test_watermark()
            test_pack_html_render(tmp)
    finally:
        for k, v in keep.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    print("\n%d checks, %d failed%s" % (CHECKS, len(FAIL),
          ": " + ", ".join(FAIL) if FAIL else ""))
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
