#!/usr/bin/env python3
r"""The first end-to-end send: prove the transport before anything depends on it.

WORKSTATION ONLY, and it really sends. Nothing else in the demo flow has ever put a
message on the wire: the 67 checks in test_demo_flow.py run against a fake transport
that carries its own sender, which is exactly why the sender-identity fault survived
until the Postmark move. This script closes that gap and nothing else.

WHAT IT PROVES: that the workstation can authenticate to the configured SMTP host, that
the message is accepted, that it is signed by the verified domain, and that the From
address is the one intended rather than the credential. WHAT IT DOES NOT PROVE: the pack
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
        cfg = DM.config()
    except DM.MailError as e:
        print("NOT SENT. %s" % e)
        return 2

    stamp = datetime.datetime.now().strftime("%d %B %Y at %H:%M")
    print("host     %s:%s" % (cfg["host"], cfg["port"]))
    print("from     %s" % cfg["from"])
    print("to       %s" % a.to)
    print("credential length %d (never printed)" % len(cfg["user"]))
    if cfg["from"] == cfg["user"]:
        print("NOTE: the sending address and the credential are identical. That is correct "
              "for M365 and wrong for Postmark; check AVIA_SMTP_FROM before reading the "
              "result as a pass.")

    tmp = tempfile.mkdtemp(prefix="meridian_first_send_")
    path = os.path.join(tmp, "Meridian_transport_test.html")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(ATTACHMENT % (stamp, cfg["from"], cfg["host"]))

    try:
        sender = DM.send_pack(
            to=a.to,
            subject="Meridian transport test, %s" % stamp,
            body=("This is the first message sent by the Meridian workstation through the "
                  "Observatory's sending domain. It proves the transport only and carries "
                  "no forecast figures.\n\nAvia Solutions Limited."),
            attachment_path=path,
            attachment_name="Meridian_transport_test.html")
    except DM.MailError as e:
        print("NOT SENT. %s" % e)
        return 1

    print("SENT from %s" % sender)
    print("Now check three things in Postmark, Activity: that it shows as delivered, that "
          "the DKIM column reads pass, and that the From is the address above and not a "
          "token. Then check the message actually arrived, and look at its headers.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
