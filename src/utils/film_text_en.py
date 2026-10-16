"""
film_text_en.py - the hindcast film's words, English (the reference table).

Every key here is the complete set; the other languages are held to it by
tools/film_text_lint.py. Templates are str.format templates with named fields; the fields a
key takes are fixed by this file. The wording is Script 47's as at 1.8.1, moved here
unchanged (the English caveats file is byte-identical before and after the move).
"""
from __future__ import annotations

__version__ = "1.0.1"  # Hollingham (2026) - 2026-10-15. says_p1 "several times" -> "about twice" (the 1960s
#   carry 1.8-2.4x the other decades' mean winter open water in 47_01); more_p4 (the D-226 datum paragraph)
#   removed - the film keeps one straight story (Martin 2026-10-15: "keep the modeling simple").
# 1.0.0  Hollingham (2026) - 2026-10-13. The 1.8.1 English, moved out of Script 47.

NAME = "English"
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August",
          "September", "October", "November", "December"]
MONTHS_SHORT = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

T = {
    # ---- the title, the strap, the byline, the opening clip ----------------------------
    "title": "Newborough Warren under a century of weather",
    "subtitle": "Today's reserve under the weather of every month since 1930: a what-if, not a history",
    "byline": "Newborough Warren hydrology study, 2026 · Martin Hollingham",
    "open_clip_label": "The last decade",
    "contents": "Contents",
    "chapter_opening": "Opening",
    "chapter_clip": "{label}: {y0}–{y1}",
    "chapter_title": "Title and contents",
    "chapter_film": "The film: {y0}–{y1}",
    "slide_count": "{a} / {b}",

    # ---- the frame: readout, hydrograph, caption -----------------------------------------
    "readout_water_table": "water table",
    "readout_open_water": "open water",
    "readout_wet_floor": "wet floor",
    "study": "study area {floor_ha:.0f} ha",
    "beyond": "BEYOND THE RECORD",
    "hydro_ylabel": "water table, m\n(0 = ground)",
    "era_before": "before the wells: model only, corrected to the well years",
    "era_wells": "wells measured",
    "era_above": "above the 2021 flood: beyond anything measured",
    "arrival_wet_floor": "wet floor appears",
    "arrival_open_water": "open water appears",
    "caption": (
        "Today's reserve under the\nweather of each past month. Not what actually\n"
        "happened: a what-if. The model's water table is\ncorrected to match the wells over 2005–2026.\n\n"
        "Blue: open water.  Yellow: wet floor.\n10 m squares from satellite pictures, 2016–2026.\n"
        "Not a flood map: puddles and margins are too\nsmall to show.\n\n"
        "The outline is the study area: the warren slack\nfloor. Nothing outside it is assessed.\n\n"
        "Totals in the title are from the corrected water\ntable; open water is right to within a\n"
        "factor of {s_ow:.1f}, wet floor to about {wf_pct:.0f} %."),
    "caption_beyond_head": "THIS MONTH IS BEYOND THE RECORD.",
    "caption_beyond": (
        "\n\nTHIS MONTH IS BEYOND THE RECORD.\nThe water table is above the 2021 flood, the\n"
        "wettest ever measured. The totals are the curves\nrun past the end of the data; pale orange is\n"
        "slack floor never seen wet — wetter than\nanything on record, where exactly unknown."),

    # ---- the comparison slide and the thumbnails -----------------------------------------
    "compare_left": "Sentinel-2, true colour",
    "compare_right": "The film, the same month",
    "compare_row": "{when} · model {lvl} m · {aw:.0f} ha open water, {af:.0f} ha wet floor",
    "thumb_label": "{when} · wells {lvl} m",
    "rel_same": "the {kind}",
    "rel_other": "{n} mo {dir} the {when} {kind}",
    "peak": "peak",
    "trough": "trough",
    "after": "after",
    "before": "before",

    # ---- the film's own free-run chart (47_06) --------------------------------------------
    "fr_label_model": "the model: weather only, running since 1930",
    "fr_label_model_stats": " (R² {r2:.2f}, {bias} cm on average)",
    "fr_label_wells": "the dipwells: median of the reference network (months with {n}+ wells)",
    "fr_ylabel": "water table, m (0 = ground)",
    "fr_title": "The warren's water table: the model against the wells",

    # ---- figure references in slide feet ---------------------------------------------------
    "foot_none": "Report figure",
    "foot_one": "Report Figure {num}",
    "foot_one_section": ", section {sec}",
    "foot_many": "Report Figures ",
    "foot_many_section": " (section {sec})",
    "foot_and": " and ",
    "foot_model_run": " · the model against the wells: this film's own run",
    "cop": "Contains modified Copernicus Sentinel data",
    "cop_years": "Contains modified Copernicus Sentinel data {years}",

    # ---- the method slides ---------------------------------------------------------------
    "f4_number": "Figure {n4}",
    "f4_none": "The climate figure",
    "low_phrase": ", on average {cm:.0f} cm {dir}",
    "low": "low",
    "high": "high",
    "m1_title": "1.  A weather-driven groundwater model",
    "m1_p1": (
        "{f4} (left) is the weather and the water table together, 2005–2026. (a) Rain, "
        "month by month, with its long-term average as the dashed line. (b) Evaporation, "
        "which peaks every summer. (c) The running balance of rain minus evaporation: it "
        "climbs through wet runs of months and falls through dry ones. (d) The water table, "
        "averaged over the reserve's dipwells, with the spread between wells shaded. Panels "
        "(c) and (d) rise and fall together: that is the link the model is built on."),
    "m1_p2": (
        "From it the study learned a simple monthly rule: the water table rises with the "
        "month's rain, falls with its evaporation, and drains back in proportion to how high "
        "it stands."),
    "m1_p3": (
        "The chart above right is the test this film depends on. The blue line is the model, "
        "run on nothing but RAF Valley's weather since 1930 with no well reading to correct "
        "it; the black line is what the dipwells measured. The model follows the warren's wet "
        "and dry years{low}: the bias the next slide removes."),
    "m2_title": "Correcting the model to the wells",
    "m2_p1": (
        "Run freely for a century, the model drifts: it has no wells to hold it. So it is "
        "corrected where the wells exist. Over 2005–2026 the model's months are ranked against "
        "the measured months, and each modelled level is replaced by the measured level of the "
        "same rank."),
    "m2_p2": (
        "The order of wet and dry months is the model's own; the correction only removes its "
        "bias. That same correction is then carried back through the years before the wells."),
    "m3_title": "2.  Satellite pictures: the first calibration",
    "m3_p1": (
        "Sentinel-2 has photographed the warren every few days since 2016, in 10 m squares. In "
        "the near-infrared, water is black and grass is bright, so a wet slack floor shows as a "
        "dark patch. {n} winter pictures were clear of cloud."),
    "m3_p2": (
        "In each one the dark squares on the slack floor are counted, split into open water "
        "(the darkest) and wet floor, and set against the water table the dipwells measured in "
        "the same month. Each pair of points on the figure is one picture. Four of them are "
        "shown below in that near-infrared band, driest to wettest, each scaled to its own "
        "slack-floor brightness as the method reads it; each line leads to its points."),
    "m3_p3": (
        "The points fall on two smooth curves. Wet floor grows gently as the water table rises; "
        "open water stays near nothing until the water is close to the surface, then climbs "
        "steeply. These curves turn the film's water table into the hectares in its title."),
    "m3_p4": (
        "They are fitted between {lo_s} m and {hi_s} m, the range the pictures saw. Above "
        "that, the film says BEYOND THE RECORD."),
    "m4_title": "The check: the model against the satellite",
    "m4_p1": (
        "Before the curves are trusted with the model, they are tested with it. Here the "
        "curves are driven by the model's water table instead of the wells, and the area they "
        "predict is compared, month by month, with the area the satellite actually measured."),
    "m4_p2": (
        "The satellite takes no part in the model, so this is an independent test of the water "
        "table itself, not of the curves alone. The same four near-infrared pictures are below; each "
        "line leads to its month on the upper panel and names the peak or trough it belongs "
        "to."),
    "m4_p3": (
        "Wet floor is reproduced closely. Open water, which appears suddenly as the water "
        "reaches the surface, is reproduced less well: a small error in the water table makes a "
        "large one in the area of pools. That is why the film's blue is the less certain colour."),
    "m5_title": "3.  Where the water goes: the second calibration",
    "m5_p1": (
        "The curves say how much of the floor is wet; they do not say where. For that, each "
        "10 m square's own history in the pictures is used: the water-table level at which it "
        "first read wet floor (a, upper map) and first read open water (b, lower map)."),
    "m5_p2": (
        "The lowest hollows switch first, the higher margins last. Grey squares never switched "
        "within the range the pictures saw, and the forest is left out because under trees the "
        "satellite sees the canopy, not the ground."),
    "m5_p3": (
        "The film lights each square when the model's water table reaches its level. WHERE the "
        "colours appear was learned from the satellite; WHEN is the model."),
    "m6_title": "What the warren looks like from space",
    "m6_p1": (
        "The driest and the wettest of those four pictures, each beside the film's own map "
        "of the same month."),
    "m6_p2": (
        "In the pictures the flooded slack floors are the dark patches between the pale dunes. "
        "The film lights its yellow and blue in the same hollows as its water table rises."),
    "m6_p3": (
        "This is an illustration, not a test. Where the colours appear was learned from these "
        "same pictures, so some of the likeness is built in. The independent test is the "
        "check two slides back, where the satellite takes no part in the model."),
    "m6_foot": "{cop} {y0}, {y1}",

    # ---- the slides before the film --------------------------------------------------------
    "about_title": "About this film",
    "about_p1": (
        "A film of how wet the dune slacks would have been, month by month, from 1930 to 2026 — if "
        "the reserve as it stands today had lived through the weather of each of those years."),
    "about_p2": (
        "Newborough Warren is a sand-dune reserve on Anglesey. Between the dunes lie hundreds of low "
        "hollows called slacks. In a wet winter the water table rises into them: the ground goes "
        "damp, pools appear, and in a very wet spring whole slacks stand under water."),
    "about_p3": (
        "Only the warren is modelled, not the forest. Everything here is about the open dune slacks "
        "of Newborough Warren — the study area outlined on the map. The planted forest beside them "
        "is not part of the model and is not assessed; absence of yellow and blue cells does not "
        "imply an absence of flooding, rather it has not been modelled."),
    "howto_title": "How to read the film",
    "howto_p1": "YELLOW is wet floor: saturated ground, or a thin sheet of water hidden in the grass.",
    "howto_p2": "BLUE is open water: pools you could see from the air.",
    "howto_p3": (
        "The outline on the map is the study area — {floor_ha:.0f} hectares of slack floor within "
        "the warren. Everything the film says is about the ground inside it. Blank ground outside "
        "the outline was not assessed; it is not a claim that it was dry."),
    "howto_p4": (
        "The title gives the total of each across the study area, in hectares (a hectare is a "
        "little larger than a rugby pitch)."),
    "howto_p5": (
        "The line at the bottom is the water table — how far below or above the ground the "
        "groundwater sits, averaged over the reserve's monitoring wells. The red marker is where "
        "the film has got to. The clock runs at three seconds a year; between one month's "
        "reading and the next the map is drawn at levels in between, so the water rises and "
        "drains smoothly, but the readings are the months."),
    "howto_p6": (
        "The slides that follow show how it was made: a groundwater model, satellite pictures "
        "and a map of where the water goes, joined together, each beside the report figures "
        "that calibrate and test it."),
    "hear_title": "What you hear",
    "hear_p1": "The sound is made from the water, month by month. Nothing in it is recorded.",
    "hear_p2": (
        "A soft chord runs throughout. While the months play, one of its voices swells "
        "with each month's rain, another with its evaporation, and the highest opens as the "
        "water table rises; in the months beyond the record it trembles."),
    "hear_p3": (
        "A steady chord rises with the water table, from silence in the driest months to "
        "full at the top of the record; above the yellow line a seventh joins it, and the "
        "chord tightens as the warren floods, leaning toward where the water is: right for "
        "the east of the warren, left for the west."),
    "hear_p4": (
        "Held notes sound while the water table is above the lines on the chart at the bottom: "
        "one above the yellow line, where wet floor appears; a higher one above the blue "
        "line, where open water appears; and the highest above the 2021 flood."),
    "hear_p5": (
        "Underneath, a breath: one soft note through the winter half of each year, silence "
        "through the summer, so a year lasts three seconds."),
    "read_title": "Please read this before watching",
    "read_p1": (
        "It is today's warren, not the warren of the time. The rules were learned from 2005–2026 "
        "and the ground is the 2023 survey, with Newborough Forest at its present size. The forest "
        "was only planted between 1947 and 1965, and a forest lowers the water table around it. In "
        "1939 there was no forest. The film answers a what-if — what would the reserve as it is "
        "now have done under that weather — not what actually happened."),
    "read_p2": (
        "The map covers the warren study area only; blank outside it means not assessed, not "
        "dry."),
    "read_p3": (
        "Satellite pictures: {cop_years}. Report figures are from the Newborough Warren "
        "hydrology study."),
    "big_title": "The biggest floods go beyond anything measured",
    "big_p1": (
        "The wettest spring on record was 2021. In some months — 1939, 1959, 1961–62 and 2000–01 — "
        "the model pushes the water table higher than that, above the {hmax:+.2f} m the "
        "curves were fitted to."),
    "big_p2": (
        "No picture has seen the warren like that. So those months are marked BEYOND THE RECORD, "
        "the totals are the curves run past the end of the data, and the rest of the slack floor "
        "turns PALE ORANGE: wetter than anything on record, where exactly we cannot say."),
    "big_p3": "The honest claim for those winters is that they were bigger than 2021, nothing finer.",

    # ---- the slides after the film ---------------------------------------------------------
    "says_title": "What the film says, cautions attached",
    "says_p1": (
        "The 1960s were the wet decade, with about twice the open water of an average winter in "
        "the other decades."),
    "says_p2": (
        "The winters of 1961–62 and 2000–01 stand out as the two great floods of the century, with "
        "1938–39 and 1958–59 behind them; 2015–16 was the wettest of the satellite era after 2021."),
    "says_p3": (
        "The 1970s and 1990s were the dry decades, with almost no open water in an average winter."),
    "says_p4": (
        "All of it is the model's account of what the weather would do to the reserve as it stands "
        "today."),
    "more_title": "And a little more",
    "more_p1": (
        "It is not a flood map. The squares are 10 m across; narrow margins, small pools and thin "
        "sheets over grass are invisible at that size — roughly a third of the water in a big "
        "flood. The moment a square lights is known only to within five or ten centimetres of "
        "water table."),
    "more_p2": (
        "The model's mistakes carry through. Even corrected to the wells, it reproduces the "
        "measured water table to about twenty centimetres, and it still runs about ten "
        "centimetres low in the wettest months. A ten-centimetre error changes the open-water "
        "area by about half, because pools appear suddenly once the water nears the surface. "
        "Yellow is the steadier colour, good to about {wf_pct:.0f} %; blue is right to "
        "within a factor of {s_ow:.1f}. The first two years are the model settling from its "
        "starting guess."),
    "more_p3": (
        "Winter rules all year. The curves come from November-to-March pictures; summer months "
        "show what the water table would imply, not what a summer photograph would show."),
    "credits_title": "Credits and sources",
    "credits_p1": "Newborough Warren hydrology study, 2026 — Martin Hollingham.",
    "credits_p2": (
        "Weather: RAF Valley monthly record, 1930–2026. Water table: the reserve's dipwell "
        "network, 2005–2026. Ground: 2023 survey."),
    "credits_p3": (
        "Imagery: Copernicus Sentinel-2, 2016–2026, free and open under the Copernicus "
        "licence. {cop_years}."),
    "credits_p4": (
        "Model, code and data: github.com/newbroman/Newborough_Hydrology. The method is recorded "
        "as decision D-178; the full written guide accompanies this film."),
    "credits_p5": (
        "Sound: synthesised by the film's own code from the modelled water table and "
        "areas; no recordings."),
}
