> ## Recovered 2026-08-26 — CLOSED, kept as the record
>
> Written **2026-08-08**, never committed, recovered from Trash (it had been in
> `~/Downloads`) under T-10 and kept **verbatim below**.
> `GEOMETRY_ARCHITECTURE_SPEC.md` §7 step 5 cites it as the hub-recompute
> instruction.
>
> **Both items are closed. Do not run the commands below** — they were written
> against the 2026-08-08 state and re-running them now would re-do work that has
> already landed. Verified 2026-08-26 against the committed hub and metadata:
>
> - **Item 2 — the missing rounds: done.** The hub runs continuously through
>   2026-01 … 2026-07 at 73–77 wells a month. The three gaps the note found
>   (2026-03, 2026-04, 2026-05) are filled, and so is the fourth it spotted while
>   counting (2026-07). 15,402 rows.
> - **Item 1 — `ceh13`: closed the other way.** The note recommended Option A,
>   reverting `Pipe_Top_Elev` to 11.415. That was **not** what happened.
>   `data/well_metadata.csv` still carries **11.325**, and `ceh13`'s implied
>   ground is now constant across its whole series — so the series was rebuilt on
>   the corrected geometry rather than reverted to the old one. That is Option B
>   in the note's terms, but arrived at properly: not as a one-well exception,
>   but as part of the site-wide geometry rework recorded in
>   `GEOMETRY_ARCHITECTURE_SPEC.md`, which is exactly the "handle the geometry
>   properly across all wells as a single change" the note asked for.
>
> **The note's own verification test now passes.** Implied ground
> (`water_mAOD − depth_below_ground`, 3 dp) is a per-well constant everywhere
> except `llynrhos`, which holds two values 1 mm apart across 183 rows — a single
> row, 2024-03-01, and precisely the 3-dp rounding artefact the note predicted.
> Not a defect.
>
> **The open question at the end is still open**, and still worth an answer: was
> `ceh13`'s `Pipe_Top_Elev` edited deliberately in `a75f693`, or did it ride along
> with the metre/cm fix? It no longer affects the correction, but it bears on
> whether the same thing happened elsewhere.
>
> ---

# Hub correction note — before the next forecaster update

**Scope:** two independent items. Item 1 is a one-cell metadata revert plus one hub
value. Item 2 is three missing rounds. Neither requires a pipeline run.

**Audit status:** no files have been changed. Everything below is a proposed action
for your sign-off.

---

## Item 1 — `ceh13`: what actually happened

You were right that this is a transcription-style error, not a lineage split. My
earlier reading of it was wrong. The git history settles it.

Commit `a75f693` (2026-07-04, *"forecaster june update"*) changed **9 lines** of
`data/well_metadata.csv`. Eight are alias additions (`clearing` → `clearing;c`,
`FE1` → `f1`, and so on). **Exactly one is a numeric change:**

```
- ceh13,240964.108,364066.298,11.325,11.235,0.09,11.415,False,879.0,nr 2a
+ ceh13,240964.108,364066.298,11.325,11.235,0.09,11.325,False,879.0,nr 2a
                                                    ^^^^^^ Pipe_Top_Elev
```

`Pipe_Top_Elev` went **11.415 → 11.325** in the same commit as the metre/cm fix. No
other well's geometry moved. That single cell is what produced the step I flagged.

### Why it produced a step, and why only in one column

From `intake_monthly.py` (lines 204–205):

```
wte = pipe_top_elev - depth      -> depends on Pipe_Top_Elev
dfs = upstand      - depth      -> does NOT depend on Pipe_Top_Elev
```

So the edit moved `water_mAOD` and left `depth_below_ground` untouched.

Working the June row back: `dfs` = 0.077 = 0.09 − depth, so **depth = 0.013 m**.

| | Pipe_Top_Elev | water_mAOD | depth_below_ground |
|---|---|---|---|
| 219 historical rows (seeded pre-edit) | 11.415 | on this basis | 0.077-equivalent |
| June 2026 row (computed post-edit) | 11.325 | **11.312** | 0.077 |
| June 2026 on the historical basis | 11.415 | **11.402** | 0.077 |

**`depth_below_ground` is identical under either geometry.** It is the only column
`update_forecaster_msl5.py` reads (line 42), so MSL5 and the newsletter are unaffected
by this. `update_forecaster_feed.py` reads both, so `latest_readings.json` currently
carries a `water_mAOD` for `ceh13` that is 0.090 m below the rest of its own series.

### The correction — restore uniformity now, fix geometry globally later

Two coherent options. Note that 11.325 is arguably the *more correct* pipe top
(see the geometry findings in the defect register), but adopting it for `ceh13` alone
leaves that well on a different basis from the other 98.

**Recommended — Option A, revert to uniform:**

1. In `data/well_metadata.csv`, restore `ceh13` `Pipe_Top_Elev` to **11.415**.
2. In `living/readings_living.csv`, change the `ceh13` `2026-06` row:
   `water_mAOD` **11.312 → 11.402**. Leave `depth_below_ground` at 0.077.
3. Re-run the feed generators.

**Option B, adopt corrected geometry for ceh13 only:** leave the metadata at 11.325
and lower all 219 historical `ceh13` `water_mAOD` values by 0.090. Internally
consistent, but makes `ceh13` the only well on the corrected basis.

I'd take Option A to unblock this month, and handle the geometry properly across all
wells as a single change once you've ruled on the register items.

**Verification after either fix** — implied ground must be a per-well constant:

```bash
python3 -c "
import pandas as pd
d = pd.read_csv('living/readings_living.csv')
d['ig'] = (d.water_mAOD - d.depth_below_ground).round(3)
g = d.groupby('well').ig.nunique()
print('wells with a non-constant implied ground:', (g > 1).sum())
print(g[g > 1])
"
```

Expect `0`. (Five wells — ceh1, ceh2, nw7, nw9, llynrhos — vary by exactly 1 mm from
3-dp rounding; rounding to 3 dp as above absorbs that.)

---

## Item 2 — the three missing 2026 rounds

Confirmed absent from the committed hub: **2026-03, 2026-04, 2026-05.** The hub jumps
2026-02 → 2026-06. (2005-06 and 2022-12 are genuine field gaps — no action.)

**The readings exist.** The master workbook's `depth from surface` sheet has 283
reading-date columns, ending:

```
31/10/2025, 04/12/2025, 06/01/2026, 02/02/2026, 28/02/2026,
30/03/2026, 02/05/2026, 04/06/2026, 01/07/2026, 03/08/2026
```

Applying the bucketing rule from `MONTHLY_ROUTINE.md` (on/before the 15th → previous
month; after the 15th → that month):

| master column | month it is | in the hub? |
|---|---|---|
| 30/03/2026 | **2026-03** | missing |
| 02/05/2026 | **2026-04** | missing |
| 04/06/2026 | **2026-05** | missing |
| 01/07/2026 | 2026-06 | present (76 wells) |
| 03/08/2026 | **2026-07** | missing (hub ends at June) |

So it is four rounds, not three — July is also absent from the committed hub, which
matches your note that the July levels export was lost. If July is already in your
working copy, ignore that row.

**Backfill, oldest first** (order matters: `intake_monthly.py` uses the previous
month's `wte` for its outlier check):

```bash
cd ~/projects/NRG
for m in 2026-03 2026-04 2026-05; do
  python3 living/intake_monthly.py \
    --master "$MASTER_ODS" \
    --recordsheet "$MASTER_ODS" \
    --month $m \
    --hub living/readings_living.csv \
    --metadata data/well_metadata.csv \
    --no-ods
done
```

`--no-ods` skips the LibreOffice write-back, which is what you want here — the master
already holds these readings; you are only growing the hub.

**Do Item 1 first.** Backfilling while `Pipe_Top_Elev` is at 11.325 writes three more
`ceh13` rows on the minority basis, and you would then have four rows to correct
instead of one.

**Check before regenerating the feeds:**

```bash
python3 -c "
import pandas as pd
d = pd.read_csv('living/readings_living.csv')
d['date'] = pd.to_datetime(d.date)
print(d.groupby(d.date.dt.to_period('M')).size().tail(8))
print('rows:', len(d))
"
```

Expect a continuous 2026-01 … 2026-06 (or 2026-07) run at roughly 73–76 wells per
month, and no gap.

Then run the normal update:

```bash
./living/forecaster_monthly_update.sh 2026-07
```

---

## What I have not done

No files written, no commits, no pushes. The `ceh13` values above are derived from the
committed hub and the git history; re-derive `depth` from your own copy before
applying if your working tree has moved on.

The open question for you: whether `ceh13`'s `Pipe_Top_Elev` was edited deliberately
in that commit or came along with the metre/cm fix. It doesn't change the correction
either way, but it bears on whether the same thing could have happened elsewhere —
and the diff says it did not, on that commit at least.
