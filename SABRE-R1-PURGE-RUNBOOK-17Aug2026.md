# R1: purging the raw Sabre extracts from the repository

Version 1.0, 17 August 2026. Avia Solutions. Audit item R1 (Sabre GDD compliance
audit, 16 August 2026). John runs every command; nothing here is run from a Cowork
session. Do this FIRST, before any other audit fix lands, so no further history
builds on top of the files.

The three tracked files, verified against the git index on 17 August:

    app/OD Italy 202503-202602.xlsx
    app/POS Milan 202503-202602.xlsx
    app/syd_per_sabre.csv

History rewriting is destructive, so the order is: backup, remove from the tree,
purge history on a fresh clone, force push, re-base every clone. Dev PC throughout.

## Step 1: safety mirror (keeps every ref as it stands)

    cd C:\src
    git clone --mirror https://github.com/Aviaacct1/Meridian.git meridian-backup-17Aug2026.git

## Step 2: move the files out of the tree and commit the removal

    cd C:\AviaDev
    New-Item -ItemType Directory -Force C:\Avia_extracts | Out-Null
    Move-Item "app\OD Italy 202503-202602.xlsx" C:\Avia_extracts\
    Move-Item "app\POS Milan 202503-202602.xlsx" C:\Avia_extracts\
    Move-Item "app\syd_per_sabre.csv" C:\Avia_extracts\
    Add-Content .gitignore "`n# Raw Sabre MI extracts never enter the repo (audit R1, 17 Aug 2026)"
    Add-Content .gitignore "OD *.xlsx"
    Add-Content .gitignore "POS *.xlsx"
    Add-Content .gitignore "syd_per_sabre.csv"
    git add -A
    git commit -m "R1: raw Sabre MI extracts leave the repository (compliance audit, 16 Aug 2026)"
    git push

C:\Avia_extracts is a waypoint: the files' home is the workstation data root
(E:\Avia\extracts), moved there when convenient, and the Dev PC copy deleted.

## Step 3: purge the history (fresh clone; filter-repo requires one)

    py -3.12 -m pip install git-filter-repo
    cd C:\src
    git clone https://github.com/Aviaacct1/Meridian.git meridian-purge
    cd meridian-purge
    git filter-repo --invert-paths --path "app/OD Italy 202503-202602.xlsx" --path "app/POS Milan 202503-202602.xlsx" --path "app/syd_per_sabre.csv"
    git remote add origin https://github.com/Aviaacct1/Meridian.git
    git push --force --all origin
    git push --force --tags origin

## Step 4: re-base every clone (history is rewritten; old clones must not push)

On the Dev PC, both copies:

    cd C:\AviaDev
    git fetch origin
    git reset --hard origin/main

    cd C:\src\meridian
    git fetch origin
    git reset --hard origin/main

On donatello (ssh):

    cd C:\src\meridian
    git fetch origin
    git reset --hard origin/main

The working tree content is identical after the reset; only the history changes.
The four tags survive, rewritten.

## Step 5: verify, and one GitHub fact

    git log --all --oneline -- "app/OD Italy 202503-202602.xlsx"

must return nothing, in C:\AviaDev and on donatello. Note: after a force push,
GitHub can hold unreachable objects in its own caches until it runs garbage
collection; for a private single-user repository this is a housekeeping matter,
and GitHub support will run the collection on request if wanted. The mirror
backup from step 1 is retained offline until the purge is confirmed good, then
deleted, since it also contains the extracts.

## One look while in there

APD_Round2/ carries seventeen analysis CSVs from the APD engagement. The audit
judged them derived aggregates (repackaged analysis, permitted), not raw
extracts; worth one confirming glance while the purge tooling is open, since a
second purge later costs another force push everywhere.

Avia Solutions Limited. All rights reserved.
