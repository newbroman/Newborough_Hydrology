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

The newsletter PDF goes to Drive / Facebook — it is **not** pushed to GitHub.

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

- **Master workbook:** `~/Google Drive/projects/newborough/spreadsheets/Newborough_well_records.ods`
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
Flags: `--no_wu`, `--wu_station IBODOR6`, `--no_valley_update`, `--dem`,
`--kml_dir`, `--output_dir`.

---

## Notes

- **Labels follow the report month, not the reading date.** A round read on
  1 July is the June report; the maps, newsletter, and forecaster all say June.
- **Valley climate lag.** The Met Office publishes RAF Valley data a few working
  days after month‑end. If the current month isn't out yet, the report says so;
  run `./living/run_report.sh update` once it's published, then re‑run.
- **Local rain gauge — check it.** The report pulls the local Weather
  Underground gauge **ILLANF24**, which **over‑reads on intense‑rain days**.
  Sanity‑check its monthly total against **IBODOR6 (Bodorgan)** and use Bodorgan
  for the published figure; treat ILLANF24 as *pattern* only. RAF Valley is the
  regional reference. *(A future tidy‑up will switch the report's default gauge
  to IBODOR6.)*
- **"No reading buckets to <month>."** The Absolute Level column for that month
  isn't in the master yet, or it's dated outside the end‑of‑month / first‑15‑days
  window.
- **The forecaster is self‑updating.** Once the wired page is deployed, you never
  rebuild it — pushing the monthly feeds is enough. Script 11b is only needed
  when the *template* or the *frozen pipeline science* changes, not for a
  monthly reading.
