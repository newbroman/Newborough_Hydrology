#!/usr/bin/env python3
"""
prune_versions — cap how many versions of each versioned document are kept.

WHY. Sixty-six Methods Supplements, twenty Paper 1s. Every edit batch saves to a
bumped filename and the prior version is left on disk (the versioned-document
rule), which is right — but nothing ever removed the tail, and the tail is now
most of docs/.

WHAT IS KEPT, and why the oldest is in the set:

    the NEWEST            the live document; never a candidate for removal
    the OLDEST            the origin of the family. It is the only version that
                          says what the document looked like before the project
                          started editing it, and it costs one file. Martin's
                          call, 2026-09-10.
    the next most recent  filling the quota, newest-first

so with --keep 10 a family retains its newest, its oldest, and the eight most
recent of the rest. A family at or below the quota is untouched.

WHAT IT REFUSES TO DO:

  * run at all when `odt_media verify` is not green. Superseded documents are
    stripped to stubs with a `<name>.odt.media.json` sidecar, and verify is the
    gate that proves each still rebuilds byte-identically. Pruning on top of a
    broken store would destroy the evidence of what broke.
  * remove a document without its sidecar. `odt_media.verify()` walks sidecars
    and FAULTs on one whose document is gone, so an orphaned sidecar converts
    this tool's tidy-up into a failing check_all.
  * delete anything without --apply. The default is a plan.

ORPHANED STORE IMAGES are reported, never deleted. An image in docs/media_store
that no surviving sidecar references is dead weight, but the store is also the
Drive archive (D-081, D-149) and a stale reference is cheaper than a lost image.

Usage:
    python3 tools/prune_versions.py                 # plan, all families
    python3 tools/prune_versions.py --keep 12
    python3 tools/prune_versions.py --only Methods
    python3 tools/prune_versions.py --apply         # actually remove
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-09-10. First version.

import argparse
import json
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
REPO = TOOLS.parent
sys.path.insert(0, str(TOOLS))

from refresh_mirrors import SOURCES, _version_key  # noqa: E402
import odt_media  # noqa: E402

STORE = REPO / "docs" / "media_store"


def families() -> dict[str, list[Path]]:
    """Every versioned SOURCES pattern, resolved to its files, newest last."""
    out: dict[str, list[Path]] = {}
    for pattern, _mirror, versioned in SOURCES:
        if not versioned:
            continue
        matches = sorted(REPO.glob(pattern), key=_version_key)
        if matches:
            out[pattern] = matches
    return out


def plan(keep: int, only: str | None) -> list[tuple[str, list[Path], list[Path]]]:
    rows = []
    for pattern, files in families().items():
        if only and only.lower() not in pattern.lower():
            continue
        if len(files) <= keep:
            rows.append((pattern, files, []))
            continue
        newest, oldest = files[-1], files[0]
        quota = [f for f in reversed(files) if f != oldest][: keep - 1]
        kept = {newest, oldest, *quota}
        drop = [f for f in files if f not in kept]
        rows.append((pattern, sorted(kept, key=_version_key), drop))
    return rows


def referenced_images() -> set[str]:
    names: set[str] = set()
    for side in REPO.glob("docs/**/*.odt.media.json"):
        try:
            d = json.loads(side.read_text(encoding="utf-8"))
        except Exception:
            continue
        for entry in d.get("images", d.get("entries", [])):
            n = entry.get("store") if isinstance(entry, dict) else None
            if n:
                names.add(Path(n).name)
    return names


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep", type=int, default=10,
                    help="versions retained per family, newest + oldest included (default 10)")
    ap.add_argument("--only", help="substring of the family pattern")
    ap.add_argument("--apply", action="store_true", help="remove; default is a plan")
    a = ap.parse_args(argv[1:])

    if a.keep < 3:
        print("  --keep must be at least 3 (newest, oldest, and one more)")
        return 1

    if a.apply:
        print("Gate: odt_media verify")
        if odt_media.verify(quiet=True) != 0:
            print("  REFUSED — the media store is not green. Fix that first: a prune on top")
            print("            of a broken store removes the evidence of what broke.")
            return 1

    rows = plan(a.keep, a.only)
    total_drop = 0
    total_bytes = 0
    for pattern, kept, drop in rows:
        fam = pattern.split("/")[-1]
        if not drop:
            print(f"  ok      {fam}  {len(kept)} version(s), at or under the quota")
            continue
        size = sum(f.stat().st_size for f in drop if f.is_file())
        total_drop += len(drop)
        total_bytes += size
        print(f"  prune   {fam}  {len(kept) + len(drop)} -> {len(kept)}  "
              f"(remove {len(drop)}, {size / 1048576:.1f} MB)")
        print(f"            keep newest {kept[-1].name}")
        print(f"            keep oldest {kept[0].name}")
        if not a.apply:
            continue
        for f in drop:
            side = odt_media.sidecar_path(f)
            for victim in (f, side):
                if victim.is_file():
                    try:
                        victim.unlink()
                    except OSError:
                        odt_media._retire(victim)   # the mount refuses unlink

    print(f"\n  {total_drop} file(s), {total_bytes / 1048576:.1f} MB "
          f"{'removed' if a.apply else 'would be removed'}")

    if a.apply and total_drop:
        rc = odt_media.verify(quiet=True)
        print(f"  post-prune odt_media verify: {'OK' if rc == 0 else 'FAIL'}")
        if rc:
            return 1

    referenced = referenced_images()
    if STORE.is_dir() and referenced:
        orphans = [f for f in STORE.glob("*") if f.name not in referenced]
        if orphans:
            mb = sum(f.stat().st_size for f in orphans) / 1048576
            print(f"  note: {len(orphans)} store image(s) ({mb:.1f} MB) referenced by no "
                  f"surviving sidecar — reported, not removed")

    print(f"\nprune_versions: {'APPLIED' if a.apply else 'PLAN ONLY'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
