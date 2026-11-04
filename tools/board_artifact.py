#!/usr/bin/env python3
"""board_artifact — the work board as a page Martin can read from anywhere (R6(a), D-300).

WHY A PAGE AND NOT JUST THE TERMINAL

  tools/work_board.py answers "who holds what" for whoever is sitting in front of a shell. The
  request this answers (2026-11-04, 21:18) was different: "so that it's easier for different chats
  to monitor and for ME to regulate what's going on" - from wherever he is, including his phone.
  So the same board that prints in a session is also rendered as a private claude.ai artifact.

  doc_lock.py CANNOT publish it. Publishing is a session's act, not a script's, so a take or a
  release leaves a marker (working/.board_publish_owed) and `--check` tells the next session the
  page is behind. That is the pattern tools/proof_copy.py already uses for the proof bundle, which
  is why it is the pattern here.

WHERE THE DATA MAY AND MAY NOT GO

  Claim metadata is PRIVATE - chat names, notes, what each chat is working on. R6's one constraint
  is that none of it may be copied into the public repository, so:

    the rendered HTML      -> scratch/board/index.html, which is gitignored
    the published URL      -> working/.board_artifact.json, the private half
    this script            -> public, and carries no data at all

  Never render into docs/, notes/ or anywhere else the public repository tracks.

Usage
  python3 tools/board_artifact.py                      # render to scratch/board/index.html
  python3 tools/board_artifact.py --check              # is a republish owed? (exit 1 if so)
  python3 tools/board_artifact.py --published URL      # record the publish, clear the marker
  python3 tools/board_artifact.py --url                # print the artifact's URL, if known
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-11-04 (D-300, R6(a), spec
#   NRG_handover_control_board_2026-11-04, signed off). First issue.

import argparse
import datetime
import html
import json
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parents[1]
REPO = pathlib.Path(os.environ.get("NRG_REPO_ROOT") or HERE).resolve()
sys.path.insert(0, str(HERE / "tools"))

OUT = REPO / "scratch/board/index.html"          # gitignored - see the docstring
STATE = REPO / "working/.board_artifact.json"    # private half
OWED = REPO / "working/.board_publish_owed"

# Palette and faces are set in the :root block below, which is the design plan: a sand/marram
# neutral with a slate ink, because that is the ground this project measures. Semantic colour is
# kept away from the accent so a flag never reads as decoration.
FONTS = ('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
         'family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@400;600&display=swap">')

CSS = """
<style>
/* Layout: one column of labelled bands, summary before detail; the claim table scrolls in itself. */
:root {
  --sand: #f6f3ec; --sand-2: #ece7da; --ink: #22281f; --ink-2: #5b6356;
  --rule: #d6cfbe; --accent: #2f5d50; --ok: #3f7d4e; --warn: #9a6514; --crit: #a33124;
  --font-body: "IBM Plex Sans", ui-sans-serif, system-ui, sans-serif;
  --font-mono: "IBM Plex Mono", ui-monospace, "SFMono-Regular", Menlo, monospace;
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --sand: #16180f; --sand-2: #1f2218; --ink: #e8e6dc; --ink-2: #a3a899;
  --rule: #343828; --accent: #7fb6a4; --ok: #7bc08c; --warn: #d9a24a; --crit: #e2887c;
  color-scheme: dark; } }
:root[data-theme="dark"] {
  --sand: #16180f; --sand-2: #1f2218; --ink: #e8e6dc; --ink-2: #a3a899;
  --rule: #343828; --accent: #7fb6a4; --ok: #7bc08c; --warn: #d9a24a; --crit: #e2887c;
  color-scheme: dark; }
body { background: var(--sand); color: var(--ink); font-family: var(--font-body); line-height: 1.5;
  font-size: 15px; }
.wrap { max-width: 50rem; margin: 0 auto;
  padding-left: max(16px, env(safe-area-inset-left, 0px));
  padding-right: max(16px, env(safe-area-inset-right, 0px)); padding-block: 1.5rem 3rem; }
h1 { font-size: 1.45rem; font-weight: 600; letter-spacing: -0.01em; margin: 0; text-wrap: balance; }
h2 { font-size: 0.72rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em;
  color: var(--ink-2); margin: 2rem 0 0.6rem; }
.sub { color: var(--ink-2); font-size: 0.85rem; margin: 0.15rem 0 0; }
.digest { font-family: var(--font-mono); font-size: 0.86rem; background: var(--sand-2);
  border-left: 3px solid var(--accent); padding: 0.7rem 0.85rem; margin-top: 1rem;
  border-radius: 0 4px 4px 0; }
.banner { border: 1px solid var(--crit); border-left-width: 4px; background: var(--sand-2);
  padding: 0.8rem 0.9rem; margin-top: 1rem; border-radius: 0 4px 4px 0; }
.banner b { color: var(--crit); }
.banner code { display: block; font-family: var(--font-mono); font-size: 0.8rem; margin-top: 0.3rem; }
.grid { display: grid; gap: 0.75rem; grid-template-columns: repeat(auto-fit, minmax(14rem, 1fr)); }
.card { background: var(--sand-2); border: 1px solid var(--rule); border-radius: 5px;
  padding: 0.8rem 0.9rem; min-width: 0; }
.card h3 { margin: 0; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.08em;
  color: var(--ink-2); font-weight: 600; }
.card .big { font-family: var(--font-mono); font-size: 1rem; margin-top: 0.3rem;
  font-variant-numeric: tabular-nums; }
.card .meta { color: var(--ink-2); font-size: 0.78rem; margin-top: 0.3rem; }
.tablewrap { overflow-x: auto; }
table { border-collapse: collapse; width: 100%; font-size: 0.85rem; }
th { text-align: left; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.08em;
  color: var(--ink-2); font-weight: 600; border-bottom: 1px solid var(--rule);
  padding: 0.3rem 0.6rem 0.3rem 0; white-space: nowrap; }
td { padding: 0.45rem 0.6rem 0.45rem 0; border-bottom: 1px solid var(--rule); vertical-align: top; }
td.mono, .mono { font-family: var(--font-mono); font-variant-numeric: tabular-nums; }
.pill { display: inline-block; font-size: 0.7rem; font-family: var(--font-mono); padding: 0.1rem 0.4rem;
  border-radius: 3px; border: 1px solid currentColor; white-space: nowrap; }
.pill.ok { color: var(--ok); } .pill.warn { color: var(--warn); } .pill.crit { color: var(--crit); }
.pill.quiet { color: var(--ink-2); }
ul { margin: 0.3rem 0 0; padding-left: 1.1rem; }
li { margin: 0.15rem 0; }
.free { color: var(--ink-2); font-size: 0.82rem; font-family: var(--font-mono); }
footer { margin-top: 2.5rem; border-top: 1px solid var(--rule); padding-top: 0.9rem;
  color: var(--ink-2); font-size: 0.78rem; }
footer code { font-family: var(--font-mono); }
a { color: var(--accent); }
</style>
"""


def esc(x) -> str:
    return html.escape(str(x if x is not None else ""))


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M") + " UTC"


def flag_pill(flag: str) -> str:
    cls = {"ABANDONED": "crit", "STALE": "warn"}.get(flag, "quiet")
    return f'<span class="pill {cls}">{esc(flag)}</span>' if flag else ""


def render_html(B: dict) -> str:
    import work_board
    P = [FONTS, CSS, '<title>NRG Work Board</title>',
         '<meta name="claude:viewport-fit-sides" content="cover">', '<div class="wrap">']
    P.append("<h1>NRG work board</h1>")
    P.append(f'<p class="sub">Who holds what across the two repositories of one working tree. '
             f'Generated {esc(_now())}.</p>')
    P.append(f'<p class="digest">{esc(work_board.digest(B))}</p>')

    if B.get("store") == "ABSENT":
        P.append('<div class="banner"><b>The private repository is not attached to the session that '
                 'rendered this page.</b> Every claim below reads UNKNOWN, not free — another chat may '
                 'hold any of them. Attach both with push access and re-render:'
                 '<code>add_repo newbroman/Newborough_Hydrology          access=push<br>'
                 'add_repo newbroman/Newborough_Hydrology_working  access=push</code></div>')
    for w in B.get("warnings") or []:
        P.append(f'<div class="banner"><b>{esc(w)}</b></div>')

    # ── repositories ────────────────────────────────────────────────────────
    P.append("<h2>Repositories</h2><div class='grid'>")
    for r in B.get("repos") or []:
        if not r.get("present"):
            P.append(f'<div class="card"><h3>{esc(r["name"])}</h3>'
                     f'<div class="big">not present</div>'
                     f'<div class="meta">{esc(r.get("holds"))}</div></div>')
            continue
        if r.get("behind") or r.get("ahead"):
            pos = f'{r.get("ahead", 0)} ahead, {r.get("behind", 0)} behind'
            pill = '<span class="pill warn">diverged</span>'
        else:
            pos, pill = "level with origin/main", '<span class="pill ok">level</span>'
        fetch = f'fetched {esc(r["last_fetch"])}' if r.get("last_fetch") else "last fetch unknown"
        if r.get("origin_moved"):
            fetch = '<span class="pill crit">origin has moved — fetch</span>'
        P.append(f'<div class="card"><h3>{esc(r["name"])} {pill}</h3>'
                 f'<div class="big">{esc(r.get("head"))} on {esc(r.get("branch"))}</div>'
                 f'<div class="meta">{esc(pos)}<br>{fetch}<br>{esc(r.get("holds"))}</div></div>')
    P.append("</div>")

    # ── the machine lock ────────────────────────────────────────────────────
    ml = B.get("machine_lock") or {}
    P.append("<h2>Documents — machine lock</h2>")
    if ml.get("holder"):
        P.append(f'<div class="card"><h3>held</h3><div class="big">{esc(ml["holder"])}</div>'
                 f'<div class="meta">since {esc(ml.get("since"))}'
                 + (f'<br>{esc(ml.get("note"))}' if ml.get("note") else "") + '</div></div>')
    else:
        P.append('<div class="card"><h3>free</h3><div class="big">no machine holds the ODTs</div>'
                 '<div class="meta">take it before editing any ODT, so Drive cannot fall behind</div></div>')

    # ── claims ──────────────────────────────────────────────────────────────
    P.append("<h2>Claims</h2>")
    claims = B.get("claims") or {}
    stale = B.get("stale") or {}
    held = [(k, v) for k, v in claims.items() if v and v != "UNKNOWN"]
    unknown = [k for k, v in claims.items() if v == "UNKNOWN"]
    free = [k for k, v in claims.items() if not v]
    if held:
        P.append('<div class="tablewrap"><table><thead><tr><th>claim</th><th>chat</th><th>where</th>'
                 '<th>taken</th><th>last activity</th><th>note</th></tr></thead><tbody>')
        for k, c in sorted(held):
            st = stale.get(k) or {}
            act = c.get("touched") or "—"
            P.append(f'<tr><td class="mono">{esc(k)}</td><td>{esc(c.get("chat"))}</td>'
                     f'<td class="mono">{esc(c.get("mode") or "?")}</td>'
                     f'<td class="mono">{esc(c.get("since"))}</td>'
                     f'<td class="mono">{esc(act)} {flag_pill(st.get("flag", ""))}</td>'
                     f'<td>{esc(c.get("note"))}'
                     + (f'<br><a href="{esc(c["link"])}">open the chat</a>' if c.get("link") else "")
                     + '</td></tr>')
        P.append("</tbody></table></div>")
    else:
        P.append('<p class="sub">No claim is held.</p>')
    if unknown:
        P.append(f'<p class="free"><b>UNKNOWN (no private store):</b> {esc(", ".join(sorted(unknown)))}</p>')
    if free:
        P.append(f'<p class="free">free: {esc(", ".join(sorted(free)))}</p>')

    # ── uncommitted work ────────────────────────────────────────────────────
    P.append("<h2>Uncommitted in the tree</h2>")
    ch = B.get("changes") or {}
    if not ch:
        P.append('<p class="sub">Nothing uncommitted in either repository.</p>')
    else:
        P.append('<div class="tablewrap"><table><thead><tr><th>claim</th><th>held by</th>'
                 '<th>files</th></tr></thead><tbody>')
        for k, v in sorted(ch.items()):
            c = claims.get(k)
            who = ("holder UNKNOWN" if c == "UNKNOWN" else
                   esc(c.get("chat")) if isinstance(c, dict) and c.get("chat") else
                   '<span class="pill warn">unclaimed</span>' if k in claims else "shared")
            P.append(f'<tr><td class="mono">{esc(k)}</td><td>{who}</td><td class="mono">{len(v)}'
                     + "".join(f"<br>{esc(p)}" for p in v[:6])
                     + (f"<br>… {len(v) - 6} more" if len(v) > 6 else "") + "</td></tr>")
        P.append("</tbody></table></div>")

    # ── ships ───────────────────────────────────────────────────────────────
    s = B.get("ship") or {}
    P.append("<h2>Ships</h2>")
    P.append(f'<div class="card"><h3>last request</h3><div class="big">{esc(s.get("id") or "none")}</div>'
             f'<div class="meta">{esc(s.get("state"))} {esc(s.get("ship_line") or s.get("verdict") or "")}<br>'
             + ("a request is queued" if B.get("ship_request_waiting") else "nothing queued")
             + "</div></div>")
    if B.get("held_back"):
        P.append('<h2>Held back by a ship and not put back</h2><ul>')
        for h in B["held_back"]:
            P.append(f'<li class="mono">{esc(h["id"])} (chat {esc(h.get("chat"))}): '
                     f'{len(h["left"])} item(s) — <code>python3 tools/ship_scope.py restore --id '
                     f'{esc(h["id"])}</code></li>')
        P.append("</ul>")

    P.append(f'<footer>A claim is taken with <code>python3 tools/doc_lock.py take &lt;claim&gt; '
             f'--chat "&lt;this chat&gt;" --note "..."</code> and released the same way once the ship '
             f'has reached GitHub. Staleness is measured from last activity, not from when the claim '
             f'was taken: flagged after {esc(B.get("stale_hours"))} h, loudly after '
             f'{esc(B.get("abandoned_hours"))} h. Flagging never releases anything — '
             f'<code>release --force --by NAME</code> is the only override, and every one is logged to '
             f'working/claim_overrides.csv. D-300.</footer></div>')
    return "\n".join(P)


def owed() -> str | None:
    """The marker doc_lock leaves on take/release, if the page has not been republished since."""
    if not OWED.exists():
        return None
    try:
        when = OWED.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    if not when:        # an emptied marker (the bridge cannot unlink) means nothing is owed
        return None
    try:
        st = json.loads(STATE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return when
    return None if (st.get("published_at") or "") >= when.split("  ")[0] else when


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="exit 1 if a republish is owed")
    ap.add_argument("--published", default=None, help="record the artifact URL just published")
    ap.add_argument("--url", action="store_true", help="print the artifact URL, if known")
    a = ap.parse_args()

    if a.url:
        try:
            print(json.loads(STATE.read_text(encoding="utf-8")).get("url") or "")
        except (OSError, ValueError):
            print("")
        return 0

    if a.published:
        STATE.parent.mkdir(parents=True, exist_ok=True)
        STATE.write_text(json.dumps({"url": a.published, "published_at": _now(),
                                     "by": os.environ.get("NRG_CHAT") or "?"}, indent=2) + "\n",
                         encoding="utf-8")
        try:
            OWED.unlink(missing_ok=True)
        except OSError:
            # The bridge mount refuses unlink (CLAUDE.md 4), so emptying is the fallback that works -
            # but ONLY for a marker that is really there. missing_ok above is what keeps this branch
            # from CREATING an empty marker when nothing was owed, which it did on 2026-11-04.
            try:
                OWED.write_text("", encoding="utf-8")
            except OSError:
                pass
        print(f"  recorded: {a.published}")
        return 0

    if a.check:
        w = owed()
        try:
            url = json.loads(STATE.read_text(encoding="utf-8")).get("url")
        except (OSError, ValueError):
            url = None
        if w:
            print(f"  STALE  the board artifact is behind: {w}")
            print(f"  Republish {OUT.relative_to(REPO)} to {url or 'a new private artifact'}"
                  f" (Artifact tool, same URL), then:")
            print(f"      python3 tools/board_artifact.py --published {url or '<URL>'}")
            return 1
        print(f"  OK  the board artifact is current" + (f" ({url})" if url else " (never published)"))
        return 0

    import work_board
    B = work_board.collect(do_probe=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(render_html(B), encoding="utf-8")
    print(f"  wrote {OUT}  ({len(OUT.read_text(encoding='utf-8')):,} bytes)")
    print(f"  publish it as a PRIVATE artifact, then: python3 tools/board_artifact.py --published <URL>")
    return 0


if __name__ == "__main__":
    sys.exit(main())
