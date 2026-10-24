"""
pet_alternatives.py — evaporation estimates other than Thornthwaite, for Script 50 E13 (D-273).

The SSM's evaporation term is Thornthwaite PET (Script 01), which sees temperature alone. E13 asks
whether an estimate that sees sunshine, wind or humidity removes the 2006-08 excess (D-231). This module
builds those estimates. It reads two raw inputs, a documented raw-input exception like Scripts 09/10/24
and utils/midas_rain.py:

  * data/RAF_Valley_Climate.csv (paths.DATA_CLIMATE_RAW): monthly Tmax, Tmin and sunshine hours;
  * data/midas_weather/valley_01145/ (paths.MIDAS_WEATHER_DIR): MIDAS Open hourly weather (wind, air
    temperature, dew point, station pressure, sunshine) and hourly global radiation. Provenance and DOIs:
    data/MIDAS_WEATHER_PROVENANCE.md.

Two builders:

  monthly_radiation_pet(index, lat_deg)
      Hargreaves, FAO-56 Priestley-Taylor and Makkink, each monthly, from the monthly record, radiation
      from sunshine by the Angstrom relation. Gaps of up to RADIATION_PET_FILL_MONTHS are interpolated.

  midas_monthly_pm(lat_deg)
      FAO-56 Penman-Monteith built daily from the hourly record and summed to months, with two
      decomposition runs: wind held at its day-of-year mean, and vapour pressure held at its
      day-of-year mean. Radiation, month by month: measured global radiation where the day has
      MIDAS_RAD_MIN_HOURS hourly values; else the day's hourly sunshine (Angstrom); else the month's
      sunshine fraction from RAF_Valley_Climate.csv (before hourly sunshine began).

The physical constants are FAO Irrigation and Drainage Paper 56 (Allen et al., 1998), named below with
their equation numbers; the site constants (latitude, anemometer height) come from config.py and the
station height from the MIDAS file itself.

Reproduces, exactly, the scratch runs working/nvc_laurence/scripts/26_e13_scratch.py and
27_e13_wind_scratch.py (2026-10-22/23), which the E13 rule was first run on.
"""
from __future__ import annotations

__version__ = "1.1.0"  # Hollingham (2026) - 2026-10-24 (D-274): midas_monthly_pm also returns the monthly dew
#   point, daily minimum temperature and pressure, so E13b can show the inputs' homogeneity. No PET value changes.
# 1.0.0  # Hollingham (2026) - 2026-10-23 (D-273; Martin 23:20 "Make e13 a proper step"; spec
#   NRG_spec_E13_build_2026-10-23, approved). First issue.

import gzip
import io
from pathlib import Path

import numpy as np
import pandas as pd

from utils.config import (MIDAS_ANEMOMETER_HEIGHT_M, MIDAS_DAY_MIN_HOURS, MIDAS_DEWPOINT_3HOURLY_YEARS,
                          MIDAS_DEWPOINT_3HOURLY_MIN, MIDAS_RAD_MIN_HOURS, MIDAS_MONTH_MIN_DAYS,
                          RADIATION_PET_FILL_MONTHS)
from utils.data_utils import parse_met_date

# ── FAO-56 constants (Allen et al., 1998) ───────────────────────────────────────────────────────────
GSC = 0.0820                    # solar constant, MJ m-2 min-1 (eq. 21)
ANG_A, ANG_B = 0.25, 0.50       # Angstrom coefficients when not calibrated (eq. 35)
ALBEDO = 0.23                   # reference crop albedo (eq. 38)
SIGMA = 4.903e-9                # Stefan-Boltzmann, MJ K-4 m-2 day-1 (eq. 39)
LAMBDA_INV = 0.408              # 1/latent heat, kg MJ-1 (eq. 20 note)
GAMMA_SEA = 0.0665              # psychrometric constant at sea level, kPa C-1 (eq. 8, P = 101.3)
GAMMA_P = 0.000665              # psychrometric constant per kPa of pressure (eq. 8)
P_SEA_KPA = 101.3               # standard pressure at sea level (eq. 7)
T_REF_K = 293.0                 # reference temperature in the pressure-height relation (eq. 7)
LAPSE = 0.0065                  # lapse rate, K m-1 (eq. 7)
P_EXP = 5.26                    # exponent of eq. 7
RSO_A, RSO_B = 0.75, 2e-5       # clear-sky radiation from Ra and elevation (eq. 37)
KELVIN = 273.16                 # as in eq. 39
PM_CN, PM_CD = 900.0, 0.34      # Penman-Monteith reference-grass numerator and denominator (eq. 6)
PM_T_K = 273.0                  # Kelvin offset in eq. 6
WIND_LOG_A, WIND_LOG_B, WIND_LOG_C = 4.87, 67.8, 5.42   # wind at height z to 2 m (eq. 47)
HARG_C, HARG_T = 0.0023, 17.8   # Hargreaves (eq. 52)
PT_ALPHA = 1.26                 # Priestley-Taylor coefficient
MAK_A, MAK_B = 0.61, 0.12       # Makkink (mm day-1 offset)
ES_A, ES_B, ES_C = 0.6108, 17.27, 237.3   # saturation vapour pressure (eq. 11)
DELTA_N = 4098.0                # slope of the vapour-pressure curve (eq. 13)
RNL_A, RNL_B = 0.34, 0.14       # net emissivity (eq. 39)
RNL_C, RNL_D = 1.35, 0.35       # cloudiness factor (eq. 39)
RS_RSO_FLOOR = 0.3              # floor on Rs/Rso in the daily Penman-Monteith cloudiness factor
EARTH_SUN_A, DECL_A, DECL_B = 0.033, 0.409, 1.39   # eqs. 23, 24
DAYS_YEAR = 365
MIN_PER_DAY = 24 * 60
KNOT_MS = 0.514444              # 1 knot in m s-1
HPA_KPA = 10.0                  # hPa per kPa
KJ_MJ = 1000.0                  # kJ per MJ
MM_M = 1000.0                   # mm per m


def es(t):
    """Saturation vapour pressure, kPa (FAO-56 eq. 11)."""
    return ES_A * np.exp(ES_B * t / (t + ES_C))


def _delta(tm):
    return DELTA_N * es(tm) / (tm + ES_C) ** 2


def extraterrestrial(doy, lat_deg):
    """Ra (MJ m-2 day-1) and daylight hours N for day-of-year doy (FAO-56 eqs. 21-25, 34)."""
    phi = np.radians(lat_deg)
    dr = 1 + EARTH_SUN_A * np.cos(2 * np.pi * doy / DAYS_YEAR)
    de = DECL_A * np.sin(2 * np.pi * doy / DAYS_YEAR - DECL_B)
    ws = np.arccos(-np.tan(phi) * np.tan(de))
    ra = MIN_PER_DAY / np.pi * GSC * dr * (ws * np.sin(phi) * np.sin(de) + np.cos(phi) * np.cos(de) * np.sin(ws))
    return ra, 24 / np.pi * ws


def read_raf_monthly() -> pd.DataFrame:
    """Tmax, Tmin (C) and sunshine hours per month from RAF_Valley_Climate.csv, by first of month."""
    from utils.paths import DATA_CLIMATE_RAW
    raw = pd.read_csv(DATA_CLIMATE_RAW)
    idx = raw.iloc[:, 0].apply(parse_met_date)
    t_max_col = "Max Temp ©" if "Max Temp ©" in raw.columns else "Max Temp (C)"
    out = pd.DataFrame({"tx": pd.to_numeric(raw[t_max_col], errors="coerce").values,
                        "tn": pd.to_numeric(raw["Min Temp (C)"], errors="coerce").values,
                        "sun": pd.to_numeric(raw["Sun (hrs)"], errors="coerce").values}, index=pd.DatetimeIndex(idx))
    return out[out.index.notna()].sort_index()


def monthly_radiation_pet(index: pd.DatetimeIndex, lat_deg: float) -> pd.DataFrame:
    """Hargreaves, Priestley-Taylor and Makkink, m/month, on the monthly `index` (first of month)."""
    d = read_raf_monthly().reindex(index)
    doy = (d.index.dayofyear + 15).values          # mid-month
    nd = d.index.days_in_month.values
    ra, n_day = extraterrestrial(doy, lat_deg)
    tm = (d.tx + d.tn) / 2
    hg = HARG_C * LAMBDA_INV * ra * (tm + HARG_T) * np.sqrt((d.tx - d.tn).clip(lower=0)) * nd
    rs = (ANG_A + ANG_B * (d.sun / nd / n_day).clip(0, 1)) * ra
    ea = es(d.tn)
    rnl = SIGMA * (((d.tx + KELVIN) ** 4 + (d.tn + KELVIN) ** 4) / 2) * (RNL_A - RNL_B * np.sqrt(ea)) \
        * (RNL_C * (rs / (RSO_A * ra)).clip(0, 1) - RNL_D)
    dl = _delta(tm)
    pt = (PT_ALPHA * dl / (dl + GAMMA_SEA) * ((1 - ALBEDO) * rs - rnl) * LAMBDA_INV).clip(lower=0) * nd
    mk = (MAK_A * dl / (dl + GAMMA_SEA) * rs * LAMBDA_INV - MAK_B).clip(lower=0) * nd
    alt = pd.DataFrame({"Hargreaves": hg, "Priestley-Taylor": pt, "Makkink": mk}, index=index) / MM_M
    return alt.interpolate(limit=RADIATION_PET_FILL_MONTHS)


# ── MIDAS ───────────────────────────────────────────────────────────────────────────────────────────
def _badc(path: Path) -> tuple[pd.DataFrame, dict]:
    """Body and header of one gzipped BADC-CSV file."""
    t = gzip.open(path, "rt", encoding="utf-8", errors="replace").read()
    head, body = t.split("\ndata\n", 1)
    meta = {}
    for line in head.splitlines():
        p = line.split(",")
        if len(p) >= 3 and p[1] == "G":
            meta.setdefault(p[0], p[2:])
    return pd.read_csv(io.StringIO(body.rsplit("\nend data", 1)[0]), low_memory=False), meta


def _station_height(metas) -> float:
    hs = {float(m["height"][0]) for m in metas}
    if len(hs) != 1:
        raise ValueError(f"MIDAS station height differs between files: {sorted(hs)}")
    return hs.pop()


def midas_daily_pm(station_dir: Path, lat_deg: float) -> pd.DataFrame:
    """Daily FAO-56 Penman-Monteith (mm/day) and its inputs, from the MIDAS hourly records."""
    files = sorted((station_dir / "hourly_weather").glob("*qcv-1_*.csv.gz"))
    cols = ["ob_time", "wind_speed", "air_temperature", "dewpoint", "stn_pres", "wmo_hr_sun_dur", "drv_hr_sun_dur"]
    parsed = [_badc(f) for f in files]
    h = pd.concat([b[cols] for b, _ in parsed])
    elev = _station_height([m for _, m in parsed])
    h["t"] = pd.to_datetime(h.ob_time)
    # 1980-2001 carry two message types per hour: the first non-missing value of each field per hour
    h = h.drop(columns="ob_time").groupby("t").first().sort_index()
    h["sun"] = h.wmo_hr_sun_dur.fillna(h.drv_hr_sun_dur)
    g = h.resample("D")
    day = pd.DataFrame({"tx": g.air_temperature.max(), "tn": g.air_temperature.min(), "nT": g.air_temperature.count(),
                        "td": g.dewpoint.mean(), "nD": g.dewpoint.count(),
                        "u10": g.wind_speed.mean() * KNOT_MS, "nU": g.wind_speed.count(),
                        "p": g.stn_pres.mean() / HPA_KPA, "sun": g.sun.sum(min_count=MIDAS_DAY_MIN_HOURS)})
    dew_years = range(MIDAS_DEWPOINT_3HOURLY_YEARS[0], MIDAS_DEWPOINT_3HOURLY_YEARS[1] + 1)
    ok_t = day.nT >= MIDAS_DAY_MIN_HOURS
    ok_d = day.nD >= np.where(day.index.year.isin(dew_years), MIDAS_DEWPOINT_3HOURLY_MIN, MIDAS_DAY_MIN_HOURS)
    ok_u = day.nU >= MIDAS_DAY_MIN_HOURS
    day.loc[~ok_t, ["tx", "tn"]] = np.nan
    day.loc[~ok_d, "td"] = np.nan
    day.loc[~ok_u, "u10"] = np.nan
    day["p"] = day.p.fillna(P_SEA_KPA * ((T_REF_K - LAPSE * elev) / T_REF_K) ** P_EXP)
    # radiation: hourly records only (ob_hour_count 1), kJ m-2 per hour, the hour ENDING at ob_end_time
    rfiles = sorted((station_dir / "radiation").glob("*qcv-1_*.csv.gz"))
    r = pd.concat([_badc(f)[0][["ob_end_time", "ob_hour_count", "glbl_irad_amt"]] for f in rfiles])
    r = r[r.ob_hour_count == 1].copy()
    r["t"] = pd.to_datetime(r.ob_end_time) - pd.Timedelta(minutes=1)
    r = r.drop_duplicates("t").set_index("t").glbl_irad_amt
    rg = r.resample("D")
    day["Rs_meas"] = (rg.sum(min_count=1) / KJ_MJ).where(rg.count() >= MIDAS_RAD_MIN_HOURS)
    doy = day.index.dayofyear.values
    ra, n_day = extraterrestrial(doy, lat_deg)
    day["Rs_ang"] = (ANG_A + ANG_B * (day.sun / n_day).clip(0, 1)) * ra
    # before hourly sunshine, the month's sunshine fraction from RAF_Valley_Climate.csv
    msun = read_raf_monthly()["sun"]
    n_month = pd.Series(n_day, index=day.index).resample("MS").sum()
    frac = (msun / n_month.reindex(msun.index)).clip(0, 1)
    day["Rs_monthsun"] = (ANG_A + ANG_B * frac.reindex(day.index.to_period("M").to_timestamp()).values) * ra
    day["Rs"] = day.Rs_meas.fillna(day.Rs_ang).fillna(day.Rs_monthsun)
    day["Rs_src"] = np.where(day.Rs_meas.notna(), "measured", np.where(day.Rs_ang.notna(), "hourly sunshine",
                             np.where(day.Rs_monthsun.notna(), "monthly sunshine", "")))
    tm = (day.tx + day.tn) / 2
    e_s = (es(day.tx) + es(day.tn)) / 2
    e_a = es(day.td)
    dl = _delta(tm)
    gam = GAMMA_P * day.p
    rso = (RSO_A + RSO_B * elev) * ra
    rnl = SIGMA * ((day.tx + KELVIN) ** 4 + (day.tn + KELVIN) ** 4) / 2 * (RNL_A - RNL_B * np.sqrt(e_a.clip(lower=0))) \
        * (RNL_C * (day.Rs / rso).clip(RS_RSO_FLOOR, 1) - RNL_D)
    rn = (1 - ALBEDO) * day.Rs - rnl
    u2 = day.u10 * WIND_LOG_A / np.log(WIND_LOG_B * MIDAS_ANEMOMETER_HEIGHT_M - WIND_LOG_C)

    def pm(u, ea_):
        return ((LAMBDA_INV * dl * rn + gam * PM_CN / (tm + PM_T_K) * u * (e_s - ea_))
                / (dl + gam * (1 + PM_CD * u))).clip(lower=0)

    day["u2"] = u2
    day["ea"] = e_a
    day["pm"] = pm(u2, e_a)
    day["pm_wind_clim"] = pm(u2.groupby(u2.index.dayofyear).transform("mean"), e_a)
    day["pm_hum_clim"] = pm(u2, e_a.groupby(e_a.index.dayofyear).transform("mean"))
    return day


def midas_monthly_pm(station_dir: Path, lat_deg: float, thornthwaite: pd.Series) -> tuple[pd.DataFrame, int]:
    """Monthly Penman-Monteith (m/month) on the months of `thornthwaite` (the span to use), with the
    decomposition runs, mean wind at 2 m, mean vapour pressure and the radiation source counts.

    A month needs MIDAS_MONTH_MIN_DAYS valid days; an isolated missing month is filled from that calendar
    month's median PM/Thornthwaite ratio. Returns the frame and the number of months filled."""
    day = midas_daily_pm(station_dir, lat_deg)

    def monthly(c):
        m = day[c].resample("MS")
        return (m.mean() * m.size()).where(m.count() >= MIDAS_MONTH_MIN_DAYS) / MM_M

    mon = pd.DataFrame({c: monthly(c) for c in ("pm", "pm_wind_clim", "pm_hum_clim")})
    mon["u2_ms"] = day.u2.resample("MS").mean()
    mon["td_c"] = day.td.resample("MS").mean()
    mon["tn_c"] = day.tn.resample("MS").mean()
    mon["p_kpa"] = day.p.resample("MS").mean()
    mon["ea_kpa"] = day.ea.resample("MS").mean()
    for src in ("measured", "hourly sunshine", "monthly sunshine"):
        mon[f"rs_days_{src.replace(' ', '_')}"] = (day.Rs_src == src).resample("MS").sum()
    mon = mon.reindex(thornthwaite.index)
    mon["thornthwaite"] = thornthwaite
    n_filled = int(mon.pm.isna().sum())
    for c in ("pm", "pm_wind_clim", "pm_hum_clim"):
        ratio = (mon[c] / mon.thornthwaite).groupby(mon.index.month).transform("median")
        mon[c] = mon[c].fillna(mon.thornthwaite * ratio)
    return mon, n_filled


def midas_span(station_dir: Path) -> tuple[str, str]:
    """First and last month the hourly weather covers, as YYYY-MM-01, from the capability file's own
    date_valid header (never typed)."""
    f = sorted((station_dir / "hourly_weather").glob("*capability*.csv.gz"))[0]
    for line in gzip.open(f, "rt", encoding="utf-8", errors="replace").read().splitlines():
        p = line.split(",")
        if p[0] == "date_valid" and len(p) >= 4:
            return tuple(pd.Timestamp(x).to_period("M").to_timestamp().strftime("%Y-%m-%d") for x in p[2:4])
    raise ValueError(f"no date_valid in {f}")
