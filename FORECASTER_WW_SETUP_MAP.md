# Newborough — Living / Water Watch: where things live & how to run it

*The live-data / Water Watch workstream. This supersedes every earlier version of
this map — earlier drafts described a `src/living/` + `ww/` + `data/living/`
structure that was never built. The real structure is a single `living/` folder
inside the git clone, described below.*

---

## The one home

Everything runs from the git clone at **`~/projects/NRG`** (the same folder
`nrg_git.sh` syncs). There is no second copy. The old Google Drive
`projects/newborough/NHGR` folder has been archived and must not be used.

```
~/projects/NRG/                         ← THE home (git clone)
├── living/
│   ├── run_report.sh                    WW newsletter + difference maps  (v2.0.0+)
│   ├── newborough_report.py             the report engine
│   ├── intake_monthly.py                logger/recordsheet → master column + QA
│   ├── seed_living_hub.py               one-time: frozen mAOD → hub
│   ├── update_forecaster_feed.py        monthly: hub → latest_readings.json
│   ├── update_forecaster_msl5.py        monthly: hub → forecaster_msl5.json
│   ├── msl_common.py                    van Willegen MSL5 core (shared w/ Script 26)
│   ├── readings_living.csv              the hub (committed)
│   ├── latest_readings.json             forecaster feed (committed)
│   ├── forecaster_msl5.json             forecaster MSL5 feed (committed)
│   ├── inbox/    ← PUT THIS MONTH'S FILES HERE (gitignored)
│   │      well-levels-YYYY-MM-DD.csv     logger dumps here
│   │      recordsheet.ods                manual sheet (if used)
│   │      valleydata.txt                 auto-fetched by run_report.sh
│   └── output/   ← WW newsletters + maps (gitignored → Drive/Facebook)
│          <year>/<Month>/ ...
├── data/         well_metadata.csv (Name,E,N,…), RAF_Valley_Climate.csv
├── data/geo/     newborough_dem.tif + KMLs (Features, streams, clearfell, …)
├── outputs/11b_spatial_thresholds/forecaster.html   ← consumes ../../living/*.json
├── src/ srcBW/ outputs/ docs/           the frozen pipeline (other chat's world)
└── nrg_git.sh                           git toolkit (sync / push / pull / size / gc)
```

### The private master — left on Google Drive

The master workbook is **not** in the clone and **not** in git. One canonical copy
lives on Drive and the scripts read it in place:

```
~/Google Drive/projects/newborough/spreadsheets/Newborough_well_records.ods
```

`run_report.sh` and `intake_monthly.py` point at that path (set once, at the top
of `run_report.sh` as `MASTER_ODS`). Keeping a single copy there avoids the
stale-duplicate problem and preserves Drive's backup.

---

## The report month rule (important)

A reading round driven **at month-end / early next month is the *previous*
month's level**. A column dated **1 July is the June level** (field rule:
day ≤ 15 → previous month). So you write up the month *before* the round you drove:

```
1-Jul reading  →  ./living/run_report.sh 2026-06
```

`run_report.sh` with no month defaults to "last month", which is usually correct.

---

## Monthly routine

```
1.  ./nrg_git.sh            → 3) Pull latest
2.  drop the logger CSV (and recordsheet, if used) into  living/inbox/
3.  (optional) cross-check logger vs recordsheet          [passed 0.0 cm, Jul 2026]
4.  update the master ODS with the new month              (LibreOffice, as now)
5.  ./living/run_report.sh <report-month>                 → living/output/<yr>/<Mon>/
6.  regenerate the two forecaster feeds (commands below)
7.  ./nrg_git.sh            → 2) Push   (hub + feeds; newsletter PDF optional)
```

### Step 6 — regenerate feeds

```bash
cd ~/projects/NRG
python3 living/update_forecaster_feed.py \
    --hub living/readings_living.csv \
    --cluster-map outputs/03_master_data.csv \
    --out living/latest_readings.json

python3 living/update_forecaster_msl5.py \
    --hub living/readings_living.csv \
    --cluster-map outputs/03_master_data.csv \
    --out living/forecaster_msl5.json
```

---

## What is / isn't pushed

| Pushed to git (public)          | Local only (gitignored)              |
|---------------------------------|--------------------------------------|
| living/ scripts                 | living/inbox/ (logger, recordsheet, valleydata) |
| readings_living.csv (the hub)   | living/output/ (newsletters, maps)   |
| latest_readings.json            | the master ODS (on Drive)            |
| forecaster_msl5.json            | ~/.newborough_venv (outside the repo)|

The **Water Watch newsletter PDF** is a Drive/Facebook deliverable, not normally a
git artefact — push it only if you want it published in the repo.

---

## Still to wire (not yet done)

- **Hub append.** `intake_monthly.py` computes and QA-checks a new month but the
  append into `readings_living.csv` is not yet wired, so the forecaster feeds
  currently run off the seeded hub only. Until this lands, the feeds don't move
  between springs (MSL5 is annual anyway), but the current-levels feed won't
  reflect the newest round until the hub grows.

---

## The git part, plainly

`./nrg_git.sh` does it all: **3) Pull** before you start, **2) Push** when you're
done (it commits first, then pulls, then pushes, and asks which version wins on a
conflict). **5) Repo size** and **6) Clean up git storage** are there if `.git`
ever bloats.
