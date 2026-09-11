#!/usr/bin/env python3
"""
store_roundtrip_lint.py — does reading a store and writing it back change it?

WHAT GOES WRONG WITHOUT IT

  On 2026-09-11 a committed value moved in its last digits while its own
  provenance said it had not:

      site_p_minus_pet_annual   0.23557798234529378 -> 0.2355779823452937
      updated  2026-09-09      run_id  run:20260909T103134-f79545   (unchanged)

  Script 16 produces that value and Script 16 had not been run. The cause was
  `update_site_observation()` writing ONE row by reading the whole store and
  writing the whole store back, through `pandas.read_csv`'s default C float
  parser, which is fast, within a few ULP, and NOT correctly rounded. Every
  write perturbed every other row. It compounds across passes.

  The fix is `utils/store_io.read_store()`, which parses with
  `float_precision="round_trip"`. The fix is one keyword, which is exactly the
  kind of thing that gets dropped by a later edit, a new updater, or a copied
  call site. Hence this gate.

  It is also the only check in the tree that can SEE this fault. `provenance_lint`
  hashes each output as written, so a store whose rows drift on every write
  hashes consistently and reads as sound. An md5 staleness check on such a file
  reports a difference after any re-run, forever, with nothing numeric behind
  it — which is part of what the 2026-09-10 "ULP cascade" was chasing.

WHAT IT CHECKS

  For each store in `tools/roundtrip_stores.csv`: read it with `read_store()`
  and write it with `write_store()`, in memory, and require the result to be
  BYTE-IDENTICAL to the file on disk. A store that fails has either been written
  by something bypassing `store_io`, or gained a column whose formatting does not
  round-trip.

  A store that is not on disk is skipped, not failed: these are pipeline outputs
  and a clone legitimately lacks them (D-081 reasoning).

  GATE. A failure means a future write to that store will corrupt rows nobody
  touched, which is a provenance fault, not a rounding preference.

  See D-157 and utils/store_io.py.
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) - 2026-09-11. New, for D-157.

import csv
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from utils.store_io import roundtrip_is_exact          # noqa: E402

REGISTRY = REPO / "tools" / "roundtrip_stores.csv"


def selftest() -> int:
    """Prove the gate can FAIL — a check that cannot fail is not a check.

    Writes a one-row store holding a literal pandas' default parser is known to
    mis-round, then asserts that the default parser does NOT round-trip it and
    `read_store` does. If pandas ever fixes its fast parser this test goes green
    on both and says so, which is the right outcome: the gate stays, the reason
    for it has gone.
    """
    import io
    import tempfile
    import pandas as pd
    from utils.store_io import read_store, write_store

    literal = "0.23557798234529378"        # the measured case, 3 ULP, 2026-09-11
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "store.csv"
        path.write_text(f"observation,value\nsite_p_minus_pet_annual,{literal}\n",
                        encoding="utf-8")
        before = path.read_bytes()

        loose = io.StringIO()
        pd.read_csv(path).to_csv(loose, index=False)
        loose_exact = loose.getvalue().encode("utf-8") == before

        tight = io.StringIO()
        write_store(read_store(path), tight)
        tight_exact = tight.getvalue().encode("utf-8") == before

    print(f"  default parser round-trips {literal}: {loose_exact}")
    print(f"  read_store round-trips     {literal}: {tight_exact}")
    if not tight_exact:
        print("store_roundtrip_lint --selftest: FAIL — read_store does not "
              "round trip its own measured case; the fix is broken, not the gate")
        return 1
    if loose_exact:
        print("store_roundtrip_lint --selftest: OK, but the default parser now "
              "round-trips this literal too — pandas may have fixed its fast "
              "parser. The gate stays; its original motivating case no longer "
              "demonstrates the fault, so find a new one before relaxing it.")
        return 0
    print("store_roundtrip_lint --selftest: OK — the default parser loses this "
          "value and read_store keeps it, so the gate can fail")
    return 0


def main() -> int:
    quiet = "--quiet" in sys.argv
    if "--selftest" in sys.argv:
        return selftest()
    if not REGISTRY.is_file():
        print(f"store_roundtrip_lint: FAIL — {REGISTRY.name} is missing; the "
              f"registry is what says which files are stores")
        return 1
    rows = list(csv.DictReader(REGISTRY.open(encoding="utf-8")))
    if not rows:
        print(f"store_roundtrip_lint: FAIL — {REGISTRY.name} registers no "
              f"stores; an empty gate is not a passing gate")
        return 1

    bad, skipped, ok = [], [], []
    for row in rows:
        rel = row["store"].strip()
        path = REPO / rel
        if not path.is_file():
            skipped.append(rel)
            continue
        exact, detail = roundtrip_is_exact(path)
        (ok if exact else bad).append((rel, detail, row.get("owner_module", "")))

    if not quiet:
        for rel, detail, _ in ok:
            print(f"  ok    {rel} — {detail}")
        for rel in skipped:
            print(f"  skip  {rel} — not on disk (a clone legitimately lacks it)")
    for rel, detail, owner in bad:
        print(f"  FAIL  {rel} — a read-modify-write would change rows nobody "
              f"touched")
        print(f"        {detail}")
        print(f"        owner: {owner or 'unregistered'} — route its reads and "
              f"writes through utils/store_io (read_store / write_store)")

    if bad:
        print(f"store_roundtrip_lint: FAIL — {len(bad)} store(s) do not round "
              f"trip. See D-157.")
        return 1
    print(f"store_roundtrip_lint: OK — {len(ok)} store(s) round trip "
          f"byte-identically"
          + (f", {len(skipped)} not on disk" if skipped else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
