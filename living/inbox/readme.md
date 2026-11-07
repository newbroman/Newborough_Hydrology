Drop this month's files here. Everything in this directory is gitignored: these
are the month's inputs, read in place, not part of either repository.

| file | where it comes from | read by |
|---|---|---|
| `valleydata.txt` | Met Office, RAF Valley station data — `./run_report.sh update` fetches it | `newborough_report.py --valley` |
| `weather-history-<YYYY>-<MM>-01_<STATION>.csv` | Weather Underground, the **Export CSV** button on the station's table view | `newborough_report.py` finds it itself (`find_wu_export`) |
| `well-levels-<date>.csv`, `well-gps-<date>.csv`, `well-track-<date>.gpx` | the Well Logger app, that round | `intake_monthly.py` |

## The Weather Underground exports

Two stations are configured — **IBODOR4** (Rhianfa, 6.6 km) and **IHOLYH29**
(Capel Gwyn, 14.2 km). Open each station's table view for the month, click
**Export CSV**, and **add the station to the filename**:

    weather-history-2026-10-01.csv   ->   weather-history-2026-10-01_IBODOR4.csv

That rename is not tidiness. WU's download carries **neither the station nor the
year inside it** — its `Time` column is a bare `10/1` — so both stations' exports
for one month arrive under the same name with nothing in either file to tell them
apart. The report reads `Precip. Accum.`, never `Precip. Rate` (Rate is the day's
peak, and taking it over-reported October 2026 by 64%).

`wu_<STATION>_<YYYY-MM>.csv` works too, and so does any `.csv` whose name carries
both the station and `YYYY-MM`. Two candidates for one station-month are
**refused**, not guessed — name one properly, or pass `--wu_csv`.
