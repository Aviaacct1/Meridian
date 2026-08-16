#!/usr/bin/env python3
r"""M365 SMTP transport for the demonstration pack (John's choice, 16 August 2026).

smtp.office365.com:587 with STARTTLS. Configuration comes from the environment or the
gitignored secrets file, never the repo:

    AVIA_SMTP_HOST   default smtp.office365.com
    AVIA_SMTP_PORT   default 587
    AVIA_SMTP_USER   the sending mailbox (meridian@aviationobservatory.com once live)
    AVIA_SMTP_PASS   its password

The sender IS the user: M365 SMTP AUTH rejects a From that is not the authenticated
mailbox unless SendAs is granted, so nothing here invents a separate From address.

FAIL LOUDLY. A missing variable or a refused send raises MailError with the reason in
plain words; the caller records the lead with status failed. A failed send is never
silently dropped, because a lead that vanishes is a person at Routes who was promised
a pack and did not get one.

Tested against a fake transport, never a live send: anything with a send(msg) method
can stand in for SmtpTransport.

Avia Solutions Limited. All rights reserved.
"""
import os
import smtplib
import ssl
from email.message import EmailMessage


class MailError(RuntimeError):
    """Raised for anything that stops a message going out, with the reason stated."""


def config():
    """The four settings, read at call time. Raises MailError naming what is missing,
    so 'the demo email is broken' is never the whole of the diagnosis."""
    host = os.environ.get("AVIA_SMTP_HOST", "").strip() or "smtp.office365.com"
    try:
        port = int(os.environ.get("AVIA_SMTP_PORT", "").strip() or "587")
    except ValueError:
        raise MailError("AVIA_SMTP_PORT is set but is not a number")
    user = os.environ.get("AVIA_SMTP_USER", "").strip()
    pw = os.environ.get("AVIA_SMTP_PASS", "")
    missing = [n for n, v in (("AVIA_SMTP_USER", user), ("AVIA_SMTP_PASS", pw)) if not v]
    if missing:
        raise MailError("mail is not configured on this server: %s not set (setx on the "
                        "workstation, new window to pick it up)" % " and ".join(missing))
    return {"host": host, "port": port, "user": user, "password": pw}


class SmtpTransport:
    """The real thing. One connection per send: the demo sends single messages minutes
    apart, and a held-open connection to M365 times out between them."""

    def __init__(self, cfg=None):
        self.cfg = cfg or config()
        self.sender = self.cfg["user"]

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
    t = transport or SmtpTransport()
    sender = getattr(t, "sender", None)
    if not sender:
        raise MailError("the transport names no sender address")
    msg = build_message(sender, to, subject, body, attachment_path, attachment_name)
    t.send(msg)
    return sender
