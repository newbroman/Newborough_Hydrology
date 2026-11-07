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
