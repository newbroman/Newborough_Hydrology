#!/usr/bin/env python3
"""
env_audit.py — is this the machine the pipeline runs on, and has it moved?

WHAT WENT WRONG WITHOUT IT

  On 2026-08-26 a Cowork session reported, in a commit message, a changelog, the
  ledger header and a tool's own output, that Script 09g had been unable to start
  for five weeks. The evidence was `src/venv/bin/python3.12` resolving to a
  Python 3.10 that could not parse a module 09g imports.

  Every one of those commands ran in a sandbox VM with the NRG folder mounted
  into it. The machine that runs this pipeline is on Python 3.12.3. Nothing was
  broken. The same session had spent the day working around
  `refresh_mirrors.py` refusing to write because "pandoc 2.9.2 is below the
  pinned minimum 3.0" — and the pipeline's machine has pandoc 3.1.3, the exact
  version the mirrors were built with.

  The failure was not that a sandbox has old tools. It is that EVERY
  ENVIRONMENT-DEPENDENT LINE THIS SUITE PRINTS IS UNATTRIBUTED. `check_all` says
  "pandoc 2.9.2 is below the pinned minimum" without saying whose pandoc, so a
  fact about the shell reads as a fact about the project. Attribute it and the
  whole class of mistake becomes visible at a glance.

WHAT IT DOES

  RECORD    `--record`, run once ON THE MACHINE THAT RUNS THE PIPELINE, writes
            tools/environment.json: an identity marker plus the version of every
            external this suite shells out to and every library whose version
            can move a published number.

  COMPARE   the default. Probes the live environment and prints it beside the
            record. Two outcomes, and they are not the same finding:

              * same machine, versions moved  — a real change worth knowing;
                pandoc especially, since the mirrors are byte-reproducible only
                on the version that wrote them.
              * different machine             — nothing below describes the
                pipeline. Said loudly, at the top, before any of it.

  It gates nothing by default. `--strict` exits non-zero on any difference, for
  a release check where the environment must be the recorded one.

  A MISSING RECORD IS REPORTED LOUDLY, not treated as agreement. `drive_lag.py`
  learned the same lesson from `.last_drive_archive`: a marker nothing writes and
  a marker nothing reads fail identically, and silence is the worst answer.

Usage:
    python3 tools/env_audit.py              # compare against the record
    python3 tools/env_audit.py --record     # write the record (on THE machine)
    python3 tools/env_audit.py --strict     # non-zero if anything differs
    python3 tools/env_audit.py --quiet      # one verdict line, for check_all
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-08-26.

import argparse
import getpass
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RECORD = REPO / "tools/environment.json"

C_RED, C_YEL, C_GRN, C_DIM, C_0 = "\033[31m", "\033[33m", "\033[32m", "\033[2m", "\033[0m"


def _c(s: str, c: str) -> str:
    return s if not sys.stdout.isatty() else f"{c}{s}{C_0}"


# ── probes ───────────────────────────────────────────────────────────────────
# Each external this suite actually shells out to, with the call sites that make
# it matter. Adding a tool here is cheap; a tool the suite depends on and this
# does not name is a tool whose version can move a result unannounced.
EXTERNALS = {
    "pandoc":     (["pandoc", "--version"],     r"pandoc\s+([0-9.]+)",
                   "refresh_mirrors.py — mirrors are byte-reproducible only on "
                   "the version that wrote them"),
    "pdftotext":  (["pdftotext", "-v"],         r"pdftotext\s+version\s+([0-9.]+)",
                   "tools/figref_lint.py, tools/audit_number_drift.py"),
    "soffice":    (["soffice", "--version"],    r"([0-9]+\.[0-9.]+)",
                   "tools/build_pdfs.sh, nrg_git.sh — every published PDF"),
    "git":        (["git", "--version"],        r"git version\s+([0-9.]+)", "nrg_git.sh"),
}

# Libraries whose version can change a committed number rather than merely a
# message. Probed by import, in the interpreter that would run the pipeline.
# (import name, reported name) — odfpy installs as `odf`, and probing "odfpy"
# recorded a false "absent" in the first reference written on 2026-08-26.
LIBRARIES = ["numpy", "pandas", "scipy", "statsmodels", "matplotlib",
             "sklearn", "geopandas", "shapely", "pyproj", "odf", "cairosvg",
             "rasterio", "contextily", "adjustText"]
# adjustText added 2026-08-29: the figure scripts import it, so a version change
# moves label placement in five maps, and it was outside the comparison. The
# record's key for the ODF reader was "odfpy" while this list probes "odf", so
# every run reported it "absent when recorded" against a record that had it —
# a permanent false difference, corrected in the same pass.


def _run(cmd: list[str]) -> str | None:
    exe = shutil.which(cmd[0])
    if exe is None:
        return None
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
    except (subprocess.SubprocessError, OSError):
        return None
    return (r.stdout or "") + (r.stderr or "")


def probe() -> dict:
    ext = {}
    for name, (cmd, pat, _why) in EXTERNALS.items():
        out = _run(cmd)
        if out is None:
            ext[name] = None                      # not on PATH
            continue
        m = re.search(pat, out)
        ext[name] = m.group(1) if m else "?"

    libs = {}
    for name in LIBRARIES:
        try:
            mod = __import__(name)
            libs[name] = getattr(mod, "__version__", "?")
        except Exception:
            libs[name] = None

    # Any venv is worth recording verbatim, because a venv here pins nothing:
    # `src/venv/bin/python3.12` was a symlink to the host's system python, so its
    # NAME promised a version the machine did not have. That is the trap this
    # tool exists to surface, so it looks wherever a venv might be rather than at
    # one hard-coded path. (src/venv itself was retired on 2026-08-27 — it had
    # been built at a Google Drive path from before the project moved.)
    venv_target = {}
    for cand in ("venv", "src/venv", ".venv"):
        for exe in ("python3.12", "python3", "python"):
            p = REPO / cand / "bin" / exe
            if p.exists() or p.is_symlink():
                try:
                    venv_target[f"{cand}/bin/{exe}"] = str(p.resolve())
                except OSError:
                    venv_target[f"{cand}/bin/{exe}"] = "<unresolvable>"
    venv_target = venv_target or None

    return {
        "machine": {
            "hostname": platform.node(),
            "user": getpass.getuser(),
            "system": f"{platform.system()} {platform.release()}",
            "repo_path": str(REPO),
        },
        "python": {
            "version": platform.python_version(),
            "executable": sys.executable,
            "venv_interpreters": venv_target,
        },
        "externals": ext,
        "libraries": libs,
    }


# ── record / compare ─────────────────────────────────────────────────────────
def do_record(live: dict, force: bool = False) -> int:
    # A second machine must not quietly become the reference. tools/environment.json
    # is TRACKED and PUSHED, so running --record on the A475 would overwrite the
    # L14's record, publish it, and leave every later run comparing against
    # whichever machine recorded last. The correct behaviour on a second machine
    # is to report "NOT THE MACHINE" forever; that is the tool working.
    if RECORD.exists() and not force:
        rec = json.loads(RECORD.read_text(encoding="utf8"))
        if not same_machine(live, rec):
            r, m = rec["machine"], live["machine"]
            print(_c("  REFUSING to re-record from a different machine.", C_RED))
            print(f"      recorded {r['user']}@{r['hostname']}")
            print(f"      here     {m['user']}@{m['hostname']}")
            print("  tools/environment.json is tracked and pushed. Recording here "
                  "would overwrite")
            print("  the reference and publish it, and every later run would "
                  "compare against")
            print("  whichever machine recorded last. A second machine SHOULD "
                  "report 'NOT THE")
            print("  MACHINE' — that is the tool working, not a fault to clear.")
            print(_c("  If the reference machine has genuinely changed: "
                     "--record --force", C_YEL))
            return 1
    print(_c("Recording this environment as the pipeline's reference.", C_YEL))
    print("  Only meaningful if this IS the machine that runs the pipeline —")
    print(f"  recording as: {live['machine']['user']}@{live['machine']['hostname']} "
          f"at {live['machine']['repo_path']}")
    RECORD.write_text(json.dumps(live, indent=2, sort_keys=True) + "\n",
                      encoding="utf8")
    print(_c(f"  wrote {RECORD.relative_to(REPO)}", C_GRN))
    return 0


def same_machine(live: dict, rec: dict) -> bool:
    a, b = live["machine"], rec["machine"]
    return (a["hostname"], a["user"]) == (b["hostname"], b["user"])


def compare(live: dict, rec: dict, quiet: bool) -> list[str]:
    """Differences, as human sentences. Empty means the environments agree."""
    diffs: list[str] = []

    lv, rv = live["python"]["version"], rec["python"]["version"]
    if lv != rv:
        diffs.append(f"python {lv}  (recorded {rv})")

    for name in EXTERNALS:
        l, r = live["externals"].get(name), rec["externals"].get(name)
        if l == r:
            continue
        if l is None:
            diffs.append(f"{name} NOT ON PATH  (recorded {r})")
        elif r is None:
            diffs.append(f"{name} {l}  (not present when recorded)")
        else:
            diffs.append(f"{name} {l}  (recorded {r})")

    for name in LIBRARIES:
        l, r = live["libraries"].get(name), rec["libraries"].get(name)
        if l == r or (l is None and r is None):
            continue
        if l is None:
            diffs.append(f"{name} NOT IMPORTABLE  (recorded {r})")
        elif r is None:
            diffs.append(f"{name} {l}  (absent when recorded)")
        else:
            diffs.append(f"{name} {l}  (recorded {r})")
    return diffs


# ── record validity — is the RECORD itself a runnable environment? ───────────
# D-093's failure was not a live environment that differed; it was a RECORD that
# described a stack the pipeline cannot run on, and every session's gate passing
# against it. Nothing in this file tested the record's central claim. This does,
# and it does so machine-independently, because both files it reads are tracked:
# tools/environment.json against requirements.txt, which D-093 settled as the
# environment ("venv/ IS the environment").
#
# The import name is not the distribution name. odfpy installs as `odf` and
# probing the wrong one recorded a false "absent" that lasted weeks (see the
# note above LIBRARIES); scikit-learn imports as `sklearn`. That map is EXPLICIT
# here rather than heuristic, because a heuristic is how the first one happened.
DIST_NAME = {
    "sklearn": "scikit-learn",
    "odf": "odfpy",
}

REQUIREMENTS = REPO / "requirements.txt"


def record_vs_requirements(rec: dict) -> list[str]:
    """Disagreements between the recorded reference and requirements.txt."""
    if not REQUIREMENTS.exists():
        return ["requirements.txt is absent — the record cannot be validated"]
    pins = {}
    for line in REQUIREMENTS.read_text(encoding="utf8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "==" not in line:
            continue
        name, _, ver = line.partition("==")
        pins[name.strip().lower()] = ver.strip()
    out = []
    for name, recorded in sorted(rec.get("libraries", {}).items()):
        if recorded in (None, "?"):
            continue                      # no __version__ to compare; not a fault
        pinned = pins.get(DIST_NAME.get(name, name).lower())
        if pinned is None:
            continue                      # not pinned; requirements is not exhaustive
        if pinned != recorded:
            out.append(f"{name}: record says {recorded}, requirements.txt "
                       f"pins {pinned}")
    return out


def classify(live: dict, rec: dict) -> tuple[list[str], list[str], list[str]]:
    """Split the comparison into (capability, externals, version drift).

    Capability — a library the pipeline imports is NOT IMPORTABLE — is not a
    statement about WHICH pipeline you would run. It is a statement that there
    is no pipeline here, and it is true on every machine. Version drift is only
    meaningful on the recorded one.
    """
    cap, ext, drift = [], [], []
    for name in LIBRARIES:
        l, r = live["libraries"].get(name), rec["libraries"].get(name)
        if l == r or (l is None and r is None):
            continue
        if l is None:
            cap.append(f"{name} NOT IMPORTABLE  (recorded {r})")
        elif r is None:
            drift.append(f"{name} {l}  (absent when recorded)")
        else:
            drift.append(f"{name} {l}  (recorded {r})")
    for name in EXTERNALS:
        l, r = live["externals"].get(name), rec["externals"].get(name)
        if l == r:
            continue
        if l is None:
            ext.append(f"{name} NOT ON PATH  (recorded {r})")
        else:
            drift.append(f"{name} {l}  (recorded {r})")
    return cap, ext, drift


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--record", action="store_true",
                    help="write tools/environment.json from THIS environment")
    ap.add_argument("--force", action="store_true",
                    help="with --record: re-record even from a different machine")
    ap.add_argument("--strict", action="store_true",
                    help="exit non-zero if the live environment differs")
    ap.add_argument("--quiet", action="store_true",
                    help="one verdict line (for check_all)")
    ap.add_argument("--gate", action="store_true",
                    help="exit non-zero on a fault that is true on ANY machine: "
                         "a library the pipeline needs not importable, or a "
                         "record that disagrees with requirements.txt. Identity "
                         "never gates; version drift gates only on the recorded "
                         "machine.")
    a = ap.parse_args()

    live = probe()
    if a.record:
        return do_record(live, a.force)

    if not RECORD.exists():
        # Not "fine". Unknown. Those are different, and the second is the one
        # that lets a sandbox's pandoc pass for the project's.
        print(_c("  NO REFERENCE ENVIRONMENT RECORDED", C_RED))
        print(f"  {RECORD.relative_to(REPO)} does not exist, so nothing below "
              f"can be compared and")
        print("  every environment-dependent line this suite prints is "
              "unattributed.")
        print(_c("  On the machine that runs the pipeline, once: "
                 "python3 tools/env_audit.py --record", C_YEL))
        print(f"  This environment is {live['machine']['user']}@"
              f"{live['machine']['hostname']}, python {live['python']['version']}"
              f", pandoc {live['externals'].get('pandoc') or 'absent'}.")
        return 1 if a.strict else 0

    rec = json.loads(RECORD.read_text(encoding="utf8"))
    here = same_machine(live, rec)
    diffs = compare(live, rec, a.quiet)
    cap, ext, drift = classify(live, rec)
    invalid = record_vs_requirements(rec)

    # Faults that are true wherever they are seen. Neither depends on which
    # machine this is, so neither is excused by the identity banner below.
    gate_fault = bool(cap) or bool(invalid)

    def _report_universal() -> None:
        if invalid:
            print(_c("  THE RECORD ITSELF DISAGREES WITH requirements.txt",
                     C_RED))
            for d in invalid:
                print(f"      {d}")
            print("  requirements.txt is the environment (D-093). A record that "
                  "disagrees with it")
            print("  is not a reference; it is a second opinion nothing "
                  "checked.")
        if cap:
            print(_c(f"  {len(cap)} librar(y/ies) THE PIPELINE IMPORTS ARE NOT "
                     f"IMPORTABLE HERE:", C_RED))
            for d in cap:
                print(f"      {d}")
            print("  This is not a version disagreement. Nothing in this run "
                  "that touches an")
            print("  output can be trusted from this environment.")
        if ext:
            print(_c(f"  {len(ext)} external(s) not on PATH "
                     f"(document toolchain — reported, not gated):", C_YEL))
            for d in ext:
                print(f"      {d}")

    if not here:
        m, r = live["machine"], rec["machine"]
        print(_c("  NOT THE MACHINE THIS PIPELINE RUNS ON", C_RED))
        print(f"      here     {m['user']}@{m['hostname']}  ({m['system']})  "
              f"{m['repo_path']}")
        print(f"      recorded {r['user']}@{r['hostname']}  ({r['system']})  "
              f"{r['repo_path']}")
        print("  Every version-dependent line below — and in every other check "
              "in this run —")
        print("  describes THIS environment, not the pipeline's. A refusal or a "
              "warning from")
        print("  here is not a finding about the project until it is reproduced "
              "there.")
        if diffs:
            print(_c(f"  {len(diffs)} difference(s) from the record:", C_YEL))
            for d in diffs:
                print(f"      {d}")
        # Difference from the record is expected on a different machine and is
        # not, by itself, a fault. --strict still fails: a release check has no
        # business running anywhere but the recorded machine.
        #
        # But the banner is NOT an amnesty. It used to swallow everything below
        # it, which is how eight absent libraries read as green. The two faults
        # that are true on any machine are reported and gated here, and the
        # banner says which classes it is suppressing so silence is never
        # ambiguous.
        _report_universal()
        if not gate_fault:
            print(_c("  identity and version drift suppressed here (expected "
                     "on a second machine);", C_YEL))
            print(_c("  capability and record validity checked and clean.",
                     C_YEL))
        return 1 if (a.strict or (a.gate and gate_fault)) else 0

    if not diffs:
        if a.quiet:
            print(_c("  env_audit: this is the recorded machine, nothing has "
                     "moved", C_GRN))
        else:
            m = live["machine"]
            print(f"  {m['user']}@{m['hostname']} — the recorded machine.")
            print(f"  python {live['python']['version']}, "
                  + ", ".join(f"{k} {v}" for k, v in live["externals"].items()
                              if v) + ".")
            print(_c("  every recorded version matches.", C_GRN))
        _report_universal()
        return 1 if (a.gate and gate_fault) else 0

    print(_c(f"  the recorded machine, but {len(diffs)} version(s) have moved:",
             C_YEL))
    for d in diffs:
        print(f"      {d}")
    if live["externals"].get("pandoc") != rec["externals"].get("pandoc"):
        print("  pandoc moved — the committed mirrors are byte-reproducible "
              "only on the")
        print("  version that wrote them. Run "
              "`python3 tools/refresh_mirrors.py --verify` before trusting a "
              "mirror diff.")
    print("  If these upgrades are intended, re-record: "
          "python3 tools/env_audit.py --record")
    _report_universal()
    # On the recorded machine a moved version means the reference is stale and a
    # published number may not reproduce, and re-recording is a one-command fix.
    # That is worth failing on. Off this machine it means nothing and must not.
    return 1 if (a.strict or a.gate) else 0


if __name__ == "__main__":
    sys.exit(main())
