#!/usr/bin/env python3
"""find_missing_docs_archives.py — look for the missing documents INSIDE archives.

Martin bundled parts of the project store into archives to compact it, so a
document can be present on disk and still invisible to a filename sweep: it is
a member of a zip, not a file. This reads archive indexes and matches member
names against the missing list.

    python3 tools/find_missing_docs_archives.py            report only
    python3 tools/find_missing_docs_archives.py --extract  pull matches out

Read-only on the archives themselves: members are extracted to
Updates_required/_recovered_<date>/, never back into the archive, and the
archive is never rewritten. Matching is on the BASENAME, so a document filed
under any directory inside the archive is still found.

Roots come from tools/_search_roots.sh, the same list the other sweeps use, so
the cloud drives are covered. NRG_SKIP_CLOUD=1 skips them.
"""
import argparse, datetime, hashlib, os, pathlib, subprocess, sys, tarfile, zipfile

REPO = pathlib.Path(__file__).resolve().parent.parent
SUFFIXES = (".zip", ".tar", ".tar.gz", ".tgz", ".tar.bz2", ".tbz2",
            ".tar.xz", ".txz", ".7z", ".rar", ".odt.zip")


def missing_names():
    out = subprocess.run([sys.executable, str(REPO / "tools" / "docref_lint.py"),
                          "--list-missing"], capture_output=True, text=True)
    if out.returncode != 0:
        sys.exit("cannot read the missing-document list from tools/docref_lint.py")
    return {n.strip() for n in out.stdout.splitlines() if n.strip()}


def roots():
    out = subprocess.run(
        ["bash", "-c", f'source "{REPO}/tools/_search_roots.sh"; printf "%s\\n" "${{ROOTS[@]}}"'],
        capture_output=True, text=True)
    return [r for r in out.stdout.splitlines() if r and os.path.isdir(r)]


def find_archives(rs):
    seen, found = set(), []
    for r in rs:
        for dp, dn, fn in os.walk(r, onerror=lambda e: None):
            # -xdev equivalent: do not cross into another filesystem
            try:
                if os.stat(dp).st_dev != os.stat(r).st_dev:
                    dn[:] = []
                    continue
            except OSError:
                dn[:] = []
                continue
            if str(REPO) in dp:
                dn[:] = []
                continue
            dn[:] = [d for d in dn if d not in (".git", "node_modules", "__pycache__", "venv")]
            for f in fn:
                if f.lower().endswith(SUFFIXES):
                    p = os.path.join(dp, f)
                    try:
                        key = os.stat(p).st_ino, os.stat(p).st_size
                    except OSError:
                        continue
                    if key in seen:
                        continue
                    seen.add(key)
                    found.append(p)
    return sorted(found)


def members(path):
    """(member_name, reader) pairs. reader() returns bytes, or None if unsupported."""
    low = path.lower()
    try:
        if low.endswith(".zip"):
            z = zipfile.ZipFile(path)
            return [(i.filename, (lambda n=i.filename: z.read(n))) for i in z.infolist()
                    if not i.is_dir()]
        if any(low.endswith(s) for s in (".tar", ".tar.gz", ".tgz", ".tar.bz2",
                                         ".tbz2", ".tar.xz", ".txz")):
            t = tarfile.open(path)
            return [(m.name, (lambda n=m.name: t.extractfile(n).read()))
                    for m in t.getmembers() if m.isfile()]
        if low.endswith((".7z", ".rar")):
            exe = "7z" if low.endswith(".7z") else "unrar"
            out = subprocess.run([exe, "l", path], capture_output=True, text=True, timeout=120)
            if out.returncode != 0:
                return []
            return [(ln.split()[-1], None) for ln in out.stdout.splitlines()
                    if ln.strip() and "/" in ln or ln.strip().endswith(".md")]
    except Exception:
        return []
    return []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--extract", action="store_true",
                    help="write matching members into Updates_required/_recovered_<date>/")
    a = ap.parse_args()

    names = missing_names()
    rs = roots()
    print(f"== {len(names)} document(s) to look for, {len(rs)} search root(s) ==")
    archives = find_archives(rs)
    print(f"== {len(archives)} archive(s) to read ==")

    dest = REPO / "Updates_required" / f"_recovered_{datetime.date.today().isoformat()}"
    hits = 0
    # Dedup per document name, not globally: two documents can hold identical
    # bytes and both are wanted. Same rule as stage_recovered_docs.sh.
    seen_by_name = {}
    dupes = 0
    unreadable = []
    for arc in archives:
        ms = members(arc)
        if not ms:
            # empty is normal for an archive with no files; unreadable is not
            if not os.access(arc, os.R_OK) or arc.lower().endswith((".7z", ".rar")):
                unreadable.append(arc)
            continue
        for name, read in ms:
            base = pathlib.PurePosixPath(name).name
            if base not in names:
                continue
            hits += 1
            print(f"  {base}")
            print(f"      in  {arc}")
            print(f"      at  {name}")
            if a.extract:
                if read is None:
                    print("      cannot extract this archive type here — use the "
                          "file manager")
                    continue
                try:
                    data = read()
                except Exception as e:
                    print(f"      extract failed: {e}")
                    continue
                h = hashlib.sha256(data).hexdigest()[:12]
                if h in seen_by_name.setdefault(base, set()):
                    dupes += 1
                    print("      byte-identical to a copy already staged — skipped")
                    continue
                seen_by_name[base].add(h)
                dest.mkdir(parents=True, exist_ok=True)
                tag = pathlib.Path(arc).name
                for s in sorted(SUFFIXES, key=len, reverse=True):
                    if tag.lower().endswith(s):
                        tag = tag[: -len(s)]
                        break
                tag = tag.replace(" ", "_")[:40]
                out = dest / f"{base[:-3]}__archive_{tag}_{h}.md"
                if out.exists():
                    print(f"      already staged as {out.name}")
                else:
                    out.write_bytes(data)
                    print(f"      extracted -> {out.name}")

    print()
    if unreadable:
        print(f"{len(unreadable)} archive(s) could not be read "
              f"(7z/rar need the 7z or unrar binary):")
        for u in unreadable[:10]:
            print(f"   {u}")
    print(f"{hits} match(es) across {len(archives)} archive(s)"
          + (f", {dupes} byte-identical duplicate(s) skipped" if dupes else ""))
    if hits and not a.extract:
        print("re-run with --extract to pull them out")
    if hits and a.extract:
        print("Nothing committed, nothing removed from any archive. Tell Claude.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
