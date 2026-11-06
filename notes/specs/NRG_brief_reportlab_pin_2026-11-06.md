# Brief — put `reportlab` in the pin (D-313)

*Martin ruled this on 2026-11-06: "The newsletter toolchain — reportlab-in-the-pin". The full
reasoning, the measurements and the Revisit-if are in **D-313**; this brief is the work it owes.
Claim: `tools` (and `pipeline` for `requirements.txt`). Raised by `Fieldwork Oct 2026`, which
could not do it because both claims were held.*

## Why it is owed

`living/newborough_report.py` builds the monthly Water Watch PDF through `reportlab`, which is in
**neither `requirements.txt` nor `tools/environment.json`**. So the newsletter is produced outside
the D-227 environment pin and outside `artefact_lint` Check C. Measured 2026-11-06:

| route | `/Producer` | pages | bytes |
|---|---|---|---|
| reportlab (today) | `ReportLab PDF Library - (opensource)` | 5 | 8,072,969 |
| LibreOffice, from the `.odt` the engine writes beside it | `LibreOffice 24.2` | 5 | 1,727,955 |

Check C compares each manifest PDF's Producer major.minor against `externals.soffice`
(`24.2.7.2`). Martin chose reportlab anyway, so the gate has to be told about it.

## The work

1. **`requirements.txt`** — add `reportlab` at a pinned version. The build measured here was
   **5.1.0**.
2. **`tools/environment.json`** — record it wherever the pinned libraries are recorded, so
   `env_audit` compares it like the rest.
3. **Expect every existing venv to fail `env_audit` until rebuilt.** The L14's and this cloud
   container's venvs do not have `reportlab` installed. Say so when it ships, and pair it with
   `tools/nrg_env.sh` so a rebuild picks it up — otherwise the first machine to pull gets a red
   gate for a change it did not make.
4. **Check C** — **only if and when the newsletter is committed under `PDF_MANIFEST.txt`** (the
   control board's J-4 answer, not yet ruled). Then Check C must admit the newsletter's own
   Producer rather than demanding the LibreOffice one. D-313 states that widening is part of the
   decision, not a later surprise. If the newsletter stays out of the committed corpus, this item
   lapses and items 1–3 stand alone.

## What NOT to do

Do not route the newsletter through LibreOffice to make Check C pass. That was the rejected
option, and D-313 records the 4.7x size cost of the choice as accepted, not overlooked.

Do not take the October PDF already on Drive as the pinned-build artefact: it was built with
`reportlab` on `PYTHONPATH` outside the venv, as a workaround this decision exists to remove. Once
the pin is in, rebuild it inside the environment.

## Check to carry

A check that `reportlab` appears in BOTH `requirements.txt` and `tools/environment.json` — one
without the other is the state D-313 is closing, and would read green to anything that looks at
only one.
