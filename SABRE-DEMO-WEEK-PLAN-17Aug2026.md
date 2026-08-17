# The week to the Sabre demo: audit remediation plan

Version 1.0, 17 August 2026. Avia Solutions. Companion to "Meridian - Sabre GDD
compliance audit - 16 August 2026.docx" (register R1-R24). John's instruction of
17 August: demo to Sabre within seven days, written approval sought before Routes,
so every remediable item lands this week and the version Sabre sees carries none of
them. This plan re-orders the audit's October sequence to that deadline.

## The shape of the week

R1 first and alone, because history rewriting must precede every other commit.
Then the visible surface (attribution, credits, fares), because that is what Sabre
will look at hardest. Then the reconstitution set at demo-sufficient depth, then
the controls (terms, airline hold, demo mode), then the letter and a dry run.
Build items run in Cowork sessions against C:\AviaDev with commits batched to John
as usual; John's own items are marked.

| Day | Items | Who |
|---|---|---|
| Mon 18 | R1 purge per SABRE-R1-PURGE-RUNBOOK-17Aug2026.md (0.5 day, blocks all other commits). Then the quick batch: R12 GeoNames credit, R13 map attribution on, R16 gate default closed, R19 recent-routes hidden on shared deployments, R24 freshness block trimmed | John (R1), build (rest) |
| Tue 19 | R3+R4 attribution: one shared constant carrying "Sabre Global Demand Data", applied to dashboard, packs, workbook, pitch, economics, catchment, methodology, track record; rails on the five naked surfaces | Build |
| Wed 20 | R5 fares to index/band on self-serve surfaces; R7 payload rounding/banding of measured bases; R8 track record: Sabre-graded routes as ratio and verdict, DB1B absolutes stay | Build |
| Thu 21 | R6 opportunities banding and cap; R9 minimal per-account request/export log and daily caps; R17 terms-of-use click-through mechanism + airline-domain auto-hold (reuses the demo held-pending machinery); legal text slot | Build; ToU text John/counsel |
| Fri 22 | R18 demo mode (pre-loaded samples SJC-TPE, GOA-JFK, EDI-AUS; exports off; watermark). Draft the Sabre confirmation letter (the three asks of audit section 11) and the demo running order | Build + draft |
| Sat 23 | Dry run against the live portal: every demo screen eyeballed for attribution, fares form, banding; fix list closed same day. Buffer | John + build |

In parallel, John, any day: the OAG confirmation letter (R10, the priority letter;
access stays tester-only until answered), the ACI letter (R11), the MAP raster
licence check (R14), the R20 review of the old client-named Sabre O&D pack
deliverable, and booking the Sabre session itself.

## Demo-smoothness items, beyond the register

1. DECIDED (John, 17 August): Teams screen-share from the Dev PC, John signed in
   there; Sabre receives no access of any kind. This is also the 3(b) story told
   live. Practical consequences: the demo runs over the tunnel, so the Saturday
   dry run happens on Teams from the Dev PC against meridian.aviacortex.com, not
   at the workstation, and timings are read from that path (the performance
   memory: keep to the acceptance route; nothing that runs minutes). John's email
   is in the Access policy; OTP sign-in is part of the demo, so it is rehearsed,
   not discovered.
2. Demo route is the acceptance case (SJC-TPE, CI, A359, 5x weekly): known
   numbers, known pass marks, and the story of the k decision behind it if asked.
3. R18 demo mode ON for the session, so what Sabre sees is the conference posture
   they are being asked to approve.
4. The welcome screen counter and recent routes: R19 lands before the demo.
5. QSI_PASSWORD + QSI_DEMO_ENTRY=0 confirmed on the workstation (the origin gate
   check still owed from the Cloudflare work), and R16 makes closed the default.
6. No live sends: the demo-pack email flow is shown on the fixture path if shown
   at all; the aviationobservatory.com mailbox (week-list item 10) is not needed
   for Sabre and stays on its own track.
7. The refresh commissioning (item 8) continues in parallel; a refresh is never
   run on demo day.

## Standing facts this plan honours

The audit's compliant findings (R2, R15, R21, R22, R23) go into the confirmation
letter as architecture facts, not rebuilt. Disclosure posture on remediated items
is John's per the audit's section 11, with counsel input where he wants it. The
one-model rule and the claim-language ruling are untouched by this work. Effort
total per the audit is 6-9 build days; this plan fits it in five by taking the
reconstitution set at demo-sufficient depth first (banding and caps), with the
fuller logging build finishable before October.

Avia Solutions Limited. All rights reserved.
