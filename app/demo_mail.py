#!/usr/bin/env python3
r"""M365 SMTP transport for the demonstration pack (John's choice, 16 August 2026).

smtp.office365.com:587 with STARTTLS. Configuration comes from the environment or the
gitignored secrets file, never the repo:

    AVIA_SMTP_HOST   the SMTP host. REQUIRED, no default (see below)
    AVIA_SMTP_PORT   default 587
    AVIA_SMTP_USER   the credential the host authenticates
    AVIA_SMTP_PASS   its password
    AVIA_SMTP_FROM   the address mail is sent from

THE CREDENTIAL AND THE SENDER ARE NOT THE SAME THING, and assuming they were would have
broken the first live send. Under M365 they coincide: SMTP AUTH rejects a From that is
not the authenticated mailbox, so the username is both. Postmark, which is the supplier
from 19 September 2026, authenticates with a Server API token and takes the From from
the account's verified domains, so a username is a 36-character token and putting it in
a From header produces a message no receiver will accept. AVIA_SMTP_FROM therefore names
the sender explicitly. It falls back to AVIA_SMTP_USER only when that looks like an
address, which keeps the M365 behaviour exactly as it was.

AVIA_SMTP_HOST HAS NO DEFAULT, deliberately. It defaulted to smtp.office365.com, which
after the move to Postmark meant an unset variable would send the server at the wrong
supplier and fail with an authentication error naming Microsoft. A missing setting now
says so in plain words instead.

FAIL LOUDLY. A missing variable or a refused send raises MailError with the reason in
plain words; the caller records the lead with status failed. A failed send is never
silently dropped, because a lead that vanishes is a person at Routes who was promised
a pack and did not get one.

Tested against a fake transport, never a live send: anything with a send(msg) method
can stand in for SmtpTransport.

Avia Solutions Limited. All rights reserved.
"""
import base64
import json
import os
import smtplib
import ssl
import urllib.error
import urllib.request
from email.message import EmailMessage


class MailError(RuntimeError):
    """Raised for anything that stops a message going out, with the reason stated."""


def config():
    """The four settings, read at call time. Raises MailError naming what is missing,
    so 'the demo email is broken' is never the whole of the diagnosis."""
    host = os.environ.get("AVIA_SMTP_HOST", "").strip()
    try:
        port = int(os.environ.get("AVIA_SMTP_PORT", "").strip() or "587")
    except ValueError:
        raise MailError("AVIA_SMTP_PORT is set but is not a number")
    user = os.environ.get("AVIA_SMTP_USER", "").strip()
    pw = os.environ.get("AVIA_SMTP_PASS", "")
    sender = os.environ.get("AVIA_SMTP_FROM", "").strip()
    if not sender and "@" in user:
        sender = user          # M365 and anything else where the login IS the mailbox
    missing = [n for n, v in (("AVIA_SMTP_HOST", host), ("AVIA_SMTP_USER", user),
                              ("AVIA_SMTP_PASS", pw)) if not v]
    if missing:
        raise MailError("mail is not configured on this server: %s not set (setx on the "
                        "workstation, new window to pick it up)" % " and ".join(missing))
    if not sender:
        raise MailError("AVIA_SMTP_FROM is not set, and AVIA_SMTP_USER is not an address "
                        "to fall back to. With Postmark the username is a Server API "
                        "token, not a mailbox, so the sending address has to be named: "
                        "set AVIA_SMTP_FROM to an address on a domain verified in the "
                        "Postmark account.")
    return {"host": host, "port": port, "user": user, "password": pw, "from": sender}


class SmtpTransport:
    """The real thing. One connection per send: the demo sends single messages minutes
    apart, and a held-open connection to M365 times out between them."""

    def __init__(self, cfg=None):
        self.cfg = cfg or config()
        # The FROM, never the credential. See the module docstring: under Postmark the
        # username is a token and a token in a From header is not a deliverable message.
        self.sender = self.cfg["from"]

    def send(self, msg):
        c = self.cfg
        try:
            with smtplib.SMTP(c["host"], c["port"], timeout=60) as s:
                s.ehlo()
                s.starttls(context=ssl.create_default_context())
                s.ehlo()
                s.login(c["user"], c["password"])
                s.send_message(msg)
        except smtplib.SMTPAuthenticationError as e:
            raise MailError("M365 refused the sign-in for %s: %s (is SMTP AUTH enabled "
                            "for the mailbox?)" % (c["user"], e))
        except (smtplib.SMTPException, OSError) as e:
            raise MailError("send via %s:%s failed: %s: %s"
                            % (c["host"], c["port"], type(e).__name__, e))


API_ENDPOINT = "https://api.postmarkapp.com/email"


def _api_token():
    """The Postmark Server API token. AVIA_SMTP_USER is accepted because that is where it
    already lives on the workstation: Postmark uses the same token as the SMTP username."""
    return (os.environ.get("AVIA_POSTMARK_TOKEN", "").strip()
            or os.environ.get("AVIA_SMTP_USER", "").strip())


class ApiTransport:
    """Postmark's HTTP API. THE DEFAULT since 21 September 2026, and here is why.

    SMTP was the original transport and it lied. On 21 September Postmark's SMTP endpoint
    accepted three messages that its own policy forbade, reported success every time, and
    recorded none of them; its API refused the identical message with ErrorCode 412 and a
    sentence naming the reason (recipients must share the From domain while an account is
    pending approval). Three hours went into chasing a fault that the API would have named
    in one call. A transport that cannot tell a refusal from a delivery has no business
    behind a promise of a pack within thirty minutes.

    It also returns a MessageID, which is what the queue view needs in order to show a pack
    as accepted by the provider rather than merely handed to a socket.

    poster is injectable for tests: anything taking (url, body_bytes, headers) and returning
    (status_int, body_bytes) can stand in, so the checks never touch the network.
    """

    def __init__(self, token=None, sender=None, poster=None):
        self.token = token or _api_token()
        self.sender = sender or os.environ.get("AVIA_SMTP_FROM", "").strip()
        if not self.token:
            raise MailError("no Postmark token: set AVIA_POSTMARK_TOKEN, or AVIA_SMTP_USER, "
                            "which holds the same value on the workstation")
        if not self.sender:
            raise MailError("AVIA_SMTP_FROM is not set, so there is no sending address")
        self._post = poster or self._http_post
        self.last_message_id = None

    @staticmethod
    def _http_post(url, body, headers):
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.getcode(), r.read()
        except urllib.error.HTTPError as e:
            return e.code, e.read()          # Postmark puts the reason in the error body
        except OSError as e:
            raise MailError("could not reach %s: %s: %s" % (url, type(e).__name__, e))

    @staticmethod
    def payload_from(msg):
        """The API's fields, taken from the same EmailMessage the SMTP transport sends, so
        both transports carry an identical message and neither can drift from the other."""
        text = ""
        body = msg.get_body(preferencelist=("plain",))
        if body is not None:
            text = body.get_content()
        atts = []
        for part in msg.iter_attachments():
            data = part.get_payload(decode=True) or b""
            atts.append({"Name": part.get_filename() or "attachment",
                         "Content": base64.b64encode(data).decode("ascii"),
                         "ContentType": part.get_content_type()})
        out = {"From": msg["From"], "To": msg["To"], "Subject": msg["Subject"],
               "TextBody": text}
        if atts:
            out["Attachments"] = atts
        return out

    def send(self, msg):
        payload = self.payload_from(msg)
        payload["MessageStream"] = os.environ.get("AVIA_POSTMARK_STREAM", "").strip() or "outbound"
        headers = {"X-Postmark-Server-Token": self.token,
                   "Accept": "application/json", "Content-Type": "application/json"}
        status, raw = self._post(API_ENDPOINT, json.dumps(payload).encode("utf-8"), headers)
        try:
            data = json.loads(raw.decode("utf-8", "replace"))
        except ValueError:
            raise MailError("Postmark answered HTTP %s with something that is not JSON: %s"
                            % (status, raw[:200]))
        code = data.get("ErrorCode")
        if status >= 400 or code:
            raise MailError("Postmark refused the message (HTTP %s, ErrorCode %s): %s"
                            % (status, code, data.get("Message", "no reason given")))
        self.last_message_id = data.get("MessageID")


def default_transport():
    """api unless told otherwise. SMTP stays available and is not the default: see
    ApiTransport's docstring for what it cost on 21 September 2026."""
    which = (os.environ.get("AVIA_MAIL_TRANSPORT", "").strip().lower() or "api")
    if which == "api":
        return ApiTransport()
    if which == "smtp":
        return SmtpTransport()
    raise MailError("AVIA_MAIL_TRANSPORT must be 'api' or 'smtp', not %r" % which)


def build_message(sender, to, subject, body, attachment_path=None, attachment_name=None):
    """A plain-text message with the pack attached as a self-contained HTML file."""
    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    if attachment_path:
        name = attachment_name or os.path.basename(attachment_path)
        try:
            with open(attachment_path, "rb") as fh:
                data = fh.read()
        except OSError as e:
            raise MailError("the pack file could not be read for sending: %s" % e)
        msg.add_attachment(data, maintype="text", subtype="html", filename=name)
    return msg


def send_pack(to, subject, body, attachment_path=None, attachment_name=None,
              transport=None):
    """Build and send. transport is injectable for tests; None means the real SMTP
    transport built from the environment. Returns the sender address used."""
    t = transport or default_transport()
    sender = getattr(t, "sender", None)
    if not sender:
        raise MailError("the transport names no sender address")
    msg = build_message(sender, to, subject, body, attachment_path, attachment_name)
    t.send(msg)
    return sender
