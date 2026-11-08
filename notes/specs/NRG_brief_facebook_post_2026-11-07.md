# Brief — the October 2026 Water Watch post for the Facebook water levels group

*Raised by Martin, 2026-11-07: "Write me a post for the water levels group on facebook".
Written by the `Fieldwork Oct 2026` chat, which drafted the post but could not see the group.
**This brief needs a session with BROWSER access** — see §3. No claim: the post is outreach,
it touches no claimed area, and nothing in the repository changes unless Martin asks.*

## 1. What is wanted

A Facebook post announcing the October 2026 Water Watch to
**https://www.facebook.com/groups/1164026318685018**.

**Martin posts it. Not you.** Nothing in this brief authorises posting to a group, and the
draft is his to edit. Hand him text he can paste.

## 2. The draft, as it stands

Accurate to the published issue and ready to paste. Every figure is lifted from the
newsletter rather than recalculated, which is deliberate — see §4.

> **Newborough Warren water levels — October 2026**
>
> The latest round of readings was taken on 3 November, covering 68 dipwells across the reserve.
>
> The water table is on the way back up. 55 wells rose, 12 fell and one held steady, a mean rise
> of **+0.07 m**. September turned out to be this year's low point, so the recovery has begun —
> though four wells (D7, NW3, NW6 and CEH22) were still completely dry when we visited.
>
> Rain was almost exactly normal: **101.8 mm at RAF Valley**, against a long-run October average
> of 101.6 mm. Our two local gauges bracketed it — 87.4 mm at Rhianfa and 115.1 mm at Capel Gwyn.
> Over the full twelve months to October we've had 864 mm, which is 101% of average. A thoroughly
> unremarkable year for rainfall.
>
> The dunes recovered fastest (+0.13 m), while the main forest was the only area to keep falling
> (−0.08 m).
>
> But some perspective: compared with the same month in previous years, **this October is lower
> than 9 of the last 10**. And for the winter ahead, the lake edge — the part of the warren
> closest to flooding — would need 495 mm of rain between October and the end of January to bring
> water up to ground level. A typical season gives 400 mm. So it would take a distinctly wet
> winter. 102 mm has fallen so far.
>
> Full newsletter, with maps: https://newbroman.github.io/Newborough_Hydrology/water_watch/

## 3. What could not be done, and why it needs you

**The group is behind a login.** A logged-out fetch of that URL returns Facebook's generic login
page — about 3,820 characters, with the group id appearing only in the `next=` redirect
parameter. No `<title>`, no `og:title`, no `og:description`. Nothing about the group is visible:
not its name, not its description, not whether it is public or private, not its member count.
Re-fetching will not change that.

So **do not fetch that URL expecting to learn anything.** It needs an authenticated browser — a
session running on Martin's machine with his Chrome sign-in (Claude in Chrome), or the desktop
app's browser pane. The `Fieldwork Oct 2026` chat was a cloud session with neither; see
`notes/reference/SESSION_MODES.md` §"Browser access and the L14's folder", and T-183.

**Three things to read off the group, which is all this needs:**

1. **Its name and description** — what the group is actually for.
2. **Who is in it** — Newborough/Malltraeth locals, Anglesey-wide, flood-affected residents, or a
   more technical crowd. This decides the register.
3. **Two or three recent posts** — how people there actually write. More useful than the
   description.

## 4. Rules for editing the draft

- **Do not recalculate the numbers. Quote the published issue.** Every figure above comes from
  `water_watch/Newborough_Water_Watch_2026_10.pdf`, **sha256 `91c053b6…`** (1,704,514 bytes,
  7 pages). `pdftotext -layout` it and read them off. Recalculating invites a public figure that
  disagrees with the newsletter it links to.
- **The flood threshold is a RAINFALL THRESHOLD, NOT A PROBABILITY.** The equations give the
  amount that would have to fall; they do not give a chance of flooding. The draft says "it would
  take a distinctly wet winter" for exactly this reason, and the newsletter's own caption says
  the same. On a public group, and especially a flood-aware one, this is the sentence most likely
  to be misread. Do not convert it into odds, a percentage chance, or a forecast.
- **The window differs by area** (D-315 / 1.7.8): the lake edge peaks in **January** over four
  months, the other four areas in **February** over five. The draft quotes the lake edge's
  January window because that is the nearest-to-flooding area. If you quote another area, quote
  its own window with it.
- **Cluster names**: the draft translates C1-C5 into "the dunes", "the main forest", "the lake
  edge". Put the labels back if the group is technical.

## 5. The three judgement calls Martin may want to overturn

Raised with him on 2026-11-07 and left open, because they depend on the group:

1. **Plain-English cluster names vs C1-C5.** Plain English in the draft.
2. **How hard to lead on the flood outlook.** The draft leads with the recovery and puts the
   flood paragraph last. *If it is a local flooding group, the recommendation is to invert that*
   — flood outlook first, by-area detail cut.
3. **Whether the "lower than 9 of the last 10 Octobers" line stays.** It is in the draft on
   purpose: leading with the recovery alone reads as better news than the record supports. If
   Martin wants it purely factual with no framing, that paragraph goes.

## 6. Where the figures live

| figure | source |
|---|---|
| all of them | `water_watch/Newborough_Water_Watch_2026_10.pdf`, sha `91c053b6…` |
| the live page the post links to | https://newbroman.github.io/Newborough_Hydrology/water_watch/ (gh-pages `7c22748`) |
| the engine that produced it | `living/newborough_report.py` 1.7.8 |

**Read the newsletter from `water_watch/`, never `living/output/`.** The engine writes a copy of
the same name into `living/output/<year>/<Month>/`, it is gitignored, and on 2026-11-07 Martin
read a stale one from there (`1d879ba1`) and reported the flood paragraph missing when the
published copy in the same clone (`91c053b6`) had it. Two files, identical names. J-4 carries it.

---

## Correction appended 2026-11-07, after a fieldwork-handover chat tested the group

That chat read the group **with no session at all** and corrected §3. The correction is
accepted; §3 stands above as written and is superseded here.

**§3 IS WRONG ABOUT WHY THE FETCH FAILED.** The group is **public — 22 members** — and the
desktop app's **browser pane pulled a full post via permalink logged out**. So:

- What was measured here is still true as far as it goes: a plain **HTTP fetch** of
  `https://www.facebook.com/groups/1164026318685018` returns Facebook's login page, 3,820
  characters, no `og:` tags. That is a fact about *fetching*, not about the group.
- What §3 then **inferred is false**: it concluded the group "needs an authenticated browser"
  and told the next session the content was unreachable without a login. A **browser is
  enough; no sign-in is needed.** One observation was generalised into a claim about access it
  did not support, and the warning not to "waste a fetch" would have stopped a capable session
  from simply looking.
- The durable route is therefore the **app's own browser pane**, not Claude in Chrome: it does
  not depend on Martin staying signed in anywhere.

**Still true, and the reason the distinction matters:** a tool that only speaks HTTP cannot read
this group, so a cloud session with no browser still cannot. Read the group with a browser, and
do not conclude anything about a site's accessibility from an HTTP fetch alone.

### Two corrections that chat made which do NOT hold, both from a clone one commit behind

It warned, correctly, that the board was stale and said to fetch before trusting any count. That
warning is also the explanation for these two, so they are recorded rather than argued:

1. **"T-183 doesn't exist; the highest row is T-182."** It is on `origin/main`: `T-183` is the
   highest id in `tools/task_register.csv`, added in public `48e0f63`, which is the commit that
   clone was missing. Verified by reading the CSV out of `origin/main`.
2. **"The three open judgement calls are nowhere in the tree."** They are **§5 of this brief**,
   line 84, in the same commit.

A third correction — that `cloud_setup.sh` is wrong for a native L14 session, which it is — was
aimed at **"step 2 of your brief"**. This brief has six sections, none of which mentions
`cloud_setup.sh`; the instruction it is correcting is in the `Fieldwork Oct 2026` chat's own
opening brief, not here.

**On Tier 0:** that chat reported 754 lines against the 650 budget, 104 over. Measured on the
tree as pushed, `session_handover --check` reports **625/650, ok**. The difference is presumably
its own uncommitted 197-line handover file sitting in a Tier-0 path, which cannot be seen from
outside its tree. Either way the advice is sound: do not grow the handover note.

---

## Martin answered the three judgement calls, 2026-11-08

*"plain english names, flood outlook first, keep the october line"*. §5 is therefore CLOSED.
The post below is the draft of §2 restructured to those three answers, and it supersedes it.

1. **Plain-English area names** — not C1–C5.
2. **Flood outlook leads**, which inverts §2's order. §5's own recommendation was to invert it
   *if* the group was flood-focused; Martin confirmed without being asked which it was.
3. **The "lower than 9 of the last 10 Octobers" line stays.**

**One simplification he may still want to overrule.** Four cluster labels render into plain
English without inventing anything: Lake Edge → *the lake edge*, Dune → *the dunes*, Main
Forest → *the main forest*, Coastal Forest → *the coastal forest*. **C3 "Western Residual" does
not.** It is rendered *"the western dunes"* on the strength of the corpus's own text —
`report_edits/text/report12.md` calls C1/C2 "the eastern open dune" and C3 a "deep buffer", so
C3 is the open dune ground to the west. But **"Residual" is partly a catch-all**: `report8.md`
records its cluster stability at 0.38 against 0.98+ for the other four, "reflecting the
landscape heterogeneity of this group". *The western dunes* is therefore a simplification, not a
translation. Do not extend it to anything load-bearing.

### The post, as answered

> **Newborough Warren water levels — October 2026**
>
> **Could the warren flood this winter?** On the current numbers it would take a notably wet one.
>
> Each part of the reserve has a measured rainfall threshold — the amount that would have to fall
> to bring the water table up to ground level, given how deep it fell this summer. The lake edge
> is closest: it would need **495 mm between October and the end of January**, against a typical
> 400 mm for those four months. So far 102 mm has fallen, with one of the four months gone.
>
> Everywhere else needs more, and has until the end of February: the dunes 597 mm, the western
> dunes 657 mm, the main forest 955 mm and the coastal forest 1,037 mm — against a typical
> 461 mm. The forest would need better than twice an average season.
>
> These are rainfall thresholds, not forecasts. They say what it would take, not how likely it is.
>
> **Where the levels actually are.** The latest round was read on 3 November, covering 68
> dipwells. The water table is on the way back up: 55 wells rose, 12 fell, one held steady, a mean
> rise of **+0.07 m**. September turned out to be this year's low point. Four wells (D7, NW3, NW6
> and CEH22) were still completely dry when we visited.
>
> The dunes recovered fastest (+0.13 m); the main forest was the only area still falling
> (−0.08 m).
>
> **The rain was unremarkable.** 101.8 mm at RAF Valley against a long-run October average of
> 101.6 mm. Our two local gauges bracketed it — 87.4 mm at Rhianfa, 115.1 mm at Capel Gwyn.
> Across the twelve months to October we've had 864 mm, 101% of average.
>
> **But some perspective:** compared with the same month in previous years, this October is
> **lower than 9 of the last 10**. An average year of rainfall has not undone the deficit.
>
> Full newsletter, with maps: https://newbroman.github.io/Newborough_Hydrology/water_watch/

**The sentence that must not be edited away:** *"These are rainfall thresholds, not forecasts."*
Leading with the flood outlook raises the risk §4 names — a flood-aware group reading a threshold
as a probability — so the disclaimer moved up with it rather than staying in a caption. If the
post is shortened, shorten something else.

**Still to do:** nothing, unless the group's register asks for a different voice. The three calls
are answered and every figure traces to `water_watch/Newborough_Water_Watch_2026_10.pdf`
(sha `91c053b6…`). Martin posts it.
