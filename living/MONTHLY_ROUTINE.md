# Newborough Warren — Monthly Routine

Everything you do each month, in order. There are **two jobs**:

1. **Water Watch newsletter** — the PDF + difference maps.
2. **Live forecaster update** — grow the hub and refresh the feeds the online
   forecaster reads.

Both run from your clone at `~/projects/NRG`. (This replaces the old
`README_report.md`, which described the earlier Google‑Drive folder layout.)

---

## The one rule to remember: which month?

A reading round is driven at the **end of a month or the first day or two of the
next**, and it is the **previous month's** level. A column dated **1 July is
June**. So you always write up / update for the month *before* the round you
drove out to read.

| Reading dated… | Counts as |
|----------------|-----------|
| on/before the 15th | the **previous** month |
| after the 15th | **that** month |

Both tools default to "last month" (usually right); or pass the month
explicitly, e.g. `2026-06`.

---

## Step 0 — update the master (once per month, in LibreOffice)

Add the month's readings to `recordsheet.ods` in `~/Downloads`. The master
workbook on Google Drive
(`…/spreadsheets/Newborough_well_records.ods`) picks them up through its live
link — no manual copying. That master is the single source both tools read.

---

## Job 1 — Water Watch newsletter

```bash
cd ~/projects/NRG
./living/run_report.sh 2026-06        # or: ./living/run_report.sh  (it prompts)
```

Produces, in `living/output/2026/June/`:

- `Newborough_Water_Watch_2026_06.pdf` — the newsletter
- `report_2026_06.md` — full markdown report with well tables
- `map_month_*.png`, `map_yoy_*.png`, `map_cumulative_*.png` — the three maps
- rainfall + difference CSVs

The newsletter PDF goes to Drive / Facebook, **and** to the public site (since 2026-10-08):

```bash
python3 living/publish_water_watch.py 2026-06               # the run_report.sh PDF
python3 living/publish_water_watch.py 2026-06 --pdf my.pdf  # or the PDF you exported after editing the ODT
```

It copies the issue into `water_watch/` (map images recompressed, about 1–2 MB an issue) and
rebuilds `water_watch/index.html`; the next push puts it on
https://newbroman.github.io/Newborough_Hydrology/water_watch/index.html once the web tools are republished (nrg_git.sh option 13 - Pages serves the gh-pages branch, not main). `run_report.sh` also writes an
editable `.odt` beside the PDF.

---

## Job 2 — Live forecaster update

```bash
cd ~/projects/NRG
./living/forecaster_monthly_update.sh 2026-06    # or answer the prompt
```

This one command: pulls, grows the hub with the month's round, rebuilds the
three forecaster feeds, and commits + pushes them (it confirms before pushing).

**No pipeline, no Script 11b, no rebuild of the page.** The deployed forecaster
fetches the feeds, so it picks up the new month on the next page load.
The site is served from the gh-pages branch, so the feeds reach it only when the web tools are
republished (`./working/nrg_git.sh`, option 13); a push to main alone leaves the live forecaster on
the previous month (found 2026-10-08: the site still showed August).

---

## One‑time setup

Everything runs from the clone; the scripts live in `living/`. Make them
executable once:

```bash
chmod +x ~/projects/NRG/living/run_report.sh
chmod +x ~/projects/NRG/living/forecaster_monthly_update.sh
chmod +x ~/projects/NRG/nrg_git.sh
```

Paths the scripts use (each has a config block at the top — edit only if yours
move):

- **Master workbook:** `~/Drive/01 Projects/Newborough research/spreadsheets/Newborough_well_records.ods` (moved 2026-10-10 with the Drive tidy; `~/Drive` is the rclone mount)
- **Workbook backup (T-116):** each night, just before restic runs, the L14 backup copies the `.ods` files
  only from that `spreadsheets/` folder into a folder under `~/backups` (copy line below), so restic keeps dated versions of the
  workbook (`~/Drive` itself is excluded from restic; the USB drive-mirror keeps overwritten files by date in its `--backup-dir`, but restic adds the regular daily/weekly/monthly snapshots). Only `*.ods`:
  the folder also holds a file that must never be copied into a backup or the repo. Copy line:
  `rclone copy "gdrive:01 Projects/Newborough research/spreadsheets" ~/backups/well_records --include "*.ods"`
- **Recordsheet:** `~/Downloads/recordsheet.ods`
- **Coordinates / DEM / KML:** `data/well_metadata.csv`, `data/geo/` — already in
  the repo, nothing to place
- **Python venv:** `~/.newborough_venv` — created automatically on the first
  report run (`./living/run_report.sh setup` to do it explicitly)

---

## Where things live

```
~/projects/NRG/                     the git clone — everything runs from here
├── living/
│   ├── run_report.sh                 Water Watch newsletter + maps
│   ├── forecaster_monthly_update.sh  grow hub + rebuild feeds + push
│   ├── newborough_report.py          the report engine
│   ├── intake_monthly.py             readings → hub
│   ├── update_forecaster_feed.py     ┐
│   ├── update_forecaster_msl5.py     ├ the three feed generators
│   ├── update_forecaster_indices.py  ┘
│   ├── readings_living.csv           the hub (grows each month)
│   ├── latest_readings.json          ┐
│   ├── forecaster_msl5.json          ├ feeds the forecaster reads
│   ├── forecaster_indices.json       ┘
│   ├── inbox/                         monthly inputs (gitignored)
│   └── output/<year>/<Month>/         newsletters + maps (gitignored)
├── data/   data/geo/                 coords, DEM, KMLs
└── nrg_git.sh                        git toolkit (pull / push / status / size)
```

---

## Commands reference

**Report** — `./living/run_report.sh`

| command | what it does |
|---|---|
| `run_report.sh` | prompts for the month |
| `run_report.sh 2026-06` | generate June's report |
| `run_report.sh update` | fetch the latest RAF Valley data |
| `run_report.sh setup` | first‑time env setup only |
| `run_report.sh clean` | remove the venv (to rebuild it) |

**Forecaster** — `./living/forecaster_monthly_update.sh` (prompts, or pass `2026-06`).

**Git** — `./nrg_git.sh` (pull / push / status / repo size / cleanup). The
forecaster script pushes for you, so you only need this for other changes.

**Run the report engine directly** (rarely needed):
```bash
source ~/.newborough_venv/bin/activate
python living/newborough_report.py 2026-06 --no_wu --no_valley_update
```
Flags: `--no_wu`, `--wu_station IBODOR4`, `--wu_station_2 IHOLYH29`,
`--no_valley_update`, `--dem`, `--kml_dir`, `--output_dir`. `--wu_csv` /
`--wu_csv_2` are for an export kept somewhere other than `living/inbox/`.

---

## Notes

- **Labels follow the report month, not the reading date.** A round read on
  1 July is the June report; the maps, newsletter, and forecaster all say June.
- **Valley climate lag.** The Met Office publishes RAF Valley data a few working
  days after month‑end. If the current month isn't out yet, the report says so;
  run `./living/run_report.sh update` once it's published, then re‑run.
- **Local rain gauges — download two CSVs into `living/inbox/`.** Corrected
  2026-11-07; the note here until then named **ILLANF24** and **IBODOR6**, and
  **both of those stations are dead** — ILLANF24's dashboard says OFFLINE and
  IBODOR6 renders no readings. The gauges are now **IBODOR4 (Rhianfa**, 6.6 km)
  and **IHOLYH29 (Capel Gwyn**, 14.2 km), and the report no longer scrapes: WU
  stopped serving the observations the scraper read, and the only key on offer is
  WU's own (T-163). Open each station's **table view** for the month, click
  **Export CSV**, and **add the station to the filename** before dropping it in
  `living/inbox/`:

      weather-history-2026-10-01.csv  ->  weather-history-2026-10-01_IBODOR4.csv

  The report then finds both by itself — no `--wu_csv` needed. The rename is not
  tidiness: WU's download carries **neither the station nor the year inside it**
  (its `Time` column is a bare `10/1`), so both stations' exports for one month
  arrive under the same name with nothing to tell them apart. Two candidates for
  one station-month are refused rather than guessed. RAF Valley remains the
  regional reference, and the two gauges are each other's cross-check — October
  2026: 87.4 and 115.1 mm with Valley's 101.8 between them. See
  `living/inbox/readme.md`.
- **"No reading buckets to <month>."** The Absolute Level column for that month
  isn't in the master yet, or it's dated outside the end‑of‑month / first‑15‑days
  window.
- **The forecaster is self‑updating.** Once the wired page is deployed, you never
  rebuild it — pushing the monthly feeds is enough. Script 11b is only needed
  when the *template* or the *frozen pipeline science* changes, not for a
  monthly reading.
