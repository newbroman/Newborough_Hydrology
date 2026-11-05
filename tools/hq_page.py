#!/usr/bin/env python3
"""hq_page — NRG HQ: the landing page for every chat and every piece of code work (D-301).

Martin, 2026-11-05 02:59: "A project management page, a bit like the one I designed for Music of the
Spheres. A landing page for all chats and code work about the project, and it uses an agent to
monitor all the chats to make sure they are behaving and following the rules."

THIS SCRIPT CARRIES NO DATA. That is the whole privacy design.

  The board page (tools/board_artifact.py) bakes the claims into the HTML, so its output must stay
  in gitignored scratch/. This page does not: it renders from the artifact's `db` at view time, so
  the HTML is a shell with no chat name, note or claim in it, and the only private things are the
  db itself (Martin's, private to him) and the recorded URL in working/.hq_artifact.json.

  It also means the page is live. A claim taken at midnight shows at midnight without anyone
  republishing - which is what the board page could not do, and why D7 folds it in here.

ONLY A SESSION CAN WRITE THE DB

  ArtifactData belongs to a conversation, not to a script. So the division is:
    tools/hq_snapshot.py  gathers and computes, and emits the batch of writes
    the session          writes that batch, and publishes this page when the SHELL changes
    this page            renders whatever is in the db
  A take or release leaves working/.hq_publish_owed, and `--check` tells the next session.

  The shell changes rarely; the data changes daily. So most days nothing is republished at all.

THE DB LAYOUT (spec §5, with two deliberate departures)

  meta/snapshot   when, store state, digest, mode, host, history depth
  meta/links      hq, project, both repositories, proof page
  meta/owed       things behind where they should be
  board/current   the work board snapshot (work_board.collect)
  tasks/current   the task register snapshot, each task carrying its 7-run trend
  gate_runs/<at>  one per run: verdict, per-section verdicts, advisory counts, newly red
  jobs/<id>       the job queue, each job with its conditions and which hold
  chats/<id>      the chat register
  findings/<id>   the HQ agent's findings (phase 3)
  dates/<id>      Martin's own dates

  Departure 1: `tasks` and `board` are ONE DOC each, not a collection of 134. The page shows the
  latest snapshot, and 134 document writes a day to say the same thing costs more than it buys.
  Departure 2: there is no `task_history` collection. The history lives in the private repository
  (working/hq_history.json), the trend is computed from it, and each task carries its answer - so
  the db holds the conclusion rather than a second copy of the record.

Usage
  python3 tools/hq_page.py                      # render to scratch/hq/index.html
  python3 tools/hq_page.py --check              # is a republish owed? (exit 1 if so)
  python3 tools/hq_page.py --published URL      # record the publish, clear the marker
  python3 tools/hq_page.py --url
"""
from __future__ import annotations

__version__ = "1.0.1"  # Hollingham (2026) — 2026-11-05 (D-301, spec NRG_handover_HQ_page_2026-11-05,
#   D1-D9 signed off). First issue: the nine bands, the start console, the job queue band, and a shell that
#   carries no data because it renders from the db.
# 1.0.1  # Hollingham (2026) — 2026-11-05. Martin, 11:59: the page "doesn't render nicely on the mobile
#   claude app — jobs waiting doesn't wrap", and "it says the L14 still has a lock; the L14 isn't editing".
#   (1) Long ids, brief paths and job conditions now wrap on a phone: .cond's text column is minmax(0,1fr)
#   (a bare 1fr has a min-content floor, so one long path widened the column past the screen), list items
#   and flex rows get min-width 0 and overflow-wrap anywhere. (2) The machine-lock card says what the lock
#   means — the machine whose copy of the ODTs is newer than Drive, which since D-299 a bridge chat takes
#   under the L14's name — rather than reading as a laptop in use. (3) The 'fired' job pill had no
#   style; it takes the amber of 'ready'. Rendering only; no data change.

import argparse
import datetime
import json
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parents[1]
REPO = pathlib.Path(os.environ.get("NRG_REPO_ROOT") or HERE).resolve()
sys.path.insert(0, str(HERE / "tools"))

OUT = REPO / "scratch/hq/index.html"              # gitignored
STATE = REPO / "working/.hq_artifact.json"        # private half
OWED = REPO / "working/.hq_publish_owed"

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
         'family=Spectral:wght@500;600&family=IBM+Plex+Sans:wght@400;500;600&'
         'family=IBM+Plex+Mono:wght@400;500&display=swap">')

# The palette is the ground this project measures: wet sand and marram over a slate ink, with a
# saltmarsh accent. Semantic colour (ok / warn / crit) is kept off the accent, so a flag never
# reads as decoration. Both themes, every token defined on bare :root first.
CSS = """
<style>
/* Layout: a wide column of labelled bands - what needs you, then the work, then the record.
   Two columns above 900px where a band has a natural sidebar; one column on a phone. */
:root {
  --bg: #f4f1e8; --panel: #fbf9f3; --panel-2: #ece7d8; --ink: #1f2420; --ink-2: #5c6358;
  --rule: #d8d1bf; --accent: #2d5c4e; --accent-ink: #f7fbf8; --accent-soft: #dbe7e0;
  --ok: #37704a; --ok-bg: #e2eee4; --warn: #8d5d12; --warn-bg: #f6e9d2;
  --crit: #9d2f23; --crit-bg: #f6e0dc; --quiet-bg: #e8e4d7;
  --display: "Spectral", Georgia, "Times New Roman", serif;
  --body: "IBM Plex Sans", ui-sans-serif, system-ui, sans-serif;
  --mono: "IBM Plex Mono", ui-monospace, "SFMono-Regular", Menlo, monospace;
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --bg: #12150f; --panel: #1b1f16; --panel-2: #242920; --ink: #e9e7dc; --ink-2: #a5a997;
  --rule: #343a2a; --accent: #7cb7a3; --accent-ink: #0f1510; --accent-soft: #23312b;
  --ok: #7cc08d; --ok-bg: #16281c; --warn: #d6a44f; --warn-bg: #2b2113;
  --crit: #e2887c; --crit-bg: #2e1815; --quiet-bg: #1f2319;
  color-scheme: dark; } }
:root[data-theme="dark"] {
  --bg: #12150f; --panel: #1b1f16; --panel-2: #242920; --ink: #e9e7dc; --ink-2: #a5a997;
  --rule: #343a2a; --accent: #7cb7a3; --accent-ink: #0f1510; --accent-soft: #23312b;
  --ok: #7cc08d; --ok-bg: #16281c; --warn: #d6a44f; --warn-bg: #2b2113;
  --crit: #e2887c; --crit-bg: #2e1815; --quiet-bg: #1f2319;
  color-scheme: dark; }
* { box-sizing: border-box; }
body { background: var(--bg); color: var(--ink); font: 400 16px/1.55 var(--body);
  padding-block: 22px 64px;
  padding-left: max(16px, env(safe-area-inset-left, 0px));
  padding-right: max(16px, env(safe-area-inset-right, 0px)); }
.wrap { max-width: 1060px; margin: 0 auto; display: grid; gap: 20px; }
h1, h2 { font-family: var(--display); font-weight: 600; margin: 0; text-wrap: balance; }
h1 { font-size: clamp(2rem, 1.5rem + 2.2vw, 3rem); line-height: 1.04; letter-spacing: -0.01em; }
h2 { font-size: 1.32rem; }
h3 { margin: 0; font: 600 0.74rem var(--body); text-transform: uppercase; letter-spacing: 0.09em;
  color: var(--ink-2); }
.eyebrow { font: 500 0.76rem var(--body); letter-spacing: 0.13em; text-transform: uppercase;
  color: var(--accent); }
.sub { color: var(--ink-2); margin: 0.3rem 0 0; max-width: 64ch; }
header { display: flex; justify-content: space-between; align-items: flex-end; gap: 16px;
  flex-wrap: wrap; }
.links { display: flex; gap: 8px; flex-wrap: wrap; }
a.btn, button { font: 500 0.94rem var(--body); color: var(--ink); background: var(--panel);
  border: 1px solid var(--rule); border-radius: 8px; padding: 8px 14px; text-decoration: none;
  cursor: pointer; display: inline-flex; align-items: center; gap: 6px; }
a.btn:hover, button:hover { border-color: var(--accent); }
.primary { background: var(--accent) !important; color: var(--accent-ink) !important;
  border-color: var(--accent) !important; font-weight: 600 !important; }
:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
section { background: var(--panel); border: 1px solid var(--rule); border-radius: 12px;
  padding: 17px; display: grid; gap: 13px; min-width: 0; }
section.alert { border-color: var(--crit); border-left-width: 4px; }
.two { display: grid; grid-template-columns: minmax(0, 1.9fr) minmax(0, 1fr); gap: 20px;
  align-items: start; }
@media (max-width: 900px) { .two { grid-template-columns: 1fr; } }
.col { display: grid; gap: 20px; min-width: 0; }
.digest { font: 500 0.92rem var(--mono); background: var(--panel-2); border-left: 3px solid var(--accent);
  padding: 0.65rem 0.8rem; border-radius: 0 5px 5px 0; overflow-wrap: anywhere; }
.banner { background: var(--crit-bg); color: var(--crit); padding: 11px 14px; border-radius: 8px;
  font-size: 0.93rem; }
.banner code { font-family: var(--mono); display: block; margin-top: 4px; }
.cards { display: grid; gap: 11px; grid-template-columns: repeat(auto-fit, minmax(13rem, 1fr)); }
.card { background: var(--panel-2); border: 1px solid var(--rule); border-radius: 9px;
  padding: 11px 13px; min-width: 0; }
.card .big { font: 500 1rem var(--mono); margin-top: 5px; font-variant-numeric: tabular-nums;
  overflow-wrap: anywhere; }
.card .meta { color: var(--ink-2); font-size: 0.8rem; margin-top: 5px; overflow-wrap: anywhere; }
.pill { font: 500 0.72rem var(--mono); padding: 2px 8px; border-radius: 99px; white-space: nowrap; }
.p-ok { background: var(--ok-bg); color: var(--ok); }
.p-warn, .p-active, .p-ready, .p-fired { background: var(--warn-bg); color: var(--warn); }
.p-crit, .p-broken { background: var(--crit-bg); color: var(--crit); }
.p-quiet, .p-parked, .p-starting, .p-queued, .p-done, .p-skip { background: var(--quiet-bg); color: var(--ink-2); }
table { border-collapse: collapse; width: 100%; font-size: 0.88rem; }
.tablewrap { overflow-x: auto; }
th { text-align: left; font: 600 0.69rem var(--body); text-transform: uppercase;
  letter-spacing: 0.08em; color: var(--ink-2); border-bottom: 1px solid var(--rule);
  padding: 4px 10px 4px 0; white-space: nowrap; }
td { padding: 7px 10px 7px 0; border-bottom: 1px solid var(--rule); vertical-align: top;
  min-width: 0; }
td.mono, .mono { font-family: var(--mono); font-variant-numeric: tabular-nums; }
.muted { color: var(--ink-2); font-size: 0.86rem; }
.empty { color: var(--ink-2); border: 1px dashed var(--rule); border-radius: 9px; padding: 15px;
  text-align: center; font-size: 0.92rem; }
ul.plain { list-style: none; margin: 0; padding: 0; display: grid; gap: 9px; }
ul.plain li { display: grid; gap: 2px; min-width: 0; overflow-wrap: anywhere; }
/* 1.0.1: long ids, paths and conditions wrap on a phone instead of pushing the column wide */
.row { min-width: 0; } .row > * { min-width: 0; overflow-wrap: anywhere; }
.mono, .muted { overflow-wrap: anywhere; }
@media (max-width: 520px) { .tablewrap td, .tablewrap th { font-size: 0.82rem; }
  a.btn { padding: 7px 11px; } }
ol.how { margin: 0; padding-left: 1.15em; color: var(--ink-2); font-size: 0.92rem;
  display: grid; gap: 4px; }
label.f { display: grid; gap: 4px; font: 500 0.74rem var(--body); letter-spacing: 0.08em;
  text-transform: uppercase; color: var(--ink-2); }
textarea, input, select { font: 400 1rem var(--body); color: var(--ink); background: var(--bg);
  border: 1px solid var(--rule); border-radius: 8px; padding: 9px 10px; width: 100%;
  text-transform: none; letter-spacing: 0; }
textarea { min-height: 80px; resize: vertical; }
.chips { display: flex; flex-wrap: wrap; gap: 6px; }
.chips button { padding: 5px 11px; border-radius: 99px; font-size: 0.87rem; }
.chips button[aria-pressed="true"] { background: var(--accent-soft); border-color: var(--accent); }
.row { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
.filters { display: flex; gap: 6px; }
.filters button { padding: 4px 10px; font-size: 0.84rem; }
.filters button[aria-pressed="true"] { border-color: var(--accent); color: var(--accent); }
.toolbar { display: flex; justify-content: space-between; align-items: center; gap: 10px;
  flex-wrap: wrap; }
.cond { font: 400 0.82rem var(--mono); display: grid; grid-template-columns: 1.6rem minmax(0, 1fr); gap: 2px 6px; }
.cond span { min-width: 0; overflow-wrap: anywhere; }
.cond .y { color: var(--ok); } .cond .n { color: var(--warn); }
.trend-closer { color: var(--ok); } .trend-further { color: var(--crit); }
.trend-unchanged, .trend-new, .trend-changed { color: var(--ink-2); }
footer { border-top: 1px solid var(--rule); padding-top: 12px; color: var(--ink-2);
  font-size: 0.8rem; }
footer code { font-family: var(--mono); }
a { color: var(--accent); }
@media (prefers-reduced-motion: reduce) { * { transition: none !important; } }
</style>
"""

BODY = """
<div class="wrap">
  <header>
    <div>
      <div class="eyebrow">Newborough Warren &middot; dipwell hydrology</div>
      <h1>NRG HQ</h1>
      <p class="sub">Start a piece of work, see every chat on the project and what it holds, and
        read the state of the tree: the board, the tasks, the gate and the queue.</p>
    </div>
    <nav class="links" aria-label="Places">
      <a class="btn primary" id="lnk-hq" href="#" target="_blank" rel="noopener">Talk to HQ</a>
      <a class="btn" id="lnk-project" href="#" target="_blank" rel="noopener">Project</a>
      <a class="btn" id="lnk-public" href="https://github.com/newbroman/Newborough_Hydrology"
         target="_blank" rel="noopener">Public repo</a>
      <a class="btn" id="lnk-private" href="https://github.com/newbroman/Newborough_Hydrology_working"
         target="_blank" rel="noopener">Private repo</a>
      <a class="btn" id="lnk-proof" href="#" target="_blank" rel="noopener">Proof page</a>
    </nav>
  </header>

  <div id="banner" class="banner" hidden></div>
  <p class="digest" id="digest">Loading the board&hellip;</p>

  <section class="alert" id="needsSec" aria-labelledby="needsH" hidden>
    <h2 id="needsH">Needs you</h2>
    <div id="needs"></div>
  </section>

  <div class="two">
    <div class="col">
      <section aria-labelledby="startH">
        <h2 id="startH">Start a new chat</h2>
        <form id="startForm">
          <div>
            <div class="muted" style="margin-bottom:6px">What kind of work?</div>
            <div class="chips" id="kinds" role="group" aria-label="Kind of work"></div>
          </div>
          <label class="f" for="what" style="margin-top:11px">What do you want it to do?
            <textarea id="what" placeholder="For example: build Script 55 from the water-balance spec, or read Paper M v1_42 for the journal's house style"></textarea>
          </label>
          <div class="row" style="margin-top:11px">
            <button class="primary" type="submit">Copy brief and open the project</button>
            <span class="muted">Paste it into a new chat. The brief tells it to register first.</span>
          </div>
          <div id="startMsg" class="muted" hidden></div>
          <label class="f" for="brief" id="briefLab" hidden style="margin-top:9px">The brief (copying did not work &mdash; select it here)
            <textarea id="brief" readonly style="min-height:150px"></textarea>
          </label>
        </form>
      </section>

      <section aria-labelledby="jobsH">
        <h2 id="jobsH">Jobs waiting to fire</h2>
        <div id="jobs"><div class="empty">Loading&hellip;</div></div>
        <p class="muted">A job fires when every condition holds &mdash; on the release that frees
          its claim, or at HQ&rsquo;s next pass. Nothing fires while HQ cannot read the private
          repository.</p>
      </section>

      <section aria-labelledby="chatsH">
        <div class="toolbar">
          <h2 id="chatsH">Chats on the project</h2>
          <div class="filters" id="filters">
            <button data-f="active" aria-pressed="true">Active</button>
            <button data-f="done" aria-pressed="false">Done</button>
            <button data-f="all" aria-pressed="false">All</button>
          </div>
        </div>
        <div id="chats"><div class="empty">Loading&hellip;</div></div>
      </section>

      <section aria-labelledby="tasksH">
        <div class="toolbar">
          <h2 id="tasksH">Tasks</h2>
          <span class="muted" id="taskHead"></span>
        </div>
        <div id="tasks"><div class="empty">Loading&hellip;</div></div>
      </section>
    </div>

    <div class="col">
      <section aria-labelledby="boardH">
        <h2 id="boardH">Work board</h2>
        <div id="board"><div class="empty">Loading&hellip;</div></div>
      </section>

      <section aria-labelledby="gateH">
        <h2 id="gateH">Gate</h2>
        <div id="gate"><div class="empty">Loading&hellip;</div></div>
      </section>

      <section aria-labelledby="owedH">
        <h2 id="owedH">Coming up and owed</h2>
        <div id="owed"><div class="empty">Loading&hellip;</div></div>
      </section>

      <section aria-labelledby="howH">
        <h2 id="howH">How it works</h2>
        <ol class="how">
          <li>Start every new chat from this page, so it arrives knowing the rules.</li>
          <li>Each chat registers itself before its first claim or commit, and claims what it
            works on. A seeded row is marked: it is not evidence the chat read the rule.</li>
          <li>HQ audits after the fact &mdash; from commits, handovers, the decision log, claims
            and the gate &mdash; and reports. It releases nothing and edits nothing.</li>
          <li>Anything it cannot see, it says it cannot see. It never reports all clear for a
            repository it does not hold.</li>
        </ol>
      </section>
    </div>
  </div>

  <footer>
    <span id="foot">NRG HQ renders live from its own store; nothing here is in the public
      repository.</span>
  </footer>
</div>
"""

# The five kinds of work the console offers (spec §4.2, D2 signed off). Each brief is
# SELF-CONTAINED: the chat that receives it has no memory of this page or of Martin's request.
KIND_BRIEFS = {
    "Pipeline / analysis": ("pipeline", "pipeline", """Setup, in this order:
1. add_repo newbroman/Newborough_Hydrology          access=push
   add_repo newbroman/Newborough_Hydrology_working  access=push
2. Run tools/cloud_setup.sh as notes/reference/SESSION_MODES.md describes, then the D-143 start:
   read working/HANDOVER_BOOTSTRAP.md and run python3 tools/session_handover.py.
3. Register this chat: python3 tools/chat_register.py register --chat "<a short name>" \\
     --kind pipeline --claim pipeline --purpose "<one line>"
4. python3 tools/work_board.py, then take the `pipeline` claim ONLY."""),
    "Document edit": ("document", "doc:<family>", """Setup, in this order:
1. add_repo newbroman/Newborough_Hydrology          access=push
   add_repo newbroman/Newborough_Hydrology_working  access=push
2. Run tools/cloud_setup.sh, then the D-143 start (working/HANDOVER_BOOTSTRAP.md,
   python3 tools/session_handover.py).
3. Register this chat: python3 tools/chat_register.py register --chat "<a short name>" \\
     --kind document --claim doc:<family> --purpose "<one line>"
4. python3 tools/work_board.py FIRST, and take only the doc: family you are editing.
ODTs are edited only through tools/odt_edit.py, never odfpy, and a document is versioned: edit
Doc_v1_9_46.odt and WRITE Doc_v1_9_47.odt. Read the passage back from the saved file."""),
    "Tools": ("tools", "tools", """Setup, in this order:
1. add_repo newbroman/Newborough_Hydrology          access=push
   add_repo newbroman/Newborough_Hydrology_working  access=push
2. Run tools/cloud_setup.sh, then the D-143 start.
3. Register this chat: python3 tools/chat_register.py register --chat "<a short name>" \\
     --kind tools --claim tools --purpose "<one line>"
4. python3 tools/work_board.py, then take the `tools` claim ONLY.
Test in throwaway trees through NRG_REPO_ROOT, never against the real lock or registers."""),
    "Read-only / a question": ("readonly", "", """Setup:
1. add_repo newbroman/Newborough_Hydrology          access=push
   add_repo newbroman/Newborough_Hydrology_working  access=push
   (both, so you can see what other chats hold; without the private one every claim reads
   UNKNOWN, which is not the same as free - D-300.)
2. Run tools/cloud_setup.sh, then the D-143 start.
3. Register this chat: python3 tools/chat_register.py register --chat "<a short name>" \\
     --kind readonly --purpose "<one line>"
TAKE NO CLAIM AND COMMIT NOTHING. Read, measure, and report. If the answer turns out to need a
change, say so and stop: that is a different chat, with a claim."""),
    "Fieldwork / data in": ("fieldwork", "pipeline", """Setup, in this order:
1. add_repo newbroman/Newborough_Hydrology          access=push
   add_repo newbroman/Newborough_Hydrology_working  access=push
2. Run tools/cloud_setup.sh, then the D-143 start.
3. Register this chat: python3 tools/chat_register.py register --chat "<a short name>" \\
     --kind fieldwork --claim pipeline --purpose "<one line>"
4. Take `pipeline` before writing anything under data/ or outputs/.
New readings go in as data, never as an edited output. Third-party data that is not in either
repository goes in the PRIVATE one (CLAUDE.md 4g), and the pipeline run that uses it comes after."""),
}

TAIL = """
<script>
const $ = s => document.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const KINDS = __KINDS__;
const BRIEFS = __BRIEFS__;
const RULES = __RULES__;

let kind = Object.keys(KINDS)[0], filter = 'active', db = null, user = null;
let SNAP = {}, LINKS = {}, OWED = {}, BOARD = {}, TASKS = {}, JOBS = [], CHATS = [], FIND = [], GATES = [];
try { const k = localStorage.getItem('nrg.kind'); if (KINDS[k]) kind = k;
      const f = localStorage.getItem('nrg.filter'); if (f) filter = f; } catch (e) {}

function banner(m, code) {
  const b = $('#banner');
  b.innerHTML = m ? esc(m) + (code ? '<code>' + esc(code) + '</code>' : '') : '';
  b.hidden = !m;
}
function pill(txt, cls) { return '<span class="pill p-' + (cls || 'quiet') + '">' + esc(txt) + '</span>'; }
function fmt(ts) {
  if (!ts) return '';
  const d = new Date(ts);
  return isNaN(d) ? String(ts) : d.toLocaleString('en-GB',
    { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });
}

/* ── the store line comes first, because what the rest is worth depends on it (D-300) ───── */
function renderDigest() {
  const s = SNAP || {};
  if (s.store === 'ABSENT') {
    banner('HQ could not read the private repository when it last ran, so the claims and the queue '
         + 'below are UNKNOWN, not free, and nothing fired. ' + (s.storeWhy || ''),
           'add_repo newbroman/Newborough_Hydrology_working  access=push');
  } else if (!s.generated) {
    banner('No snapshot yet. Run the HQ pass in a session with both repositories attached.');
  } else { banner(''); }
  $('#digest').textContent = (s.digest || 'No board snapshot yet.')
    + (s.generated ? '   ·   as of ' + fmt(s.generated) + (s.mode ? ' (' + s.mode + ')' : '') : '');
  $('#foot').textContent = 'NRG HQ renders live from its own store; nothing here is in the public '
    + 'repository.' + (s.historyRuns ? '  ' + s.historyRuns + ' run(s) of history.' : '');
}

/* ── needs you ───────────────────────────────────────────────────────────────────────────── */
function renderNeeds() {
  const rows = FIND.filter(f => f.serious !== false);
  const red = (SNAP.gateNewlyRed || []);
  const has = rows.length || red.length;
  $('#needsSec').hidden = !has;
  if (!has) return;
  let h = '';
  if (red.length) h += '<div class="card"><h3>newly red</h3><div class="big">' + esc(red.join(', '))
    + '</div><div class="meta">these gate sections passed on the previous run</div></div>';
  h += '<ul class="plain">' + rows.map(f =>
    '<li><strong>' + esc(f.title || f.rule || 'finding') + '</strong>'
    + (f.chat ? ' ' + pill(f.chat, 'warn') : '')
    + '<span class="muted">' + esc(f.detail || '') + '</span>'
    + (f.evidence ? '<span class="mono muted">' + esc(f.evidence) + '</span>' : '')
    + '</li>').join('') + '</ul>';
  $('#needs').innerHTML = h;
}

/* ── the job queue, condition by condition ───────────────────────────────────────────────── */
function renderJobs() {
  if (!JOBS.length) { $('#jobs').innerHTML = '<div class="empty">The queue is empty.</div>'; return; }
  const order = { ready: 0, queued: 1, fired: 2, held: 3, done: 4 };
  $('#jobs').innerHTML = '<ul class="plain">' + [...JOBS]
    .sort((a, b) => (order[a.status] ?? 9) - (order[b.status] ?? 9) || String(a.id).localeCompare(b.id))
    .map(j => {
      const ready = j.allHold && (j.status === 'queued' || j.status === 'ready');
      return '<li><div class="row"><span class="mono">' + esc(j.id) + '</span> '
        + pill(ready ? 'ready' : (j.status || '?'), ready ? 'ready' : (j.status || 'quiet'))
        + ' <strong>' + esc(j.title || '') + '</strong></div>'
        + '<span class="muted mono">' + esc(j.claim || 'no claim') + ' · ' + esc(j.target || '')
        + ' · ' + esc(j.brief || '') + '</span>'
        + (j.conditions && j.conditions.length ? '<div class="cond">' + j.conditions.map(c =>
            '<span class="' + (c.holds ? 'y' : 'n') + '">' + (c.holds ? 'yes' : 'no') + '</span>'
            + '<span>' + esc(c.cond) + ' &mdash; ' + esc(c.why) + '</span>').join('') + '</div>' : '')
        + (j.blockedBy ? '<span class="muted">blocked: ' + esc(j.blockedBy)
            + ' is active for the same claim</span>' : '')
        + (j.firedAt ? '<span class="muted">fired ' + fmt(j.firedAt) + ' by ' + esc(j.firedBy || '')
            + '</span>' : '')
        + '</li>'; }).join('') + '</ul>';
}

/* ── chats ───────────────────────────────────────────────────────────────────────────────── */
function renderChats() {
  let rows = [...CHATS];
  if (filter === 'active') rows = rows.filter(r => r.status !== 'done');
  if (filter === 'done') rows = rows.filter(r => r.status === 'done');
  rows.sort((a, b) => String(b.touched || '').localeCompare(String(a.touched || '')));
  if (!rows.length) {
    $('#chats').innerHTML = '<div class="empty">' + (CHATS.length ? 'No chats in this view.'
      : 'No chats registered yet.') + '</div>';
    return;
  }
  $('#chats').innerHTML = '<div class="tablewrap"><table><thead><tr><th>chat</th><th>kind</th>'
    + '<th>claim</th><th>where</th><th>last seen</th></tr></thead><tbody>'
    + rows.map(r => '<tr><td><strong>' + (r.link
          ? '<a href="' + esc(r.link) + '" target="_blank" rel="noopener">' + esc(r.chat) + '</a>'
          : esc(r.chat)) + '</strong> ' + pill(r.status || '?', r.status || 'quiet')
        + (r.seeded ? ' <span class="muted">seeded</span>' : '')
        + '<div class="muted">' + esc(r.purpose || '')
        + (r.outcome ? ' &rarr; ' + esc(r.outcome) : '') + '</div></td>'
        + '<td>' + esc(r.kind || '') + '</td><td class="mono">' + esc(r.claim || '-') + '</td>'
        + '<td>' + esc(r.mode || '') + '</td><td class="mono">' + fmt(r.touched) + '</td></tr>').join('')
    + '</tbody></table></div>';
}

/* ── tasks: open first, each with what it wants and where it is going (D6) ──────────────── */
function renderTasks() {
  const t = TASKS || {};
  const all = t.tasks || [];
  if (!all.length) { $('#tasks').innerHTML = '<div class="empty">No task snapshot yet.</div>'; return; }
  const c = t.counts || {};
  $('#taskHead').textContent = (c.total || 0) + ' tasks · ' + (c.open || 0) + ' open · '
    + (c.done || 0) + ' done' + (c.broken ? ' · ' + c.broken + ' BROKEN' : '')
    + (c.skipped ? ' · ' + c.skipped + ' skipped' : '');
  const by = s => all.filter(x => x.status === s);
  const line = x => '<tr><td class="mono">' + esc(x.id) + '</td><td><strong>' + esc(x.title || '')
    + '</strong>' + (x.implements ? '<div class="muted">' + esc(x.implements) + '</div>' : '')
    + '</td><td class="mono">' + esc(x.got || '') + (x.want !== undefined && x.want !== ''
        ? ' <span class="muted">want ' + esc(x.want) + '</span>' : '') + '</td>'
    + '<td class="mono">' + esc(x.claim || '-') + '</td>'
    + '<td class="trend-' + esc(x.trend || 'new') + '">' + esc(x.trend || '') + '</td>'
    + '<td class="mono muted">' + esc(x.opened || '') + '</td></tr>';
  let h = '';
  for (const [label, rows, cls] of [['broken', by('BROKEN'), 'broken'], ['open', by('OPEN'), 'warn'],
                                    ['skipped', by('SKIP'), 'skip']]) {
    if (!rows.length) continue;
    h += '<h3 style="margin-top:9px">' + rows.length + ' ' + label + '</h3>'
      + '<div class="tablewrap"><table><thead><tr><th>id</th><th>task</th><th>now</th>'
      + '<th>claim</th><th>trend</th><th>opened</th></tr></thead><tbody>'
      + rows.sort((a, b) => String(a.id).localeCompare(b.id)).map(line).join('')
      + '</tbody></table></div>';
  }
  const done = by('DONE');
  if (done.length) h += '<details><summary class="muted">' + done.length
    + ' done (kept as regression guards)</summary><div class="tablewrap"><table><tbody>'
    + done.sort((a, b) => String(a.id).localeCompare(b.id)).map(x =>
        '<tr><td class="mono">' + esc(x.id) + '</td><td>' + esc(x.title || '') + '</td></tr>').join('')
    + '</tbody></table></div></details>';
  $('#tasks').innerHTML = h || '<div class="empty">Nothing outstanding.</div>';
}

/* ── the work board (D7: this replaces the separate board page) ──────────────────────────── */
function renderBoard() {
  const b = BOARD || {};
  if (!b.generated && !b.claims) { $('#board').innerHTML = '<div class="empty">No board snapshot yet.</div>'; return; }
  let h = '<div class="cards">' + (b.repos || []).map(r =>
    '<div class="card"><h3>' + esc(r.name) + ' ' + (r.present
        ? pill(r.behind || r.ahead ? (r.ahead || 0) + '/' + (r.behind || 0) : 'level',
               r.behind || r.ahead ? 'warn' : 'ok')
        : pill('absent', 'crit')) + '</h3>'
    + '<div class="big">' + esc(r.head || '?') + ' on ' + esc(r.branch || '?') + '</div>'
    + '<div class="meta">' + esc(r.holds || '')
    + (r.origin_moved ? '<br>origin has moved &mdash; fetch' : '')
    + (r.last_fetch ? '<br>fetched ' + esc(r.last_fetch) : '') + '</div></div>').join('') + '</div>';

  const ml = b.machine_lock || {};
  // 1.0.1: the holder is a MACHINE, and since D-299 a chat working through the bridge takes it under
  // the L14's name - so "held by the L14" reads as "the laptop is editing" when it means "the L14's copy
  // of the ODTs is the current one". Say what it means, and who took it.
  h += '<div class="card"><h3>documents &mdash; machine lock</h3><div class="big">'
    + esc(ml.unknown ? 'UNKNOWN' : (ml.holder ? 'current copy: ' + ml.holder : 'free')) + '</div><div class="meta">'
    + esc(ml.unknown ? 'the lock cannot be read from the session that ran HQ'
          : (ml.holder ? 'since ' + fmt(ml.since) + (ml.note ? ' — ' + ml.note : '')
             : 'take it before editing any ODT'))
    + (ml.holder && !ml.unknown ? '<br>This names the machine whose copy of the ODTs is the working copy, '
        + 'not a machine in use: a chat editing documents through the bridge takes it under the L14’s '
        + 'name (D-299). It clears when that chat archives to Drive and releases it.' : '')
    + '</div></div>';

  const cl = b.claims || {};
  const held = Object.entries(cl).filter(([, v]) => v && v !== 'UNKNOWN');
  const unk = Object.keys(cl).filter(k => cl[k] === 'UNKNOWN');
  const free = Object.keys(cl).filter(k => !cl[k]);
  if (held.length) h += '<div class="tablewrap"><table><thead><tr><th>claim</th><th>chat</th>'
    + '<th>last activity</th></tr></thead><tbody>' + held.map(([k, v]) => {
      const st = (b.stale || {})[k] || {};
      return '<tr><td class="mono">' + esc(k) + '</td><td>' + esc(v.chat || '')
        + (st.flag ? ' ' + pill(st.flag, st.flag === 'ABANDONED' ? 'crit' : 'warn') : '')
        + '<div class="muted">' + esc(v.note || '') + '</div></td>'
        + '<td class="mono">' + fmt(v.touched || v.since) + '</td></tr>'; }).join('')
    + '</tbody></table></div>';
  if (unk.length) h += '<p class="muted mono">UNKNOWN (no private store): ' + esc(unk.join(', ')) + '</p>';
  if (free.length) h += '<p class="muted mono">free: ' + esc(free.join(', ')) + '</p>';

  const ch = b.changes || {};
  const keys = Object.keys(ch);
  if (keys.length) h += '<h3 style="margin-top:9px">uncommitted in the tree</h3><ul class="plain">'
    + keys.map(k => '<li><span class="mono">' + esc(k) + '</span> <span class="muted">'
        + ch[k].length + ' file(s)</span></li>').join('') + '</ul>';
  const s = b.ship || {};
  if (s.id) h += '<p class="muted">last ship request <span class="mono">' + esc(s.id) + '</span>: '
    + esc(s.state || '') + (s.ship_line ? ' &mdash; ' + esc(s.ship_line) : '') + '</p>';
  $('#board').innerHTML = h;
}

/* ── the gate, section by section ─────────────────────────────────────────────────────────── */
function renderGate() {
  const g = GATES[0];
  if (!g) { $('#gate').innerHTML = '<div class="empty">No gate run recorded yet.</div>'; return; }
  const red = (g.sections || []).filter(s => s.verdict !== 'OK');
  const newly = new Set(g.newlyRed || []);
  let h = '<div class="card"><h3>' + esc(g.verdict === 'OK' ? 'check_all: OK' : 'check_all: FAIL')
    + '</h3><div class="big">' + (g.sections || []).length + ' sections, ' + red.length
    + ' red</div><div class="meta">' + fmt(g.at) + (g.host ? ' on ' + esc(g.host) : '') + '</div></div>';
  if (red.length) h += '<ul class="plain">' + red.map(s =>
    '<li><span class="mono">' + esc(s.section) + '</span> ' + pill('FAIL', 'crit')
    + (newly.has(s.key) ? ' ' + pill('newly red', 'crit') : '') + '</li>').join('') + '</ul>';
  h += '<details><summary class="muted">every section</summary><div class="tablewrap"><table><tbody>'
    + (g.sections || []).map(s => '<tr><td class="mono">' + esc(s.section) + '</td><td>'
        + pill(s.verdict, s.verdict === 'OK' ? 'ok' : 'crit') + '</td>'
        + '<td class="mono muted">' + (s.seconds || 0) + 's</td></tr>').join('')
    + '</tbody></table></div></details>';
  const adv = g.advisory || [];
  if (adv.length) h += '<details><summary class="muted">' + adv.length
    + ' advisory count(s) &mdash; outstanding work no gate fails on</summary><ul class="plain">'
    + adv.map(a => '<li><span class="mono">' + esc(a.section) + '</span> <span class="muted">'
        + esc(a.line) + '</span></li>').join('') + '</ul></details>';
  $('#gate').innerHTML = h;
}

/* ── owed, and Martin's own dates ─────────────────────────────────────────────────────────── */
function renderOwed() {
  const rows = (OWED.items || []);
  const dates = (OWED.dates || []);
  if (!rows.length && !dates.length) {
    $('#owed').innerHTML = '<div class="empty">Nothing owed.</div>'; return;
  }
  let h = '';
  if (rows.length) h += '<ul class="plain">' + rows.map(o =>
    '<li><strong>' + esc(o.what) + '</strong>'
    + (o.do ? '<span class="muted mono">' + esc(o.do) + '</span>' : '')
    + '</li>').join('') + '</ul>';
  if (dates.length) h += '<h3 style="margin-top:9px">dates</h3><ul class="plain">'
    + dates.sort((a, b) => String(a.date).localeCompare(String(b.date))).map(d =>
        '<li><span class="mono">' + esc(d.date) + '</span> ' + esc(d.what || '') + '</li>').join('')
    + '</ul>';
  $('#owed').innerHTML = h;
}

/* ── the start console ───────────────────────────────────────────────────────────────────── */
function renderKinds() {
  $('#kinds').innerHTML = Object.keys(KINDS).map(k =>
    '<button type="button" aria-pressed="' + (k === kind) + '" data-k="' + esc(k) + '">'
    + esc(k) + '</button>').join('');
}
function renderFilters() {
  document.querySelectorAll('#filters button').forEach(b =>
    b.setAttribute('aria-pressed', String(b.dataset.f === filter)));
}
function makeBrief(what) {
  return 'New NRG chat: ' + kind + '.\\n\\n' + what.trim() + '\\n\\n' + BRIEFS[kind] + '\\n\\n' + RULES;
}

document.addEventListener('click', e => {
  const b = e.target.closest('button'); if (!b) return;
  if (b.dataset.k) { kind = b.dataset.k;
    try { localStorage.setItem('nrg.kind', kind); } catch (_) {} renderKinds(); }
  if (b.dataset.f) { filter = b.dataset.f;
    try { localStorage.setItem('nrg.filter', filter); } catch (_) {} renderFilters(); renderChats(); }
});

$('#startForm').addEventListener('submit', async e => {
  e.preventDefault();
  const what = $('#what').value;
  const msg = $('#startMsg');
  if (!what.trim()) { $('#what').focus(); msg.hidden = false;
    msg.textContent = 'Say in a line what the chat is for.'; return; }
  const brief = makeBrief(what);
  $('#brief').value = brief;
  let copied = false;
  try { await navigator.clipboard.writeText(brief); copied = true; } catch (_) {}
  $('#briefLab').hidden = copied;
  if (!copied) { $('#brief').focus(); $('#brief').select(); }
  const href = $('#lnk-project').getAttribute('href');
  if (href && href !== '#') {
    const a = document.createElement('a');
    a.href = href; a.target = '_blank'; a.rel = 'noopener';
    document.body.appendChild(a); a.click(); a.remove();
  }
  msg.hidden = false;
  msg.textContent = (copied ? 'Brief copied. Start a new chat in the project and paste it.'
    : 'Copy the brief below, then start a new chat in the project and paste it.')
    + (href && href !== '#' ? '' : ' (No project link recorded yet — HQ adds it on its next pass.)');
  if (db) {
    const id = 'starting-' + Date.now().toString(36);
    try {
      await db.collection('chats').doc(id).set({
        chat: what.trim().split('\\n')[0].slice(0, 70), kind: KINDS[kind], claim: '',
        purpose: what.trim().slice(0, 300), status: 'starting', seeded: true,
        registeredBy: 'the HQ page', touched: new Date().toISOString(),
        opened: new Date().toISOString() });
    } catch (err) {
      msg.textContent += ' (It could not be added to the index; HQ will pick it up.)';
    }
  }
});

/* ── boot ────────────────────────────────────────────────────────────────────────────────── */
renderKinds(); renderFilters();
(async () => {
  const timer = setTimeout(() => {
    if (!SNAP.generated && !BOARD.generated) {
      banner('The store did not answer. Open this page on claude.ai, signed in.');
    }
  }, 10000);
  try { db = await window.claude?.use?.('db'); } catch (e) { db = null; }
  try { user = await window.claude?.use?.('user'); } catch (e) { user = null; }
  if (!db) {
    clearTimeout(timer);
    banner('This page reads its data from its own store, which loads when it is opened on '
         + 'claude.ai while signed in.');
    for (const id of ['jobs', 'chats', 'tasks', 'board', 'gate', 'owed']) {
      $('#' + id).innerHTML = '<div class="empty">Not loaded.</div>';
    }
    return;
  }
  const sub = (ref, fn) => { try { ref.onSnapshot(s => { clearTimeout(timer); fn(s); },
      () => banner('The store stopped updating. Reload the page.')); } catch (e) {} };
  sub(db.doc('meta/snapshot'), s => { SNAP = s.exists ? s.data() : {}; renderDigest(); renderNeeds(); });
  sub(db.doc('meta/links'), s => {
    LINKS = s.exists ? s.data() : {};
    for (const [k, id] of [['hq', 'lnk-hq'], ['project', 'lnk-project'], ['proof', 'lnk-proof'],
                           ['repoPublic', 'lnk-public'], ['repoPrivate', 'lnk-private']]) {
      if (LINKS[k]) $('#' + id).href = LINKS[k];
    }
  });
  sub(db.doc('meta/owed'), s => { OWED = s.exists ? s.data() : {}; renderOwed(); });
  sub(db.doc('board/current'), s => { BOARD = s.exists ? s.data() : {}; renderBoard(); });
  sub(db.doc('tasks/current'), s => { TASKS = s.exists ? s.data() : {}; renderTasks(); });
  sub(db.collection('jobs'), s => { JOBS = s.docs.map(d => ({ id: d.id, ...d.data() })); renderJobs(); });
  sub(db.collection('chats'), s => { CHATS = s.docs.map(d => ({ id: d.id, ...d.data() })); renderChats(); });
  sub(db.collection('findings'), s => { FIND = s.docs.map(d => ({ id: d.id, ...d.data() })); renderNeeds(); });
  sub(db.collection('gate_runs'), s => {
    GATES = s.docs.map(d => ({ id: d.id, ...d.data() }))
      .sort((a, b) => String(b.at || '').localeCompare(String(a.at || '')));
    renderGate();
  });
  sub(db.collection('dates'), s => {
    OWED = Object.assign({}, OWED, { dates: s.docs.map(d => ({ id: d.id, ...d.data() })) });
    renderOwed();
  });
})();
</script>
"""

RULES = """Then, whatever the work is:
- Read working/HANDOVER_BOOTSTRAP.md and CLAUDE.md before touching anything. CLAUDE.md is the traps.
- A claim held by another chat is a refusal, not advice. Never take `--force` without saying who to.
- Run `bash tools/check_all.sh` through `tee`, quote the verdict in the commit, and use
  ${PIPESTATUS[0]} for the real exit code. A gate you did not touch going red is a stop sign.
- ASK BEFORE EVERY PUSH. A ship is TWO pushes (public and private); working/nrg_git.sh --ship does both.
- End with a dated entry at the top of working/updates/HANDOVER_NOTE.md (<=40 lines), a changelog
  delta under working/changelogs/, and `python3 tools/session_handover.py --write --check` green.
- Set your chat's status when you finish: python3 tools/chat_register.py status --chat "<name>"
  --set done --outcome "<one line>", and release your claim once the ship has reached GitHub.
- If a design question comes up that your brief does not answer, STOP, set out the question with
  your recommendation, and wait for Martin. Do not decide it."""


def render() -> str:
    kinds = {k: v[0] for k, v in KIND_BRIEFS.items()}
    briefs = {k: v[2] for k, v in KIND_BRIEFS.items()}
    js = (TAIL.replace("__KINDS__", json.dumps(kinds))
              .replace("__BRIEFS__", json.dumps(briefs))
              .replace("__RULES__", json.dumps(RULES)))
    return ("<title>NRG HQ</title>\n"
            '<meta name="claude:viewport-fit-sides" content="cover">\n'
            + FONTS + "\n" + CSS + BODY + js)


def state() -> dict:
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def owed_why() -> str:
    """An EMPTY marker is a stray file, not an owed republish. board_artifact 1.0.0 got this wrong:
    unlink() raised FileNotFoundError, the fallback wrote "", and --check then reported a republish
    was owed for ever. Measured and fixed 2026-11-04; the same shape is avoided here."""
    if not OWED.exists():
        return ""
    try:
        return OWED.read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--published", metavar="URL")
    ap.add_argument("--url", action="store_true")
    a = ap.parse_args()

    if a.url:
        print(state().get("url") or "(no HQ page recorded yet)")
        return 0

    if a.published:
        st = state()
        st.update({"url": a.published, "published_at": datetime.datetime.now(datetime.timezone.utc)
                   .strftime("%Y-%m-%dT%H:%M:%SZ"), "shell_version": __version__})
        STATE.parent.mkdir(parents=True, exist_ok=True)
        STATE.write_text(json.dumps(st, indent=2) + "\n", encoding="utf-8")
        OWED.unlink(missing_ok=True)
        print(f"  recorded: {a.published}")
        return 0

    if a.check:
        why = owed_why()
        st = state()
        if not st.get("url"):
            print("  hq_page: the HQ page has not been published yet — publish it as a PRIVATE "
                  "artifact, then: python3 tools/hq_page.py --published <URL>")
            return 0
        if st.get("shell_version") != __version__:
            print(f"  hq_page: the published shell is {st.get('shell_version')}, this is "
                  f"{__version__} — republish it ({st['url']})")
            return 1
        if why:
            print(f"  hq_page: a republish is owed — {why}")
            print(f"           {st['url']}")
            return 1
        print(f"  hq_page: OK — {st['url']} is current (shell {__version__})")
        return 0

    html_out = render()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html_out, encoding="utf-8")
    print(f"  wrote {OUT}  ({len(html_out):,} bytes)")
    st = state()
    if st.get("url"):
        print(f"  publish it to {st['url']} (capabilities db + user), then:")
    else:
        print("  publish it as a PRIVATE artifact with capabilities db + user, then:")
    print("    python3 tools/hq_page.py --published <URL>")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
