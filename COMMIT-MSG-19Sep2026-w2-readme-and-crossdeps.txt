W2 status v7: routes/README.md followed, cross-workstream facts taken from source

routes/README.md v1 read. W2 was carrying facts about other workstreams from
memory of this chat; the README requires them to come from the other workstream's
STATUS file, quoted with its version. Done, and two of them were wrong or missing.

CLOSED, from W3-STATUS.md (session 1, 19 Sep): the PDF render W2 recorded as an
undated dependency is not undated. The workstation check passed on 19 September,
Chrome and pikepdf 10.10.0 and pillow 12.3.0 are present, the render is proven end
to end 22-25 September, and John pulled the pack, the PDF and the imagery forward
from 8 October to 3 October. The email has a PDF to attach well before the freeze.

NEW, from W6-STATUS.md (v2, 19 Sep 22:10): W6 is waiting on W2 for two things W2's
own status did not mention. The pack URL rule and hosting controls, so W6 can place
the files by 16 October; W2 will deliver the rule by 3 October to sit beside W3's
pack. And the mail records on the launch domain, which the web cutover must not
disturb.

TWO CONFLICTS RAISED for the controller's sweep. W2 has changed nothing on either.

1. The hosted pack may have nowhere to live. Ruling 15's second email links to a
   pack "hosted on the launched site", and W6 records that the domain is still owed
   and that silence past 29 September makes a fallback landing page the plan. A
   landing page has no place for per-visitor packs, and no route from the
   workstation to a public host has been designed either way. W2's view, offered
   not taken: the single email with the PDF attached removes the dependency.
2. The web cutover could break sending. aviationobservatory.com now carries a DKIM
   TXT, the pm-bounces CNAME and a DMARC TXT. A nameserver move, a host migration
   or the Fasthosts "Restore Default DNS Records" control would remove all three
   and sending would stop silently, first noticed as packs not arriving at Routes.
   W2 asks that no DNS change is made on that domain without W2 reproducing the
   three records at the new host first and verifying them in Postmark afterwards.

Also records what W4 is waiting on from W2: the ruling 18 restart words verbatim
for the host manual, the form and queue view design its sections 3.5, 5.5 and 6.1
are already written against, the tablet answer, and the Postmark approval date.

Documentation only. W2's own file, per the README's ownership table.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01YYBfPojqHJ5EmQipR1awfH
