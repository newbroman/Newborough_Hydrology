#!/usr/bin/env python3
"""
hindcast_calibrate.py — calibrate a free-running SSM hindcast to the well period, drive it
through the wet-area model, and render the film.

WHAT THIS IS

  A TOOL (writes to working/updates/). Martin, 2026-09-17: "surely the better way is to
  calibrate the runs through the SSM runs through the well record period and extend
  backwards?" The recurrence cannot be run backwards — it amplifies error by 1/(1-b3) a
  month — but a free run CAN be calibrated where wells exist and the calibration carried
  through the whole run. This does that by empirical quantile mapping of the modelled
  monthly median level onto the observed one over the months with wells (ranks kept, mean
  bias removed, tails continued with the outer decile's slope), then puts the calibrated
  level through D-178's two curves and, optionally, renders the film with the per-cell
  switching levels.

  Kept separate from sentinel_wet_floor.py on 2026-09-17 because that file was being
  edited by another session (1.7.0-1.9.0, the forecaster feed); fold in later if wanted.

  Measured on the 1930-12 Mode C run against 2005-2026 (238 months, >= 20 wells):
    raw     bias -0.087 m, RMSE 0.226, rho 0.82; wet end (obs > -0.3 m) bias -0.21
    mapped  bias  0.000 m, RMSE 0.211;           wet end bias -0.10
  Note the raw RMSE: the free run seeded in 1930 is BETTER than the Mode C figure D-177
  quotes (0.366), which was seeded in 2005-10 and scored during its own spin-up.

USAGE
  python3 tools/hindcast_calibrate.py --hindcast working/updates/W94_27_from1930_hindcast_monthly.csv
  python3 tools/hindcast_calibrate.py --hindcast ... --film            # the bare film
  python3 tools/hindcast_calibrate.py --hindcast ... --presentation    # slides + film + credits
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) - 2026-09-17. First cut, from the
#   2026-09-17 sandbox: quantile-mapped calibration, the curves, the film and the
#   presentation cut (slides from the plain-English guide, timed by word count).

import argparse
import sys
import textwrap
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

import numpy as np                                            # noqa: E402
import pandas as pd                                           # noqa: E402

from utils.console_utils import banner, info, phase, progress, saved, step, warn  # noqa: E402

OUT = REPO / "working" / "updates"
MODEL_CSV = OUT / "W94_27_wet_area_model.csv"
THRESHOLDS = OUT / "W94_27_cell_thresholds.npz"
BACKGROUND = OUT / "W94_27_scene_2021-04-04.png"
QMAP_MIN_WELLS = 20
QMAP_TAIL_FRACTION = 0.10
QMAP_MIN_MONTHS = 60
FPS = 12
WORDS_PER_MINUTE = 250.0
SLIDE_LEAD_S = 1.5
COL_WATER, COL_FLOOR, COL_BEYOND = (0.04, 0.43, 0.56), (0.85, 0.68, 0.10), (0.95, 0.72, 0.55)


def quantile_map(model, observed):
    """f(x): the free run's level mapped onto the observed distribution."""
    m, o = np.sort(np.asarray(model, float)), np.sort(np.asarray(observed, float))
    k = max(5, int(len(m) * QMAP_TAIL_FRACTION))
    slo, shi = np.polyfit(m[:k], o[:k], 1)[0], np.polyfit(m[-k:], o[-k:], 1)[0]

    def f(x):
        x = np.asarray(x, float)
        q = np.interp(x, m, o)
        lo, hi = x < m[0], x > m[-1]
        q[lo] = o[0] + slo * (x[lo] - m[0])
        q[hi] = o[-1] + shi * (x[hi] - m[-1])
        return q
    return f


def calibrate(hc, mode):
    g = hc[hc["mode"] == mode]
    ok = g["median_level_observed_m"].notna() & (g["n_wells_observed"] >= QMAP_MIN_WELLS)
    if ok.sum() < QMAP_MIN_MONTHS:
        warn(f"  Mode {mode}: {int(ok.sum())} months with wells — too few to calibrate; left raw")
        return g["median_level_modelled_m"].values
    qm = quantile_map(g.loc[ok, "median_level_modelled_m"], g.loc[ok, "median_level_observed_m"])
    cal = qm(g["median_level_modelled_m"].values)
    d0 = g.loc[ok, "median_level_modelled_m"] - g.loc[ok, "median_level_observed_m"]
    d1 = pd.Series(cal, index=g.index)[ok] - g.loc[ok, "median_level_observed_m"]
    wet = g.loc[ok, "median_level_observed_m"] > -0.3
    step(f"Mode {mode} calibrated over {int(ok.sum())} months: bias {d0.mean():+.3f} -> {d1.mean():+.3f} m; "
         f"RMSE {np.sqrt((d0 ** 2).mean()):.3f} -> {np.sqrt((d1 ** 2).mean()):.3f}; wet-end bias "
         f"{d0[wet].mean():+.3f} -> {d1[wet].mean():+.3f}; level max {g['median_level_modelled_m'].max():+.2f} -> {cal.max():+.2f}")
    return cal


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--hindcast", required=True, help="a phase 27 *_hindcast_monthly.csv")
    ap.add_argument("--mode", default=None, help="which mode (default: C if present, else the only one)")
    ap.add_argument("--film", action="store_true", help="render the bare film (map, trace, technical caption)")
    ap.add_argument("--presentation", action="store_true", help="render the presentation cut with the guide slides")
    args = ap.parse_args()
    banner("Hindcast calibration and the wet-area film", __version__)
    hc = pd.read_csv(args.hindcast)
    mode = args.mode or ("C" if (hc["mode"] == "C").any() else hc["mode"].iloc[0])
    stem = "W94_27_" + Path(args.hindcast).stem.replace("W94_27_", "").replace("_hindcast_monthly", "")
    F = pd.read_csv(MODEL_CSV).set_index("cls")
    phase(1, f"Calibrating Mode {mode} of {Path(args.hindcast).name} to the well period")
    g = hc[hc["mode"] == mode].reset_index(drop=True)
    g["median_level_calibrated_m"] = calibrate(hc, mode)
    hmax = float(F.loc["open_water", "h_max"])
    floor_ha = None
    if THRESHOLDS.exists():
        floor_ha = float(np.load(THRESHOLDS)["floor"].sum() * 0.01)
    for cls in ("open_water", "wet_floor"):
        a, b = float(F.loc[cls, "a"]), float(F.loc[cls, "b"])
        for src, tag in (("median_level_calibrated_m", ""), ("median_level_modelled_m", "_raw_level")):
            v = a * np.exp(b * g[src].values)
            if floor_ha:
                v = np.minimum(v, floor_ha)
            g[f"{cls}_ha{tag}"] = v
    if floor_ha:
        g["wet_floor_ha"] = np.minimum(g["wet_floor_ha"], floor_ha - g["open_water_ha"])
    g["above_fitted_range"] = g["median_level_calibrated_m"] > hmax
    keep = ["month", "mode", "median_level_modelled_m", "median_level_calibrated_m", "above_fitted_range",
            "median_level_observed_m", "n_wells_observed", "open_water_ha", "wet_floor_ha",
            "open_water_ha_raw_level", "wet_floor_ha_raw_level"]
    g[keep].round(3).to_csv(OUT / f"{stem}_wet_area_calibrated.csv", index=False)
    saved(f"{stem}_wet_area_calibrated.csv")
    n_over = int(g["above_fitted_range"].sum())
    t = pd.to_datetime(g["month"])
    w = g[t.dt.month.isin([1, 2, 3])].copy(); w["hy"] = t[w.index].dt.year
    pk = w.groupby("hy")["open_water_ha"].max().sort_values(ascending=False)
    info(f"  {n_over} month(s) above the fitted range (> {hmax:+.2f} m); wettest Jan-Mar by open water: "
         + ", ".join(f"{y} {v:.0f} ha" for y, v in pk.head(6).items()))
    if not (args.film or args.presentation):
        return 0
    if not THRESHOLDS.exists():
        warn(f"no {THRESHOLDS.name}: run sentinel_wet_floor.py --two-class first")
        return 1
    rc = 0
    if args.film:
        rc |= render(g, mode, stem, hmax, n_over, presentation=False)
    if args.presentation:
        rc |= render(g, mode, stem, hmax, n_over, presentation=True)
    return rc


def render(g, mode, stem, hmax, n_over, presentation=False):
    import imageio                                            # noqa: PLC0415
    import matplotlib                                         # noqa: PLC0415
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt                           # noqa: PLC0415
    from PIL import Image                                     # noqa: PLC0415
    T = np.load(THRESHOLDS)
    hb, hd, floor = T["h_open_water"], T["h_wet_floor"], T["floor"]
    t, lvl = pd.to_datetime(g["month"]), g["median_level_calibrated_m"].values
    aw, af = g["open_water_ha"].values, g["wet_floor_ha"].values
    base = (np.array(Image.open(BACKGROUND).convert("L")).astype(float) / 255 if BACKGROUND.exists()
            else np.full(floor.shape, 0.6))
    rgb = np.stack([base * 0.55 + 0.25] * 3, -1)

    def even(a):
        return a[:a.shape[0] // 2 * 2, :a.shape[1] // 2 * 2].copy()

    def slide(title, paras, foot=None):
        words = len(title.split()) + sum(len(p.split()) for p in paras)
        seconds = SLIDE_LEAD_S + words / (WORDS_PER_MINUTE / 60.0)
        fig = plt.figure(figsize=(12.8, 7.2), dpi=100); fig.patch.set_facecolor("#f7f5f0")
        ax = fig.add_axes([0, 0, 1, 1]); ax.set_axis_off(); y = 0.91
        for line in textwrap.wrap(title, 52):
            ax.text(0.06, y, line, fontsize=24, weight="bold", va="top", color="#1f1f1f"); y -= 0.075
        y -= 0.03
        nl = sum(len(textwrap.wrap(p, 95)) for p in paras) + len(paras)
        fs = 15 if nl <= 11 else (13.5 if nl <= 14 else 12.5); lh = fs * 0.0034; ww = int(1400 / fs)
        for p in paras:
            for line in textwrap.wrap(p, ww):
                ax.text(0.06, y, line, fontsize=fs, va="top", color="#2a2a2a"); y -= lh
            y -= lh * 0.6
        if foot:
            ax.text(0.06, 0.05, foot, fontsize=11, color="#666")
        fig.canvas.draw(); a = even(np.asarray(fig.canvas.buffer_rgba())[..., :3]); plt.close(fig)
        return [a] * int(round(seconds * FPS))

    frames = []
    if presentation:
        for title, paras, foot in SLIDES_BEFORE:
            frames += slide(title, paras, foot)
    fig = plt.figure(figsize=(12.8, 7.2), dpi=100); fig.patch.set_facecolor("white")
    ax = fig.add_axes([0.02, 0.30, 0.62, 0.62]); ax2 = fig.add_axes([0.07, 0.09, 0.90, 0.16])
    axt = fig.add_axes([0.66, 0.30, 0.33, 0.62]); axt.set_axis_off()
    im = ax.imshow(rgb); ax.set_axis_off(); title = ax.set_title("", fontsize=12, loc="left")
    wells_from = t[g["median_level_observed_m"].notna()].min() if g["median_level_observed_m"].notna().any() else t.max()
    ax2.fill_between(t, -1.4, 0.4, where=t < wells_from, color="#eeeeee", zorder=0)
    ax2.plot(t, lvl, color="black", lw=0.6); ax2.axhline(0, color="grey", lw=0.6, ls=":")
    ax2.axhline(hmax, color="#0b6e8f", lw=0.6, ls="--"); ax2.fill_between(t, hmax, 0.4, color="#e8734a", alpha=0.10)
    ax2.set_ylim(-1.4, 0.4); ax2.set_ylabel("water table, m (0 = ground)", fontsize=8); ax2.tick_params(labelsize=8)
    ax2.text(t.iloc[12], 0.26, "before the wells: model only, corrected to the well years", fontsize=7, color="#555")
    ax2.text(wells_from + pd.Timedelta(days=300), 0.26, "wells measured", fontsize=7, color="#555")
    ax2.text(t.iloc[len(t) // 3], hmax + 0.05, "above the 2021 flood: beyond anything measured", fontsize=6.5, color="#b5532a")
    marker = ax2.axvline(t[0], color="#c0504d", lw=1.4)
    txt = axt.text(0.0, 1.0, CAPTION, fontsize=9.6, va="top", ha="left", linespacing=1.4)

    def frame(i):
        h = lvl[i]; hc = min(h, hmax); img = rgb.copy()
        y, b = floor & (hd <= hc), floor & (hb <= hc); over = h > hmax
        if over:
            img[floor & ~y] = COL_BEYOND
        img[y] = COL_FLOOR; img[b] = COL_WATER
        im.set_data(img); marker.set_xdata([t[i], t[i]])
        txt.set_text(CAPTION + (CAPTION_BEYOND if over else "")); txt.set_color("#7a2e0e" if over else "#222")
        title.set_text(f"{t[i].strftime('%B %Y')}   water table {h:+.2f} m   open water {aw[i]:.0f} ha   "
                       f"wet floor {af[i]:.0f} ha" + ("   BEYOND THE RECORD" if over else ""))
        fig.canvas.draw(); return even(np.asarray(fig.canvas.buffer_rgba())[..., :3])

    frames += [frame(0)] * FPS
    n = len(g)
    for i in range(n):
        frames.append(frame(i))
        if i % 60 == 0:
            progress(i + 1, n, t[i].strftime("%Y-%m"))
    print(flush=True)
    frames += [frames[-1]] * (2 * FPS)
    plt.close(fig)
    if presentation:
        for title_, paras, foot in SLIDES_AFTER:
            frames += slide(title_, paras, foot)
    name = f"{stem}_{'presentation' if presentation else 'film'}_mode{mode}"
    try:
        import imageio_ffmpeg                                 # noqa: PLC0415
        assert imageio_ffmpeg  # probe: MP4 needs the ffmpeg binary
        imageio.mimwrite(OUT / f"{name}.mp4", frames, fps=FPS, codec="libx264", quality=8, macro_block_size=None)
        saved(f"{name}.mp4  ({len(frames) / FPS:.0f} s)")
    except ImportError:
        warn("imageio-ffmpeg not installed; writing a GIF")
        Image.fromarray(frames[0]).save(OUT / f"{name}.gif", save_all=True,
                                        append_images=[Image.fromarray(f) for f in frames[1:]],
                                        duration=int(1000 / FPS), loop=0)
        saved(f"{name}.gif")
    return 0


CAPTION = ("Today's reserve — forest and all — under the\nweather of each past month. Not what actually\n"
           "happened: a what-if. The model's water table is\ncorrected to match the wells over 2005–2026.\n\n"
           "Blue: open water.  Yellow: wet floor.\n10 m squares from satellite pictures, 2016–2026.\n"
           "Not a flood map: puddles and margins are too\nsmall to show.\n\n"
           "Totals in the title are from the corrected water\ntable; open water is right to within a factor of\n"
           "two, wet floor to about 15 %.")
CAPTION_BEYOND = ("\n\nTHIS MONTH IS BEYOND THE RECORD.\nThe water table is above the 2021 flood, the\n"
                  "wettest ever measured. The totals are the curves\nrun past the end of the data; pale orange is\n"
                  "slack floor never seen wet — wetter than\nanything on record, where exactly unknown.")
SLIDES_BEFORE = [
    ("Newborough Warren under a century of weather",
     ["A film of how wet the dune slacks would have been, month by month, from 1930 to 2026 — if the reserve as it stands today had lived through the weather of each of those years.",
      "Newborough Warren is a sand-dune reserve on Anglesey. Between the dunes lie hundreds of low hollows called slacks. In a wet winter the water table rises into them: the ground goes damp, pools appear, and in a very wet spring whole slacks stand under water."],
     "Newborough Warren hydrology study, 2026 · Martin Hollingham"),
    ("How to read the film",
     ["YELLOW is wet floor: saturated ground, or a thin sheet of water hidden in the grass.",
      "BLUE is open water: pools you could see from the air.",
      "The title gives the total of each across the whole warren, in hectares (a hectare is a little larger than a rugby pitch).",
      "The line at the bottom is the water table — how far below or above the ground the groundwater sits, averaged over the reserve's monitoring wells. The red marker is where the film has got to. The clock runs at a year a second."], None),
    ("How it was made: three things joined together",
     ["1.  A weather-driven groundwater model. Since 2005 the reserve's dipwells have been read every month, and from them we learned a simple rule for how the water table rises with rain and falls with evaporation and drainage. RAF Valley has kept weather records since 1930, so the rule can be run through the whole century, steered by nothing but the weather. Where the wells exist, the model's water table is corrected to match them, and that correction is carried back through the years before the wells.",
      "2.  Satellite pictures. Sentinel-2 has photographed the warren every few days since 2016 in 10 m squares. In the near-infrared, water is black and grass is bright, so a wet slack floor is a dark patch. Counting the dark squares in 41 clear winter pictures and comparing with the water table gives two smooth curves — one for open water, one for wet floor.",
      "3.  Where the water goes. Each 10 m square has its own history in those pictures, so we know the water-table level at which it usually turns dark. The film lights each square when the model reaches that level. WHERE the colours appear was learned from the satellite; WHEN is the model."], None),
    ("Please read this before watching",
     ["It is today's warren, not the warren of the time. The rules were learned from 2005–2026 and the ground is the 2023 survey, with Newborough Forest at its present size. The forest was only planted between 1947 and 1965, and a forest lowers the water table around it. In 1939 there was no forest. The film answers a what-if — what would the reserve as it is now have done under that weather — not what actually happened."], None),
    ("The biggest floods go beyond anything measured",
     ["The wettest spring on record was 2021. In some months — 1939, 1959, 1961–62 and 2000–01 — the model pushes the water table higher than that.",
      "No picture has seen the warren like that. So those months are marked BEYOND THE RECORD, the totals are the curves run past the end of the data, and the rest of the slack floor turns PALE ORANGE: wetter than anything on record, where exactly we cannot say.",
      "The honest claim for those winters is that they were bigger than 2021, nothing finer."], None),
    ("And a little more",
     ["It is not a flood map. The squares are 10 m across; narrow margins, small pools and thin sheets over grass are invisible at that size — roughly a third of the water in a big flood. The moment a square lights is known only to within five or ten centimetres of water table.",
      "The model's mistakes carry through. Even corrected to the wells, it reproduces the measured water table to about twenty centimetres, and it still runs about ten centimetres low in the wettest months. A ten-centimetre error changes the open-water area by about half, because pools appear suddenly once the water nears the surface. Yellow is the steadier colour; blue is right to within a factor of two. The first two years are the model settling from its starting guess.",
      "Winter rules all year. The curves come from November-to-March pictures; summer months show what the water table would imply, not what a summer photograph would show."], None),
]
SLIDES_AFTER = [
    ("What the film says, cautions attached",
     ["The 1960s were the wet decade, with several times the open water of an average winter in any other decade.",
      "The winters of 1961–62 and 2000–01 stand out as the two great floods of the century, with 1938–39 and 1958–59 behind them; 2015–16 was the wettest of the satellite era after 2021.",
      "The 1970s and 1990s were the dry decades, with almost no open water in an average winter.",
      "All of it is the model's account of what the weather would do to the reserve as it stands today."], None),
    ("Credits and sources",
     ["Newborough Warren hydrology study, 2026 — Martin Hollingham.",
      "Weather: RAF Valley monthly record, 1930–2026. Water table: the reserve's dipwell network, 2005–2026. Imagery: Copernicus Sentinel-2, 2016–2026. Ground: 2023 survey.",
      "Model, code and data: github.com/newbroman/Newborough_Hydrology. The method is recorded as decision D-178; the full written guide accompanies this film."], None),
]

if __name__ == "__main__":
    sys.exit(main())
