#!/usr/bin/env python3
"""
script_io_scan.py — what does each pipeline script actually read and write?

WHY THIS IS A REPORT AND NOT A GATE

  `ledger_lint` states, deliberately, that it will not check the ledger's
  Consumes/Emits/Cited columns:

      NOT CHECKED — Consumes, Emits and Cited. Those need a human to read the
      script, and a tool that pretended to verify them would produce exactly
      the false assurance the ledger already suffers from.

  That reasoning stands and this tool does not overturn it. It writes nothing,
  sets no status, and passes no judgement. It answers one narrower question —
  *which path constants does this script's AST touch, and in which direction* —
  and prints the difference against the ledger row so a person reading the
  script has the mechanical half already done.

  The difference matters because the two halves fail differently. Whether a
  script still calls `to_csv(OUT_25_PANEL_FITS)` is decidable from the source.
  Whether the Methods Supplement still describes what that CSV contains is not,
  and no amount of AST walking will make it so. Everything this tool prints is
  from the first half. The status column belongs to the second.

WHAT IT CAN AND CANNOT SEE

  SEEN    direct calls whose argument is a path constant imported from
          utils.paths, by either import form:
              from utils.paths import OUT_X        ->  OUT_X
              from utils import paths              ->  paths.OUT_X
          reads:  read_csv/read_excel/read_parquet/read_file/np.load/open(...,'r')
                  Path.read_text/read_bytes
          writes: to_csv/to_excel/to_json/savefig/write_text/write_bytes/
                  open(...,'w'|'a'), json.dump into an opened constant

  UNSEEN  anything routed through a helper that takes the directory and builds
          the filename itself (`save_fig(fig, DIR_20, "...png")`), anything
          built by f-string from a loop variable, and anything a shared module
          reads on the script's behalf (`clearfell_common.load_clearfell_data`,
          `scraping_common`'s Sy lookup). These are REPORTED SEPARATELY as
          `helper` and `dynamic` lines rather than silently dropped, because a
          list that looks complete and is not is the failure this whole suite
          exists to prevent. The ledger's own header already warns about the
          first case; this tool makes it visible per script instead.

Usage:
    python3 tools/script_io_scan.py                # every script, vs the ledger
    python3 tools/script_io_scan.py 25 19 09d      # only these rows
    python3 tools/script_io_scan.py --raw 25       # resolved paths, no ledger
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-08-26.

import argparse
import ast
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "src"
LEDGER = REPO / "notes/ledgers/SCRIPT_LEDGER.md"

READ_FUNCS = {"read_csv", "read_excel", "read_parquet", "read_table",
              "read_json", "read_file", "load", "loadtxt", "genfromtxt",
              "imread", "read_text", "read_bytes"}
WRITE_FUNCS = {"to_csv", "to_excel", "to_json", "to_parquet", "savefig",
               "write_text", "write_bytes", "to_file", "savez", "save",
               "imsave", "write"}
# `save` and `write` are ambiguous (np.save writes; model.save writes; but
# `ax.save` is not a thing). Kept on the write side and flagged, never guessed
# into the read side.


def _paths_namespace() -> dict:
    """Resolve utils.paths constants to their filenames without importing data."""
    ns: dict = {}
    src = (SRC / "utils/paths.py").read_text(encoding="utf8")
    code = compile(src, str(SRC / "utils/paths.py"), "exec")
    ns["__file__"] = str(SRC / "utils/paths.py")
    exec(code, ns)  # paths.py is pure pathlib arithmetic; nothing is opened
    return {k: v for k, v in ns.items()
            if k.isupper() and isinstance(v, (Path, str))}


def param_roles(tree: ast.AST, seed: dict | None = None) -> dict[str, dict]:
    """For each local function, which parameters are used as a read or a write
    target inside it — keyed by both position and name.

    Iterated to a fixed point, because a path is often passed down two levels
    (`run_mode(m)` -> `plot_x(df, out)` -> `fig.savefig(out)`). Five rounds is
    far more than this codebase's deepest chain and terminates regardless.
    """
    funcs = {n.name: n for n in ast.walk(tree)
             if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    roles: dict[str, dict] = dict(seed or {})
    for _ in range(5):
        changed = False
        for fname, fn in funcs.items():
            names = [a.arg for a in fn.args.args] + [a.arg for a in fn.args.kwonlyargs]
            found: dict[str, str] = {}
            for node in ast.walk(fn):
                if not isinstance(node, ast.Call):
                    continue
                f = node.func
                call = f.attr if isinstance(f, ast.Attribute) else (
                    f.id if isinstance(f, ast.Name) else "")

                def note(arg, role):
                    if isinstance(arg, ast.Name) and arg.id in names:
                        found.setdefault(arg.id, role)
                    # `out.parent / "x.png"` and `out.with_suffix(...)` still
                    # write through the parameter.
                    elif isinstance(arg, ast.BinOp) and isinstance(arg.op, ast.Div):
                        note(arg.left, role)
                    elif isinstance(arg, ast.Attribute):
                        note(arg.value, role)

                if call == "open":
                    mode = "r"
                    if len(node.args) > 1 and isinstance(node.args[1], ast.Constant):
                        mode = str(node.args[1].value)
                    if node.args:
                        note(node.args[0], "w" if any(m in mode for m in "wax") else "r")
                elif call in WRITE_FUNCS:
                    if isinstance(f, ast.Attribute) and call in {"write_text", "write_bytes"}:
                        note(f.value, "w")
                    elif node.args:
                        note(node.args[0], "w")
                elif call in READ_FUNCS:
                    if isinstance(f, ast.Attribute) and call in {"read_text", "read_bytes"}:
                        note(f.value, "r")
                    elif node.args:
                        note(node.args[0], "r")
                elif call in roles:                       # pass-through
                    inner = roles[call]
                    for i, a in enumerate(node.args):
                        if inner.get(i):
                            note(a, inner[i])
                    for kw in node.keywords:
                        if inner.get(kw.arg):
                            note(kw.value, inner[kw.arg])

            table: dict = {}
            for i, p in enumerate(names):
                if p in found:
                    table[i] = found[p]
                    table[p] = found[p]
            if table != roles.get(fname):
                roles[fname] = table
                changed = True
        if not changed:
            break
    return roles


class Scan(ast.NodeVisitor):
    def __init__(self, const_names: set[str], roles: dict | None = None):
        self.param_roles = roles or {}
        self.const_names = const_names
        self.imported: set[str] = set()      # bare names imported from paths
        self.paths_alias: set[str] = set()   # module aliases for utils.paths
        self.reads: set[str] = set()
        self.writes: set[str] = set()
        self.alias: dict[str, set[str]] = {}  # local name -> path constant(s)
        self.dispatch: dict[str, set[str]] = {}   # dict-literal key -> constants
        self.dictvars: dict[str, set[str]] = {}   # dict VARIABLE -> its constants
        self.called: set[str] = set()        # analysed helpers this script calls
        self.via_reads: set[str] = set()     # opened by a helper on our behalf
        self.via_writes: set[str] = set()
        self.helper: list[str] = []          # dir constant handed to a helper
        self.dynamic: list[str] = []         # a path built, not named

    # -- imports ----------------------------------------------------------
    def visit_ImportFrom(self, node):
        mod = node.module or ""
        if mod.endswith("utils.paths") or mod.endswith("paths"):
            for a in node.names:
                if a.name == "*":
                    self.imported |= self.const_names
                else:
                    self.imported.add(a.asname or a.name)
        elif mod.endswith("utils") or mod == "utils":
            for a in node.names:
                if a.name == "paths":
                    self.paths_alias.add(a.asname or a.name)
        self.generic_visit(node)

    def visit_Import(self, node):
        for a in node.names:
            if a.name.endswith("utils.paths") or a.name == "paths":
                self.paths_alias.add(a.asname or a.name.split(".")[-1])
        self.generic_visit(node)

    # -- resolution -------------------------------------------------------
    def _const(self, node) -> str | None:
        """The path-constant NAME this expression denotes, or None."""
        if isinstance(node, ast.Name) and node.id in self.imported:
            return node.id
        # A module-level rebinding: Script 39 does `OUT_PER_WELL = paths.OUT_39_PER_WELL`
        # and then writes through the short name. Without following these, the
        # scan reported 39 as emitting nothing at all.

        if (isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
                and node.value.id in self.paths_alias
                and node.attr in self.const_names):
            return node.attr
        # DIR_X / "name.csv" — a constant joined to a literal. Resolvable, and
        # common enough that dropping it would lose real emits.
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            left = self._const(node.left)
            if left and isinstance(node.right, ast.Constant) \
                    and isinstance(node.right.value, str):
                return f"{left}/{node.right.value}"
        return None

    def _consts(self, node) -> list[str]:
        """Path constants this expression may denote — usually one, but a
        dispatch table lookup denotes one per mode.

        Script 25 runs summer and spring off `_METRICS`, a module-level list of
        dicts whose values are path constants, and writes through
        `m["out_per_well"]`. Eight of its real reads and writes are spelled that
        way; without this they would show only as unresolved `dynamic` lines.
        The lookup is by key across every dict literal in the file, so it is
        deliberately over-inclusive: better to name both modes' outputs than to
        name neither.
        """
        c = self._const(node)
        if c:
            return [c]
        # A name bound to a path constant somewhere in the file. Collected across
        # the whole module rather than per scope: `out_csv = A if summer else B`
        # is the same variable serving two constants, and both are real targets.
        # A name reused for unrelated purposes would over-report, which is the
        # side to err on for a record whose failure mode is looking complete.
        if isinstance(node, ast.Name) and node.id in self.alias:
            return sorted(self.alias[node.id])
        if isinstance(node, ast.IfExp):
            return sorted(set(self._consts(node.body)) | set(self._consts(node.orelse)))
        if isinstance(node, ast.Subscript):
            # OUT_FIG[window] — a module-level dict of path constants indexed by
            # a run-time key. Script 32 selects its two figures that way, and
            # both are real emits whichever branch runs.
            if isinstance(node.value, ast.Name) and node.value.id in self.dictvars:
                return sorted(self.dictvars[node.value.id])
            if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
                return sorted(self.dispatch.get(node.slice.value, ()))
        return []

    def _describe(self, node) -> str:
        try:
            return ast.unparse(node)[:70]
        except Exception:
            return "<expr>"

    # -- calls ------------------------------------------------------------
    def visit_Call(self, node):
        fn = node.func
        name = fn.attr if isinstance(fn, ast.Attribute) else (
            fn.id if isinstance(fn, ast.Name) else "")

        # open(path, mode)
        if name == "open":
            arg = node.args[0] if node.args else None
            mode = "r"
            if len(node.args) > 1 and isinstance(node.args[1], ast.Constant):
                mode = str(node.args[1].value)
            for kw in node.keywords:
                if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                    mode = str(kw.value.value)
            cs = self._consts(arg) if arg is not None else []
            if cs:
                (self.writes if any(m in mode for m in "wax") else self.reads).update(cs)
            elif arg is not None:
                self.dynamic.append(f"open({self._describe(arg)}, {mode!r})")

        # receiver-style: CONST.read_text() / CONST.write_text(...)
        elif isinstance(fn, ast.Attribute) and name in READ_FUNCS | WRITE_FUNCS:
            recv = self._consts(fn.value)
            if recv and name in {"read_text", "read_bytes"}:
                self.reads.update(recv)
            elif recv and name in {"write_text", "write_bytes"}:
                self.writes.update(recv)
            elif recv and name in {"to_csv", "savefig", "to_json"}:
                self.writes.update(recv)
            else:
                # argument-style: pd.read_csv(CONST) / df.to_csv(CONST)
                arg = node.args[0] if node.args else None
                cs = self._consts(arg) if arg is not None else []
                if cs:
                    (self.reads if name in READ_FUNCS else self.writes).update(cs)
                elif arg is not None:
                    # Report EVERY unresolvable target. An earlier draft filtered
                    # these on whether the expression "looked like a path", which
                    # dropped Script 25's four mode-dispatched writes
                    # (`pw.to_csv(m["out_per_well"])`) — the exact silent-drop
                    # this tool's docstring promises not to do.
                    self.dynamic.append(f"{name}({self._describe(arg)})")

        # A path constant handed to some other call. Two cases, and the second
        # is most of Script 25's figures: `plot_window_sweep(sweep, OUT_25_..._FIG)`
        # is a write, but only the callee knows that. PARAM_ROLES, computed in a
        # prior pass over this file's own function definitions, carries the
        # answer for local functions; anything else is reported as a helper call
        # with the direction left unstated rather than guessed.
        else:
            roles = self.param_roles.get(name)
            # builtins and formatting calls are not I/O; `print(DIR_17)` is a
            # console line, not a write.
            analysed = roles is not None or name in {
                "print", "str", "Path", "len", "format", "f", "repr", "exists",
                "mkdir", "name", "resolve", "sorted", "list", "set"}
            if analysed:
                self.called.add(name)
            roles = roles or {}
            for i, arg in enumerate(node.args):
                cs = self._consts(arg)
                if not cs:
                    continue
                role = roles.get(i)
                if role == "w":
                    self.writes.update(cs)
                elif role == "r":
                    self.reads.update(cs)
                elif not analysed:
                    for c in cs:
                        self.helper.append(f"{name}(... {c} ...)")
            for kw in node.keywords:
                cs = self._consts(kw.value)
                if not cs:
                    continue
                role = roles.get(kw.arg)
                if role == "w":
                    self.writes.update(cs)
                elif role == "r":
                    self.reads.update(cs)
                elif not analysed:
                    for c in cs:
                        self.helper.append(f"{name}({kw.arg}={c})")

        self.generic_visit(node)


_HELPER_ROLES: dict | None = None
UNPARSEABLE: list[str] = []


def helper_roles() -> dict:
    """Parameter roles for the shared modules in src/utils.

    Derived, not tabulated. The house figure-saver is
    `render_utils.render_figure(fig, out_path)`, so most scripts never call
    `savefig` at all — Script 25 calls it zero times and still emits nine
    figures. A hand-written table of such helpers would be a second place the
    same fact lives, which is the failure mode this project keeps paying for;
    reading the helpers' own source keeps it to one.
    """
    global _HELPER_ROLES
    if _HELPER_ROLES is None:
        _HELPER_ROLES = {}
        for p in sorted((SRC / "utils").glob("*.py")):
            try:
                _HELPER_ROLES.update(param_roles(ast.parse(p.read_text(encoding="utf8"))))
            except SyntaxError as e:
                # Do not swallow this. A helper we cannot parse is a helper
                # whose writes are invisible, and the report must say so.
                UNPARSEABLE.append(f"{p.name}: {e.msg} (line {e.lineno})")
    return _HELPER_ROLES


_HELPER_IO: dict | None = None


def helper_io(const_names: set[str]) -> dict:
    """Path constants each shared-module function reads or writes ITSELF.

    A caller's own AST cannot see these: `clearfell_common.load_clearfell_data()`
    opens five files using constants imported inside `clearfell_common`, so a
    script that consumes all five appears to consume nothing. Six of the rows
    reconciled on 2026-08-26 name exactly such reads, and without this the tool
    would report the corrected rows as wrong.

    Reported under `via` rather than merged into the direct lists, because
    "this script opens the file" and "a loader opens it on the script's behalf"
    are different facts and the ledger's Consumes column has cells that say so.
    """
    global _HELPER_IO
    if _HELPER_IO is not None:
        return _HELPER_IO
    _HELPER_IO = {}
    roles = helper_roles()
    for p in sorted((SRC / "utils").glob("*.py")):
        try:
            tree = ast.parse(p.read_text(encoding="utf8"))
        except SyntaxError:
            continue                      # already reported by helper_roles()
        mod = Scan(const_names, roles)
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                mod.visit(node)
        imported, alias_seed = set(mod.imported), set(mod.paths_alias)
        funcs = [n for n in ast.walk(tree)
                 if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        for _ in range(3):                # intra-module call chains
            for fn in funcs:
                s = Scan(const_names, roles)
                s.imported, s.paths_alias = set(imported), set(alias_seed)
                for node in ast.walk(fn):
                    if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                            and isinstance(node.targets[0], ast.Name):
                        cs = s._consts(node.value)
                        if cs:
                            s.alias.setdefault(node.targets[0].id, set()).update(cs)
                for node in fn.body:
                    s.visit(node)
                r, w = set(s.reads), set(s.writes)
                for called in s.called:
                    if called in _HELPER_IO:
                        r |= _HELPER_IO[called][0]
                        w |= _HELPER_IO[called][1]
                if (r, w) != _HELPER_IO.get(fn.name):
                    _HELPER_IO[fn.name] = (r, w)
    return _HELPER_IO


def scan(path: Path, const_names: set[str]) -> Scan:
    tree = ast.parse(path.read_text(encoding="utf8"), str(path))
    roles = dict(helper_roles())
    roles.update(param_roles(tree, seed=roles))   # a local definition wins
    s = Scan(const_names, roles)
    # Imports and dispatch tables must be known before the call walk, and the
    # visitor sees nodes in source order — so seed both up front.
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            s.visit(node)
    for _ in range(3):                       # aliases may chain
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                    and isinstance(node.targets[0], ast.Name):
                cs = s._consts(node.value)
                if cs:
                    s.alias.setdefault(node.targets[0].id, set()).update(cs)
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            for k, v in zip(node.keys, node.values):
                if isinstance(k, ast.Constant) and isinstance(k.value, str):
                    c = s._const(v)
                    if c:
                        s.dispatch.setdefault(k.value, set()).add(c)
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name) \
                and isinstance(node.value, ast.Dict):
            got = {c for v in node.value.values for c in ([s._const(v)] if s._const(v) else [])}
            if got:
                s.dictvars[node.targets[0].id] = got
    s.reads.clear(); s.writes.clear(); s.helper.clear(); s.dynamic.clear()
    s.visit(tree)
    hio = helper_io(const_names)
    for fname in s.called:
        r, w = hio.get(fname, (set(), set()))
        s.via_reads |= r - s.reads
        s.via_writes |= w - s.writes
    return s


def basename(const: str, ns: dict) -> str:
    if "/" in const:
        head, tail = const.split("/", 1)
        return tail
    v = ns.get(const)
    return Path(str(v)).name if v is not None else f"<{const}?>"


_ROW = re.compile(r"^\|\s*([0-9]+[a-z]?)\s*\|\s*([^|]+?)\s*\|")


def ledger_rows() -> dict[str, list[str]]:
    rows = {}
    for line in LEDGER.read_text(encoding="utf8").splitlines():
        m = _ROW.match(line)
        if not m or m.group(1) == "#":
            continue
        rows[m.group(1)] = [c.strip() for c in line.strip().strip("|").split("|")]
    return rows


def cells_to_names(cell: str) -> set[str]:
    """Filenames the ledger cell mentions, ignoring its prose."""
    return set(re.findall(
        r"[0-9A-Za-z_]+\.(?:csv|png|jpg|jpeg|svg|txt|json|html|ods|geojson|kml|tif)",
        cell))


def cell_prefixes(cell: str, row: str = "") -> set[str]:
    """Output prefixes a cell covers, including the ranges it writes in shorthand.

    The ledger does not spell every file: Script 25's figures are "25_05…08",
    Script 10l's are "10l_01…03 summer + 10l_06…08 spring", Script 09a's CSVs are
    "09_scrape_01…04b_*.csv". Matching only on full filenames reports every one of
    those as missing from the ledger, which would turn a tidy row into twenty
    false findings. Ranges are expanded; anything outside one still has to be
    named. The stem before the number is arbitrary, because "09_scrape_" is as
    much a prefix as "25_".
    """
    out: set[str] = set()
    stem = r"([0-9]+[a-z]?(?:_[A-Za-z]+)*_)"
    for m in re.finditer(stem + r"([0-9]+)\s*(?:…|\.{2,3})\s*([0-9]+)([a-z]?)", cell):
        head, lo, hi, suf = m.group(1), m.group(2), m.group(3), m.group(4)
        width = len(lo)
        for n in range(int(lo), int(hi) + 1):
            out.add(f"{head}{n:0{width}d}")
        out.add(f"{head}{int(hi):0{width}d}{suf}")
    # "25_02/03 (+spring)" — one stem, two output numbers.
    for m in re.finditer(stem + r"([0-9]+)((?:/[0-9]+)+)", cell):
        width = len(m.group(2))
        for n in [m.group(2)] + m.group(3).strip("/").split("/"):
            out.add(f"{m.group(1)}{int(n):0{width}d}")
    for m in re.finditer(stem + r"([0-9]+[a-z]?)", cell):
        out.add(f"{m.group(1)}{m.group(2)}")
    # "10a_04…08 + S1–S3" — the supplementary figures carry the row's own stem,
    # which the cell leaves implicit.
    if row:
        for m in re.finditer(r"\bS([0-9]+)\s*[–—-]\s*S([0-9]+)", cell):
            for n in range(int(m.group(1)), int(m.group(2)) + 1):
                out.add(f"{row}_S{n}")
    return out


_PREFIX = re.compile(r"^([0-9]+[a-z]?(?:_[A-Za-z]+)*_[0-9]+[a-z]?)")


def covered(fname: str, names: set[str], prefixes: set[str]) -> bool:
    if fname in names:
        return True
    m = _PREFIX.match(fname)
    if not m:
        return False
    tok = m.group(1)
    # "09_scrape_04b_beta3_era_summary.csv" must match the "09_scrape_04b" a
    # range produced, and "09_scrape_01_full_parameters.csv" the "09_scrape_01".
    return tok in prefixes or tok.rstrip("abcdefghijklmnopqrstuvwxyz") in prefixes


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("rows", nargs="*", help="ledger row numbers (default: all)")
    ap.add_argument("--raw", action="store_true",
                    help="print resolved reads/writes without the ledger diff")
    a = ap.parse_args()

    ns = _paths_namespace()
    const_names = set(ns)
    rows = ledger_rows()
    helper_roles()
    if UNPARSEABLE:
        print(f"  NOTE — this interpreter is Python {sys.version_info.major}."
              f"{sys.version_info.minor} and cannot parse:")
        for u in UNPARSEABLE:
            print(f"      {u}")
        print("  Any path those module(s) write is INVISIBLE below.")
        print("  This line means one of two things, and they are not close: "
              "either the pipeline")
        print("  cannot import that module, or YOU ARE NOT ON THE MACHINE THAT "
              "RUNS THE PIPELINE.")
        print("  On 2026-08-26 it was the second — a Cowork sandbox on 3.10 "
              "against a project that")
        print("  runs on 3.12.3 — and it was written up as a five-week outage "
              "before anyone checked.")
        print("  Compare `python3 --version` where the pipeline actually runs, "
              "first.")

    scripts = sorted(SRC.glob("*.py"))
    by_row = {}
    for p in scripts:
        m = re.match(r"^([0-9]+[a-z]?)_", p.name)
        if m:
            by_row[m.group(1)] = p

    targets = a.rows or sorted(by_row, key=lambda r: (int(re.sub(r"\D", "", r)), r))
    for r in targets:
        p = by_row.get(r)
        if p is None:
            print(f"{r}: no script")
            continue
        s = scan(p, const_names)
        # A directory constant is not a file. Script 17 hands DIR_OUT to its own
        # loader, which builds the filenames inside; reporting "outputs" as a
        # consumed file would be noise in a column that lists CSVs.
        def files(cs):
            return sorted({b for b in (basename(c, ns) for c in cs) if "." in b})
        reads, writes = files(s.reads), files(s.writes)
        via_r, via_w = files(s.via_reads), files(s.via_writes)
        print(f"\n=== {r}  {p.name} " + "=" * (46 - len(p.name)))
        print(f"  reads  ({len(reads):>2}): {', '.join(reads) or '—'}")
        print(f"  writes ({len(writes):>2}): {', '.join(writes) or '—'}")
        if via_r or via_w:
            print(f"  via    : opened by a helper on this script's behalf — "
                  f"reads {', '.join(via_r) or '—'}"
                  + (f"; writes {', '.join(via_w)}" if via_w else ""))
        if s.helper:
            print(f"  helper : {len(s.helper)} path constant(s) handed to a call "
                  f"whose direction could not be resolved")
            for h in sorted(set(s.helper))[:6]:
                print(f"           {h}")
        if s.dynamic:
            print(f"  dynamic: {len(s.dynamic)} target(s) not resolvable to a path constant")
            for d in sorted(set(s.dynamic)):
                print(f"           {d}")
        if a.raw or r not in rows:
            continue
        cells = rows[r]
        led_c = cells_to_names(cells[3])
        led_e = cells_to_names(cells[4]) | cells_to_names(cells[5])
        pre_c = cell_prefixes(cells[3], r)
        pre_e = cell_prefixes(cells[4], r) | cell_prefixes(cells[5], r)
        code_c, code_e = set(reads) | set(via_r), set(writes) | set(via_w)
        for label, led, pre, code in (("Consumes", led_c, pre_c, code_c),
                                      ("Emits", led_e, pre_e, code_e)):
            only_led = sorted(n for n in led if n not in code)
            only_code = sorted(n for n in code if not covered(n, led, pre))
            if label == "Consumes":
                # The ledger header: "A script's own second-pass self-reads
                # appear under Emits, not Consumes". Reporting them as a missing
                # Consumes would be arguing with the record's own convention.
                only_code = [n for n in only_code if not covered(n, led_e, pre_e)]
            if only_led or only_code:
                print(f"  {label} differs from the ledger row:")
                if only_led:
                    print(f"      ledger only: {', '.join(only_led)}")
                if only_code:
                    print(f"      code only  : {', '.join(only_code)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
