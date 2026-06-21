# Newborough (NRG) - operating guide

*Replaces the earlier setup map. Reflects the current arrangement: your local
master at ~/projects/NRG is canonical and pushes to GitHub.*

---

## The setup in one picture

- Master: ~/projects/NRG on your machine - this is the source of truth.
- It's a git repo connected to github.com/newbroman/Newborough_Hydrology (NHGR).
- GitHub Pages serves the web tools from there: newbroman.github.io/Newborough_Hydrology/
- The NRG frozen-PL chat clones NHGR fresh each session; your living / forecaster
  work lives in the root living/ folder.

## Folder layout - what goes where

    ~/projects/NRG/
    |- living/    the live side: scripts + hub (readings_living.csv) + the 2 feeds
    |- data/      inputs;  data/geo/ holds the shared KMLs + DEM (WW maps read these)
    |- outputs/   pipeline outputs + outputs/11b_spatial_thresholds/forecaster.html
    |- src/       the 30 pipeline scripts (frozen side)
    |- docs/      report, papers, summaries
    |- index.html  scenario_viewer.html  seasonal_extremes_scatter.html  (web tools, root)
    |- .gitignore

Never published (git-ignored, local only):
venv/, Living_output/ (newsletters), Updates_required/ (work notes),
report.docx (the 189 MB working copy), *.ods except the slim pipeline ODS.

## The monthly routine

    cd ~/projects/NRG && ./nhgr_sync.sh

or just double-click the "Newborough Sync" launcher. It:

  1. pulls anything new from GitHub
  2. stages the web tools to the repo root (copies them up from outputs/)
  3. rebuilds the two forecaster feeds from the hub
  4. shows what changed and asks  "Push? [y/N]"
  5. on y: commits and pushes - Pages refreshes within a minute or two

Nothing is pushed without your y.

## The Water Watch newsletter (separate)

living/run_report.sh builds the monthly newsletter into Living_output/. That
folder is git-ignored - the PDFs stay in Google Drive and go to Facebook as now.
The newsletter never touches GitHub.

## If something goes wrong

- "push failed - sign in": your token expired. Regenerate it on GitHub
  (Settings -> Developer settings -> Personal access tokens), push again, re-enter it.
- "git pull hit a problem": stop, run git status, and send it to the WW chat
  before pushing - don't force anything.

## Coordination

The NRG frozen-PL chat clones NHGR fresh, so it picks up this layout automatically.
Just make sure it knows about root living/ and data/geo/ so it builds on them
rather than reintroducing the old arrangement.
