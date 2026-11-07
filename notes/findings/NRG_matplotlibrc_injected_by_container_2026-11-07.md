# The cloud container injects a matplotlib config, and `env_audit` passes anyway

**2026-11-07, Pipeline chat (claude.ai/code cloud session). Measured, not inferred.**

## What happened

A 2-pixel difference in `10e_03_coefficient_shifts.png` was noticed while adding an
emit-only change to Script 10e. Chasing it found that **this container cannot reproduce a
committed figure**, and that `env_audit` reports the environment as correct.

## The evidence chain

| step | result |
|---|---|
| my 1.20.0 produces | `f1be55dc…` |
| **HEAD's own 10e** produces | `f1be55dc…` — identical, so the edit is innocent |
| two consecutive runs | byte-identical: deterministic within this container |
| `run_10_clearfell` inputs vs provenance | **19 of 19 match** |
| committed figure | `91941071…`, and it equals its recorded provenance hash |
| `env_audit` | "every recorded version and the BLAS pin match" |

Same code, same inputs, deterministic — different figure. So it is the environment.

## The cause

The container image sets, from outside the repository:

    MATPLOTLIBRC=/etc/matplotlib

and `/etc/matplotlib/matplotlibrc` contains:

    font.family: Inter, sans-serif, DejaVu Sans
    text.hinting: no_hinting

`utils/render_utils.py` sets `font.family` and `font.sans-serif` at runtime, so the font half is
overridden. **`text.hinting: no_hinting` is not overridden and survives**, changing glyph metrics
and therefore the `bbox_inches="tight"` extent: 2881 px tall committed against 2879 px here, and
30 KB larger. Nothing in `tools/environment.json`, `tools/nrg_env.sh` or `requirements.txt`
mentions matplotlib configuration.

## Proof

With the variable neutralised, HEAD's 10e reproduces the committed artefact exactly:

    env -u MATPLOTLIBRC python3 src/10e_coefficient_decomposition.py
    -> 9194107155d537c580d649f7e17fca351f4e77473504ffd49f3ab05fdf768dea
       9194107155d537c580d649f7e17fca351f4e77473504ffd49f3ab05fdf768dea  (committed)

So the injected rc is the **whole** difference, and this container is otherwise sound.

## Why it matters

A full `--full --with-supplementary` run from this container **would rewrite every text-bearing
figure in the corpus and record the container as the producer**. That is a foreign build entering
the published corpus — the same class as the 2026-09-01 PDF that three safeguards missed and that
stayed hidden for three days — and `env_audit`, the gate D-227 rests on, reads green throughout.

D-227's claim is that any machine building the environment produces byte-identical outputs
(58 of 58 verified on 2026-10-02 between the laptop and a cloud container). That claim still holds
for the *environment as specified*; what this shows is that **the specification does not cover
matplotlib's own configuration, which the host can set from outside the repository**, so a
conforming machine can still produce different figures.

## Not established

- ~~Whether the laptop has it.~~ **ANSWERED 2026-11-07 by Martin on the L14:** `MATPLOTLIBRC` is
  empty and `/etc/matplotlib/matplotlibrc` does not exist ("No such file or directory"). So the
  laptop uses matplotlib's stock configuration, the committed artefacts are stock-config builds,
  and the divergence is entirely the cloud image's. The framing above stands.
- Whether the 2026-10-02 byte-identical check would still pass today, i.e. whether the image
  gained this file after that date.
- Which other outputs are affected. Every figure with text is a candidate; CSVs are not
  (all of 10e's CSVs were byte-identical throughout).

## Remedy, not chosen — this is a decision

The direction is clear but it amends D-227, so it is Martin's:
1. **Neutralise it in the pipeline**: `run_analysis.py` unsets `MATPLOTLIBRC` (and sets the
   rcParams the project wants) so no host config can reach a figure. Smallest, and makes the
   corpus independent of the image.
2. **Pin and compare it**: record the expected effective matplotlib config in
   `tools/environment.json` and have `env_audit` compare it, so a mismatch fails the gate
   instead of passing silently.
3. Both. (1) stops the damage; (2) stops the next variable of this kind going unnoticed.

Until then, a pipeline run from this container must use `env -u MATPLOTLIBRC`.
