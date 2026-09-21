#!/usr/bin/env python3
r"""The first end-to-end send: prove the transport before anything depends on it.

WORKSTATION ONLY, and it really sends. Nothing else in the demo flow has ever put a
message on the wire: the 67 checks in test_demo_flow.py run against a fake transport
that carries its own sender, which is exactly why the sender-identity fault survived
until the Postmark move. This script closes that gap and nothing else.

WHAT IT PROVES: that the workstation reaches the provider, that the provider ACCEPTED the
message and returned its own identifier for it, and that the From is the intended address
rather than the credential. WHAT IT DOES NOT PROVE: delivery, the DKIM result, or the pack
itself. The attachment here is a plainly labelled transport test, not a forecast pack,
because a pack with invented numbers has no business leaving this building even once.
The pack rides the same transport through /api/demo/request once the lead store is built.

  Workstation Actual, in a window opened AFTER the setx commands:

      cd C:\src\meridian
      py -3.12 app\send_first_pack.py --to john.carter@aviasolutions.com

While the Postmark account is in test mode the recipient must be a confirmed sender
signature on the account, so that is the address to use until approval lands.

Avia Solutions Limited. All rights reserved.
"""
import argparse
import datetime
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import demo_mail as DM


ATTACHMENT = """<!doctype html>
<html lang="en-GB"><head><meta charset="utf-8">
<title>Meridian transport test</title></head><body>
<h1>Meridian transport test</h1>
<p>This file is not a forecast pack. It exists to prove that the Meridian workstation can
send mail through the configured transport, and it carries no figures of any kind.</p>
<p>Sent %s from %s via %s.</p>
<p>Avia Solutions Limited, for The Aviation Observatory.</p>
</body></html>
"""


def main():
    ap = argparse.ArgumentParser(description="Send one real message through demo_mail.")
    ap.add_argument("--to", required=True, help="recipient; in test mode this must be a "
                                                "confirmed Postmark sender signature")
    a = ap.parse_args()

    try:
        transport = DM.default_transport()
    except DM.MailError as e:
        print("NOT SENT. %s" % e)
        return 2

    stamp = datetime.datetime.now().strftime("%d %B %Y at %H:%M")
    print("transport %s" % type(transport).__name__)
    print("from      %s" % transport.sender)
    print("to        %s" % a.to)

    tmp = tempfile.mkdtemp(prefix="meridian_first_send_")
    path = os.path.join(tmp, "Meridian_transport_test.html")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(ATTACHMENT % (stamp, cfg["from"], cfg["host"]))

    try:
        sender = DM.send_pack(
            to=a.to,
            subject="Meridian transport test, %s" % stamp,
            body=("This is a message sent by the Meridian workstation through the "
                  "Observatory's sending domain. It proves the transport only and carries "
                  "no forecast figures.\n\nAvia Solutions Limited."),
            attachment_path=path,
            attachment_name="Meridian_transport_test.html",
            transport=transport)
    except DM.MailError as e:
        print("NOT SENT. %s" % e)
        return 1

    # ACCEPTANCE IS NOT A SOCKET CLOSING WITHOUT COMPLAINT. On 21 September 2026 the SMTP
    # transport reported three successes for messages Postmark never recorded, and this
    # script repeated the claim because nothing had raised. It no longer claims anything
    # the provider has not confirmed by returning an identifier for the message.
    mid = getattr(transport, "last_message_id", None)
    if not mid:
        print("SENT, BUT UNCONFIRMED. The transport raised nothing and returned no provider "
              "identifier, so there is no evidence the message was accepted. Treat this as a "
              "failure until the provider's own record shows otherwise. If this is the SMTP "
              "transport, that is expected: SMTP cannot confirm, which is why the API is the "
              "default.")
        return 3

    print("ACCEPTED by the provider, from %s" % sender)
    print("MessageID %s" % mid)
    print("That identifier is the provider's own record of the message, so acceptance is "
          "proven. Delivery is not: check that it arrived, and look at the headers for the "
          "DKIM result.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
