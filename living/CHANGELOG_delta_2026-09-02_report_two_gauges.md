# CHANGELOG delta — newborough_report.py → v1.3.0 (two local gauges)

**Date:** 2026-09-02
**File:** `living/newborough_report.py` (v1.2.2 → v1.3.0)
**Ruling:** Martin, 2026-09-02 — report all three rainfall sources in the
newsletter, not one local gauge plus Valley.

---

## Why

August 2026 produced three defensible totals for the same month, all with a
complete 31-day record and no spike flags:

| Source | August 2026 |
|---|---|
| IBODOR6 (Bodorgan, PWS) | 84.1 mm |
| ILLANF24 (PWS) | 73.7 mm |
| RAF Valley (Met Office) | 39.2 mm |

Publishing one local figure hides a 10 mm spread between the two private gauges
and a 35–45 mm gap to the regional reference. Worse, the standing note in
`MONTHLY_ROUTINE.md` — that ILLANF24 **over**-reads on intense-rain days — did
not hold this month: ILLANF24 read 12% **low** against Bodorgan. Which local
gauge is the more trustworthy is therefore not a fixed property, and a single
published number implies a confidence the record does not support.

## Changes

**New `--wu_station_2`** (default `IBODOR6`; `DEFAULT_WU_STATION_2` beside the
existing `DEFAULT_WU_STATION`, which stays `ILLANF24`). Passing an empty string
reports one gauge. `--no_wu` suppresses both.

**New step 3b in `generate_monthly_report()`.** Fetches the second gauge after
the primary. Deliberately *reported, not adjudicated*: no
`prompt_alternative_station()` call and no substitution path, so a bad secondary
can never displace the primary. `assess_wu_reliability()` still runs and its
warnings reach the console and the markdown summary. A fetch failure, an absent
second station, or a duplicate of the primary drops the column and leaves the
v1.2.2 output shape untouched.

**`generate_pdf_report()`** — new `wu_result_2` / `wu_station_2` arguments. The
weather table's local-gauge column becomes a list, so the header row is
*Metric / Local (primary) / Local (secondary) / RAF Valley / Typical*. Rainfall
row only; the temperature rows stay Valley-only and are blank across both local
columns, as before. Column widths 32/34/34/32/36 mm = 168 mm, inside the 170 mm
text block (A4 less the 20 mm margins); the four-column path keeps its original
35/40/35/40. The published-total rule (spike-adjusted where a spike was flagged)
is now a nested `_wu_rain_str()` helper applied identically to both gauges,
rather than inline for one.

**`generate_met_summary()`** — new `wu_result_2` / `wu_warnings_2`. The single
"Local station" block became a loop over both gauges, skipping a missing or
duplicate secondary.

**`rainfall_pattern_prose()`** — now names its gauge: "At the IBODOR6 gauge, rain
fell on 12 of 31 days…" instead of "At the local gauge…". With two columns in the
table an unattributed sentence leaves the reader unable to tell which gauge the
daily pattern describes. The paragraph and the structured
`rainfall_summary_*.txt` both stay on the **primary** gauge alone — they need one
daily series, and interleaving two would misdescribe both. The stale
"from the ILLANF24 daily record" wording in the docstring and at the call site
(a hardcoded gauge name of the same family as the v1.2.2 fix) is corrected to
"primary gauge".

## Verified

Both paths were exercised against the live August 2026 data and the artefacts
read back — not merely compiled.

- **Two gauges** (`--wu_station IBODOR6 --wu_station_2 ILLANF24`): PDF table
  renders `84.1 mm | 73.7 mm | 39.2 mm | ~69.4 mm` across five columns with no
  overflow; markdown carries both "Local station" blocks; the pattern paragraph
  reads "At the IBODOR6 gauge".
- **Fallback** (`--wu_station_2 ''`): four-column table, byte-comparable to the
  v1.2.2 layout.
- `--help` lists the new argument; module compiles clean.

## Not changed

Water-level computation, bucketing, maps, CSVs and every figure in the Well
Measurement Summary. This delta touches the Weather Summary only.

## Deploy

Drop into `~/projects/NRG/living/newborough_report.py`. `run_report.sh` needs no
change — it will pick up the default pairing (ILLANF24 primary, IBODOR6
secondary). To publish Bodorgan as the primary figure, as the August 2026 run
did, `run_report.sh` would need `--wu_station IBODOR6 --wu_station_2 ILLANF24`
added to its invocation; that is a separate one-line change, not made here.
