#!/usr/bin/env python3
"""
store_io.py — exact read and write for the pipeline's READ-MODIFY-WRITE stores.

WHY THIS EXISTS

  On 2026-09-11, reading a clean diff before a commit, three committed values
  had moved in their last digits. Two were explained — their scripts had been
  re-run under the venv, which D-155's amendment settles. The third was not:

      site_p_minus_pet_annual   0.23557798234529378 -> 0.2355779823452937

  Script 16 produces that value and Script 16 had NOT been run. Its row kept
  its `updated` date of 2026-09-09 and its `run_id` of
  `run:20260909T103134-f79545`, and its value changed anyway.

  `update_site_observation()` writes ONE row by reading the whole file and
  writing the whole file back:

      df = pd.read_csv(path)     # every row parsed
      ...                        # one row changed
      df.to_csv(path)            # every row rewritten

  and `pandas.read_csv`'s default C float parser is NOT correctly rounded. It
  is fast and it is within a few ULP, which is the right trade for reading
  data and the wrong one for rewriting a store. Measured on this machine,
  pandas 2.3.3:

      0.23557798234529378  default parser      -> 3 ULP away
      0.23557798234529378  float_precision=... -> exact

  So every write to one of these stores silently perturbed every OTHER value
  in it, while leaving each of those rows asserting it came from an earlier
  run. It compounds: each pass can nudge again, which is the reading of
  `four_zone_spring_step_c3warren` sitting 21 ULP from its committed value.

  None of it is scientifically material — it is the sixteenth significant
  figure. What is material is that a stored number changed with its provenance
  saying it had not, which makes an md5 staleness check on these files fail
  forever with nothing numeric behind it, and which is part of what the
  2026-09-10 "ULP cascade" was actually chasing.

WHAT THIS DOES

  `read_store()` parses with `float_precision="round_trip"`, pandas' correctly
  rounded parser, so a value read is bit-identical to the value written.
  `write_store()` writes with pandas' default float repr, which is the shortest
  string that round-trips. Together they make a read-modify-write of a store
  EXACT for every row the write did not touch.

  `tools/store_roundtrip_lint.py` gates it: for each registered store, a read
  followed by a write must be byte-identical to the file on disk.

WHAT THIS IS NOT FOR

  Derived outputs. A script that reads a committed CSV, computes from it and
  writes a DIFFERENT file does not need this: the parse error is far below any
  quantity this project reports, and routing every read in the tree through a
  slower parser to chase the sixteenth figure would be a cost with no finding
  behind it. The defect this fixes is specific — a store that rewrites rows it
  was not asked to change.

  See D-157.
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) - 2026-09-11. New. read_store /
#   write_store, the exact read-modify-write pair for the pipeline's stores.
#   Created for D-157; see the module docstring for the measurement that
#   prompted it.

from pathlib import Path

import pandas as pd

#: The parser. Named rather than repeated: it is the whole point of the module,
#: and a second copy spelled differently would be a silent hole.
EXACT_FLOAT_PRECISION = "round_trip"


def read_store(path: str | Path, **kwargs) -> pd.DataFrame:
    """Read a store so that every float is bit-identical to what was written.

    Any keyword `pd.read_csv` accepts is passed through; `float_precision` is
    set here and a caller-supplied one is honoured, so a deliberate override is
    possible and visible at the call site rather than silently ignored.
    """
    kwargs.setdefault("float_precision", EXACT_FLOAT_PRECISION)
    return pd.read_csv(path, **kwargs)


def write_store(df: pd.DataFrame, path: str | Path, **kwargs) -> None:
    """Write a store with pandas' default float repr — shortest round-tripping.

    `index=False` is the default for every store in this tree; pass
    ``index=True`` explicitly if a store ever needs its index.
    """
    kwargs.setdefault("index", False)
    df.to_csv(path, **kwargs)


def roundtrip_is_exact(path: str | Path, **read_kwargs) -> tuple[bool, str]:
    """(ok, detail) — does reading and rewriting this store change its bytes?

    The check `tools/store_roundtrip_lint.py` applies. Kept here, beside the
    functions it tests, so the module carries its own proof.
    """
    path = Path(path)
    if not path.is_file():
        return True, "not on disk — nothing to check"
    before = path.read_bytes()
    import io
    buf = io.StringIO()
    df = read_store(path, **read_kwargs)
    write_store(df, buf)
    after = buf.getvalue().encode("utf-8")
    if after == before:
        return True, "byte-identical"
    # Name the first differing line rather than the byte offset: a byte offset
    # in a 40-column CSV tells a reader nothing they can act on.
    b_lines = before.decode("utf-8").splitlines()
    a_lines = after.decode("utf-8").splitlines()
    if len(a_lines) != len(b_lines):
        return False, (f"{len(b_lines)} line(s) on disk, {len(a_lines)} after a "
                       f"round trip")
    for i, (bl, al) in enumerate(zip(b_lines, a_lines), start=1):
        if bl != al:
            return False, (f"line {i} differs after a round trip:\n"
                           f"    on disk: {bl[:160]}\n"
                           f"    rewrite: {al[:160]}")
    return False, "bytes differ but no line does — check the trailing newline"
