# Kickoff: 15 August 2026

Paste everything below into the new chat as the first message.

---

FIRST, THE MOUNT, BEFORE YOU READ ANYTHING ELSE

Cowork attaches the PROJECT folder automatically, which is
`C:\Users\Carte\OneDrive\Documents\Claude\Projects\Avia QSI Tool`. THAT IS NOT THE REPO. It holds the
handovers and kickoffs and it also holds a STALE `app\` copy that predates the connecting build and
looks exactly like a working copy. Do not read it and never write to it.

THE REPO IS `C:\AviaDev`. ASK FOR IT YOURSELF with the folder-access tool before you read a line of
code.

`E:\Avia` IS ON THE WORKSTATION AND COWORK CANNOT MOUNT IT. Do not try. Anything under E: has to be
read by a command John runs, so ask for the one command that gets you what you need rather than a
series of round trips.

THE TWO MACHINES, and do not get this wrong:

* Dev PC, where editing happens: `C:\AviaDev`
* Workstation, where running happens: `C:\src\meridian`, data root `E:\Avia`

Code moves ONLY by git push on the Dev PC then git pull on the Workstation. Never tell John to run
something you have just written without that step first. LABEL EVERY COMMAND BLOCK WITH THE MACHINE
and put a cd in front of every command.

NEVER RUN GIT, not even a read-only `git status`. It strands `.git\index.lock` on the mount and blocks
John's commits. Answer provenance questions with `ls`, `md5sum` and reading files. Hand John commit
messages as files and he runs every git command himself. Tell him to run `git status --short` and read
it BEFORE composing any `git add`, and name only the files you wrote.

PowerShell: `$env:NAME = "value"`, never `set`. ONE-LINE commands, no backtick continuations.

DO NOT USE THE MULTIPLE-CHOICE QUESTION TOOL. It does not render for John. Put questions in the body
of the message as numbered plain text, with your recommendation named.

READ FIRST: `C:\AviaDev\HANDOVER-15Aug2026.md`, then `bt2/bt2_experiments.log` from the 14 August
entries, most recent last. The 14 August entries close several things and reopen one, so read them
before proposing anything.

---

WHERE THINGS STAND, 14 August evening

The portal runs on the QSI engine. The deck data contract was fixed on 14 August and is now held by
four invariants in `app/contract_legs_check.py`; 16 of 16 cases pass. `deck/forecast_pack.py` renders
a 13-page forecast pack from a contract with a clean content budget.

Three things closed on 14 August and should not be reopened: the optimiser objective needed no code,
LF-CAP-OPEN is closed with 0.875 kept on measurement, and the seats defect and the curfew cost are
shipped. The handover explains each.

One thing reopened. The 25,999 the log had been reconciling the connecting leg against is the 2025
analyst's BASE YEAR, not his forecast. His forecast is 34,600. On the matched year our connecting leg
reads 19% BELOW his and our local leg 14% above, and they offset, which is why the total agrees within
3%. Do not quote the total agreement without saying that.

---

JOB 1, AND IT IS FIRST: DOT DATA FOR THE US MARKET

John's ruling: US airports do not trust Sabre, they trust US government data. Tampa, San Jose and
O'Hare will not buy a product that reads a GDS sample for their own domestic market. This is
commercial, not cosmetic.

`app/od_source.py` already implements the rule and is default off behind `AVIA_OD_SOURCE`. Turning it
on does not fix SJC-TPE: it governs the POINT TO POINT market and selects DB1B only for all-US
markets, and SJC-TPE is international. The leg that is entirely US domestic is the behind-San Jose
feed, built in `route_feed`, and `route_feed` does not consult `od_source` at all.

Three pieces, in order: route the behind leg through `od_source`; carry its source label into the
payload and the contract the way `forecast_engine` and `feed_level` already report themselves; then
set the default, with `auto` recommended for US markets.

Until it is done the source line stays "Sabre MI and OAG". Writing DOT DB1B onto a slide produced from
a Sabre run is the same fault as the four found in the contract, committed on purpose.

Re-measure after: changing the behind leg's source changes the connecting forecast.

---

JOB 2: JOHN'S CORRECTIONS TO THE FORECAST PACK

Listed in full in the handover under Job 2, in three groups: straightforward, needs a column the
contract does not carry, and needs a build. The straightforward ones are the missing images (the pack
renders without an `avia_slots.SlotResolver`), the disclaimer wording, and the connecting table
columns. The traffic forecast table needs base annual demand at the forecast year BEFORE stimulation,
which the contract does not carry. The catchment page needs a map with population at each end, and
`deck_contract` records that those figures were never wired.

---

JOB 3: THE COMPETITION SPLIT

The analyst captures competed and uncompeted O&Ds at different rates, 0.0% against 1.5% at Taipei and
0.2% against 4.7% at San Jose. Meridian has one blended rate per side. It is the best candidate for
the 19% connecting gap and it also produces two rows the forecast table needs, so it serves Jobs 2 and
3 together.

---

WHAT TO DO FIRST

Ask for `C:\AviaDev`. Read the handover and the 14 August log entries. Then ask John which job to
start, in plain text and not with the question tool, and do not write code before he answers. If he
has no preference, start with Job 1, because it is the product rather than the presentation and every
US airport conversation depends on it.

Avia Solutions Limited. All rights reserved.
