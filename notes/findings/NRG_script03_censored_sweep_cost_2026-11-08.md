# Script 03's per-well datum sweep became ~70x more expensive on 2026-10-29

**Found** 2026-11-08, while trying to make a full pipeline run fit inside a cloud container.
**Noticed by Martin**, from the run itself: *"the per-well datum sensitivity score is what is
taking the longest, and somehow this is a lot longer taking to run than it used to do."*
He was right on both counts.

## What changed

Commit **`67379f90` "model a ii" (2026-10-29)** introduced `_DRY` and
`dry_bound=_db(target_col)` into `well_datum_sensitivity`. Before it, every fit in the sweep
was ordinary least squares. Since it, every fit at a well with dry months goes through
`fit_ssm_censored`: maximum likelihood, with the GHK orthant probability for censored runs
and standard errors from a **numerical Hessian**.

Nothing is wrong with the change as modelling. What was not noticed is what it costs in a
place that calls the fitter five thousand times.

## The measurement

Both numbers are from this session, on the same machine, same data:

| path | wells | time | per well |
|---|---|---|---|
| OLS (`dry_bound=None`) | 66 | 31.3 s | 0.47 s |
| censored ML (`dry_bound` set) | 8 | 266.2 s | 33.3 s |

**≈ 70x per well.** The sweep is `DATUM_SWEEP` = 76 datums x 66 wells = **5,016 fits**, of
which 48 of the 66 wells carry dry bounds. A step that took well under a minute in October
now takes about 15 minutes, and Script 03 is ~78 % of pipeline wall-clock.

The OLS figure was obtained by accident: a test harness forgot to populate `_DRY`, so every
well silently took the cheap path. That accident is recorded separately because it also
produced plausible but WRONG numbers at 22 wells with no error and no gate -- see the
hidden-state note below.

## Why it matters now

A cloud container killed four long runs on 2026-11-08 (at 14 and 47 minutes, and twice
mid-Script-03). Getting a full run under ~30 minutes is what makes cloud runs viable, and
this one step is most of the gap.

## The options, cheapest win last

1. **Leave it, parallelise the sweep.** Four worker processes, byte-identical output
   (proved: md5 `292046c3` / `6d4a2f4d` across serial and 4 workers on the censored path,
   with `_DRY` populated). ~15 min becomes ~6. This is what was installed.
2. **Censored only at the CHOSEN datum; OLS for the search.** The sweep's job is to find the
   datum maximising R-squared with beta_3 > 0 -- a search. ~15 min becomes seconds. It
   changes `03_09_well_datum_sensitivity.csv`'s per-datum p-values, so it needs a decision.
3. **Keep the censored fit but drop the numerical Hessian during the search.** The Hessian is
   the expensive part and the search only uses its p-value for a
   `beta_3_significant_positive` flag. Most of the win, and it changes no statistic that is
   reported at the chosen datum.

**2 and 3 are modelling decisions and are Martin's, not a chat's.** 3 looks the better trade
if it is clean to implement, because nothing reported moves. They are recorded here rather
than acted on.

## The hidden-state trap beside it

`_db()` reads a module-level `_DRY` dict that only `main()` fills. A worker process inherits
it by **fork** and not by **spawn**, and a caller that builds its own inputs does not get it
at all. Either way `dry_bound` silently becomes `None`, `fit_ssm` takes the OLS path, and 22
wells are refitted by the wrong estimator -- no exception, no gate, and output that looks
entirely reasonable. It cost this session a false "the committed file is stale" claim.

The installed parallelism therefore passes the dry bound **in the job tuple**: the worker
holds no reference to `_db`, `_DRY`, `well_col_lookup`, `upstand_lookup` or `wells_clean`,
so fork and spawn behave identically. `_db()` is called from eight other places in Script 03
and the same trap is open at each of them.
