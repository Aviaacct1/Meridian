# Git setup: run these on the workstation

The initial commit was made from the Cowork session (`42fceb9`), but the sandbox cannot
delete files, so git left stale lock files behind and no further commits could be made
from there. Clear it and redo it properly on the workstation. Two minutes.

## 1. Move the working copy off OneDrive

A `.git` directory inside a OneDrive-synced folder is a known source of repository
corruption: OneDrive rewrites files under git's feet. Put the tool where tools live and
leave OneDrive for documents.

    move "C:\Users\Carte\OneDrive\Documents\Claude\Projects\Avia QSI Tool\Deck Generator\v4" C:\Avia\tools\deck_generator

## 2. Clear the sandbox git state and start clean

    cd C:\Avia\tools\deck_generator
    rmdir /s /q .git
    git init
    git add -A
    git commit -m "Deck generator v4: house-style library, charts, maps, Commons image store, BA LHR-SJC content script"

## 3. Create the private repo and push

    gh repo create aviasolutions/avia-deck-generator --private --source=. --remote=origin --push

Or, without the GitHub CLI, create the empty private repo on github.com first, then:

    git remote add origin https://github.com/aviasolutions/avia-deck-generator.git
    git branch -M main
    git push -u origin main

## 4. Set the config

    copy avia_config.example.json avia_config.json

Then edit `avia_config.json` for this machine. It is gitignored. Paths never go in the code.

## 5. Add it to the platform audit

New tool, new repo, same footing as the others from day one, per the Avia tool standard.

## What is deliberately not in the repo

`assets/` and every `.png`, `.jpg`, `.pptx` and `.pdf` are gitignored. Imagery belongs in
the image store built by `avia_images.py`, at the path in `avia_config.json`, on the
workstation. Generated decks belong in the output directory, not in the tool.

## Working rule from here

Pull before editing, commit and push after. This is the discipline that stops two
divergent copies of the same tool, which is the split we have hit before.
