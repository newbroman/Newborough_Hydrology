# Newborough Warren Monthly Water Level Report

> Save this as `README.md` in the report project folder (alongside
> `run_report.sh` and `newborough_report.py`).

## Quick Start

```bash
chmod +x run_report.sh
./run_report.sh
```

The script handles everything: Python check, venv creation, package
installation, Valley data download, and report generation.

---

## What changed (2026-06) — deterministic month matching

`newborough_report.py` now allocates each ODS reading to a calendar month by
your **field rule**, instead of "nearest date within 45 days". This makes every
report reproducible and removes the ambiguity around early-next-month readings.

**The rule (how a reading's date maps to a month):**

| Reading dated… | Counts as |
|----------------|-----------|
| day **after the 15th** of a month | **that** month |
| day **on or before the 15th** of a month | the **previous** month |

So a reading dated **4 June is May's level**; **31 May is also May**;
**2 July is June**. This is applied to the report month, the previous month
(month-on-month), the same month last year (year-on-year), and the August
baseline (rebound-from-summer-low) — all four columns are now chosen the same
deterministic way.

**Consequences you'll notice:**
- Asking for an **old month** (`./run_report.sh 2025-01`) now returns *that*
  month's figures, not the latest reading — re-runs are identical every time.
- If the requested month's column **isn't in the sheet yet**, the script stops
  with a clear message instead of silently using a nearby reading.
- If the **previous** month is missing, the month-on-month map is skipped but
  year-on-year and the August baseline still run.

**To deploy:** drop the new `newborough_report.py` into the project folder
(over the old one). Nothing else changes — same `run_report.sh`, same flags,
same outputs.

---

## Layout: Cloud vs Local

The project folder lives on Google Drive. The Python virtual environment lives
locally on your machine to avoid syncing thousands of small files.

```
Google Drive (synced & backed up)                Local only (not synced)
---------------------------------                ----------------------
~/Google Drive/.../newborough_reports/            ~/.newborough_venv/
|-- run_report.sh                                |-- bin/
|-- newborough_report.py   <- replace with new   |-- lib/
|-- README.md                                    \-- ...
|-- data/
|   |-- Newborough_well_records.ods  <- you update this monthly
|   |-- Well_locations_height.csv     <- static (well positions/heights)
|   |-- newborough_dem.tif            <- static
|   \-- valleydata.txt                <- auto-downloaded
|-- kml/
|   |-- Features.kml
|   |-- broadleaf_restock.kml
|   |-- clearfell.kml
|   \-- streams.kml
\-- output/                           <- reports, maps, CSVs
```

> **Check the filename.** `run_report.sh` auto-detects the `.ods` in `data/`.
> Make sure the file it reads is the **corrected** records workbook (the one
> with the FE / L7 / PDFS fixes). The project has carried more than one
> `Newborough_well_records.ods` - keep a single current copy in `data/` so the
> report can't read a stale one.

The venv at `~/.newborough_venv` is created automatically on first run.
If you ever need to rebuild it: `./run_report.sh clean` then re-run.

---

## Monthly Workflow

1. Add the new month's readings to the records workbook in `data/`
   (**Absolute Level** sheet). **Date the new column** by when you actually
   took the readings - the field rule above does the rest. (A column dated
   4 June is read as the May report month.)
2. Run:
   ```bash
   ./run_report.sh 2026-05
   ```

That's it. Valley data is fetched automatically from the Met Office. WU local
gauge data is fetched and cross-checked automatically too.

## Commands

| Command | What it does |
|---------|-------------|
| `./run_report.sh` | Interactive - prompts for month |
| `./run_report.sh 2026-05` | Generate May 2026 report |
| `./run_report.sh setup` | First-time setup only |
| `./run_report.sh update` | Download latest Valley data |
| `./run_report.sh clean` | Remove local venv (to rebuild) |

## Output

Each run produces in `output/`:
- `report_YYYY_MM.md` - markdown report with full well tables
- `Newborough_Water_Watch_YYYY_MM.pdf` - formatted PDF newsletter
- `map_month_*.png` - month-on-month difference map
- `map_yoy_*.png` - year-on-year difference map
- `map_cumulative_*.png` - rebound from summer low map
- `*.csv` - difference data (E, N, Z)

## Advanced: Running the Python Script Directly

```bash
source ~/.newborough_venv/bin/activate
python newborough_report.py 2026-05 --no_wu --no_valley_update
```

Flags: `--no_wu`, `--wu_station IBODOR6`, `--no_valley_update`,
`--dem path`, `--kml_dir path`, `--output_dir path`

## Notes

- **Month matching** is now deterministic (field rule, see top). If a report
  errors with "no reading buckets to <month>", the column for that month isn't
  in the Absolute Level sheet yet, or it's dated outside the end-of-month /
  first-15-days window.
- **Valley data.** Reports are produced promptly — e.g. June's readings by the
  second working day of July — whereas the Met Office updates the Valley station
  file on a rolling monthly basis. So the just-finished month's climate data
  usually isn't published yet when you run the report. The script handles the
  missing current month gracefully; once the Met Office publishes it, run
  `./run_report.sh update` to fetch the new file, then generate the report
  as usual.
- **ILLANF24** has sensor spike issues. The script detects these and prompts
  you to choose: use anyway, skip, or try another station.
- **IBODOR6** (Bodorgan) is a reliable alternative local gauge.
- **differenc__demCSV_creatorA.ods** is NOT needed - the CSV has the same
  coordinate data.
