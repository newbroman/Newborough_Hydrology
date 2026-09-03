#!/usr/bin/env python3
"""
apply_main_guards.py — wrap a flat pipeline script's body in main() + a __main__ guard.

WHAT GOES WRONG WITHOUT IT

  A script whose work sits at module level RUNS WHEN IT IS IMPORTED. On 2026-09-03
  nine scripts in src/ were in that state, and five of them wrote into the tracked
  outputs/ tree merely by being imported:

      10a_ancova_baci  10d_summer_minima  10e_coefficient_decomposition
      10h_synthetic_impact_baci  11c_pflood_achievability
      13_figure_experimental_design  14b_year_of_crossing
      28_c3_detrend_check  29_c3_within_variance_check

  import_audit had been reporting this daily. Its own warning states the risk
  exactly: a read-only reader, a linter, an editor's language server or an agent
  inspecting the tree would all overwrite committed results without meaning to.
  import_audit itself is safe only because it imports under a write tripwire that
  swallows the writes; nothing else does.

  There is no allowlist in import_audit, so the condition cannot be declared away.
  The remedy is the pattern the other 61 scripts already use.

WHAT IT DOES

  Everything from the first real work statement to EOF is indented one level and
  placed inside `def main():`, and `if __name__ == "__main__": main()` is appended.
  Left at column 0: the module docstring, __version__, the sys.path bootstrap, and
  the header import block. Interleaved defs move inside main() with the body and
  close over its locals, which is safe here because nothing imports these modules —
  their names begin with a digit — and none uses a `global` statement.

  Safe for the pipeline because run_analysis.py launches every step as a subprocess
  (`[sys.executable, script_path]`), so __name__ == "__main__" holds as before.

  Idempotent: a file that already carries a guard is skipped, so a stray second run
  is a no-op rather than a nested main().

THE TWO TRAPS IT EXISTS TO AVOID

  1. MULTI-LINE STRING BODIES ARE CONTENT, NOT CODE. Several of these scripts build
     their *_results.md memo from a triple-quoted f-string. Indenting the interior
     lines adds four spaces to the published markdown, which turns the whole memo
     into a code block. Those lines are located and left alone.

  2. f-STRINGS TOKENIZE DIFFERENTLY FROM PYTHON 3.12. Under PEP 701 an f-string is
     no longer a single STRING token but FSTRING_START/MIDDLE/END, so a STRING-only
     scan silently fails to protect f-string bodies — and trap 1 is sprung with no
     error. This is not hypothetical: the first version of this tool did exactly
     that on 3.12 and `git diff -w` could not see it, the damage being pure
     whitespace. Both tokenizer generations are handled here.

  __version__ must also stay at column 0: ledger_lint reads it with a `^__version__`
  regex, so an indented assignment would present as nine missing versions.

VERIFICATION THAT MATTERS

  A whitespace-ignoring diff cannot validate this transform — the failure mode IS
  whitespace. Gate on generated output instead: re-run the touched scripts and
  require their CSVs and memos to be byte-identical.

Usage:
    python3 tools/apply_main_guards.py src/<script>.py [src/<script>.py ...]
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-09-03. Applied to the nine
#   guardless scripts the same day. Outputs verified byte-identical either side of
#   the change on 10a, 10d, 10h, 14b and 28; the remaining four were confirmed
#   structurally and by re-running them on the reference machine. Output is
#   byte-identical under Python 3.11, 3.12 and 3.13.

import ast, io, sys, tokenize

# Statements allowed to remain above main(): the sys.path bootstrap and friends.
BOOTSTRAP_CALLS = {"insert", "append", "filterwarnings", "use"}


def split_line(tree, src_lines):
    """Line of the first top-level statement that does real work."""
    for node in tree.body:
        # module docstring
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) \
           and isinstance(node.value.value, str):
            continue
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        # __version__ = ..., __all__ = ...  (ledger_lint reads these at column 0)
        if isinstance(node, ast.Assign) and all(
                isinstance(t, ast.Name) and t.id.startswith("__") for t in node.targets):
            continue
        # _HERE = ... / REPO = ... — path bootstrap, before the first import
        if isinstance(node, ast.Assign) and node.lineno < _first_import(tree):
            continue
        if isinstance(node, ast.Delete):
            continue
        # sys.path.insert(...) / warnings.filterwarnings(...) / mpl.use(...)
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            fn = node.value.func
            if isinstance(fn, ast.Attribute) and fn.attr in BOOTSTRAP_CALLS:
                continue
        return node.lineno
    return None


def _first_import(tree):
    for n in tree.body:
        if isinstance(n, (ast.Import, ast.ImportFrom)):
            return n.lineno
    return 10 ** 9


def string_continuation_lines(src):
    """Line numbers INSIDE a multi-line string literal (not its first line).

    Handles f-strings on BOTH tokenizer generations. Up to 3.11 an f-string is one
    STRING token; from 3.12 (PEP 701) it is FSTRING_START/MIDDLE/END, and a
    STRING-only scan would reindent the markdown these scripts emit.
    """
    inside = set()
    FSTART = getattr(tokenize, "FSTRING_START", None)
    FEND = getattr(tokenize, "FSTRING_END", None)
    stack = []
    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        if tok.type == tokenize.STRING and tok.end[0] > tok.start[0]:
            inside.update(range(tok.start[0] + 1, tok.end[0] + 1))
        elif FSTART is not None and tok.type == FSTART:
            stack.append(tok.start[0])
        elif FEND is not None and tok.type == FEND and stack:
            begin = stack.pop()
            if tok.end[0] > begin:
                inside.update(range(begin + 1, tok.end[0] + 1))
    return inside


def transform(path):
    src = open(path, encoding="utf-8").read()
    lines = src.splitlines(keepends=True)
    tree = ast.parse(src)
    start = split_line(tree, lines)
    if start is None:
        return None, "no executable body found"
    protect = string_continuation_lines(src)

    out = lines[:start - 1]
    out.append("def main():\n")
    for i in range(start - 1, len(lines)):
        ln, text = i + 1, lines[i]
        if ln in protect or text.strip() == "":
            out.append(text)
        else:
            out.append("    " + text)
    tail = "".join(out)
    if not tail.endswith("\n"):
        tail += "\n"
    tail += '\n\nif __name__ == "__main__":\n    main()\n'
    return tail, f"body from line {start} ({len(lines) - start + 1} lines) wrapped"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__.strip().splitlines()[-1]); sys.exit(2)
    for p in sys.argv[1:]:
        # idempotence: never wrap a file that already carries a guard
        if any(l.startswith("if __name__") for l in open(p, encoding="utf-8")):
            print(f"SKIP {p}: already guarded"); continue
        new, msg = transform(p)
        if new is None:
            print(f"SKIP {p}: {msg}"); continue
        try:
            ast.parse(new)
        except SyntaxError as e:
            print(f"FAIL {p}: {e}"); continue
        open(p, "w", encoding="utf-8").write(new)
        print(f"  ok  {p}: {msg}")
