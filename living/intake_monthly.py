#!/usr/bin/env python3
"""
Newborough monthly intake
=========================
Take a month's dipwell readings from EITHER the field logger
(well-levels-YYYY-MM.csv) OR the existing recordsheet (recordsheet.ods) and
write them into the master records workbook, preserving its formulas and charts.

For each well it computes, from the master's own geometry:
    water-table elevation (m AOD)  wte = pipe_top_elev - depth
    depth from surface             dfs = upstand - depth     (negative = below ground)
and writes a new dated column into  measured / Absolute Level / depth from surface
via LibreOffice (UNO).  It works on a COPY, never the original, and writes a
QA summary listing anything that needs review.

Date handling (Option A): the column carries the actual reading date; month
allocation downstream uses the field rule (day > 15 -> that month, else previous).

Usage:
    intake_monthly.py --master MASTER.ods --logger well-levels-2026-06.csv
    intake_monthly.py --master MASTER.ods --recordsheet recordsheet.ods --month 2026-05
"""
import argparse, os, re, sys, math, subprocess, time, datetime as dt
import pandas as pd

NORM = lambda s: re.sub(r'[^a-z0-9]', '', str(s).strip().lower().split('/')[0])

def bucket_month(d):
    """Field rule: day>15 -> that month; day<=15 -> previous month. Returns 'YYYY-MM'."""
    d = pd.to_datetime(d)
    y, m = d.year, d.month
    if d.day <= 15:
        m -= 1
        if m == 0:
            m, y = 12, y - 1
    return f"{y:04d}-{m:02d}"

def _num(v):
    try:
        f = float(v); return f if math.isfinite(f) else None
    except (TypeError, ValueError):
        return None

# ───────────────────────── master ─────────────────────────
def load_master(path):
    xl = pd.ExcelFile(path, engine='odf')
    meas = xl.parse('measured', header=None)
    al   = xl.parse('Absolute Level', header=None)
    dfs  = xl.parse('depth from surface', header=None)

    geom = {}
    for ri in range(len(meas)):
        w = NORM(meas.iat[ri, 10])
        if not w or w == 'nan' or w in geom:
            continue
        geom[w] = dict(ground=_num(meas.iat[ri, 4]),
                       upstand=_num(meas.iat[ri, 5]),
                       pipe=_num(meas.iat[ri, 6]))

    def rowmap(df, cols):
        rm = {}
        for ri in range(2, len(df)):
            for c in cols:
                k = NORM(df.iat[ri, c])
                if k and k != 'nan' and k not in rm:
                    rm[k] = ri
        return rm

    rows = dict(measured=rowmap(meas, [10]), al=rowmap(al, [0, 1]), dfs=rowmap(dfs, [0, 1]))

    def last_date_col(df, start):
        last = start - 1
        for c in range(start, df.shape[1]):
            v = df.iat[1, c]
            if pd.notna(v):
                try:
                    pd.to_datetime(v); last = c
                except Exception:
                    pass
        return last

    lastcol = dict(measured=last_date_col(meas, 11),
                   al=last_date_col(al, 2),
                   dfs=last_date_col(dfs, 2))

    prev_wte = {}
    lc = lastcol['al']
    for w, ri in rows['al'].items():
        v = _num(al.iat[ri, lc])
        if v is not None:
            prev_wte[w] = v

    return dict(geom=geom, rows=rows, lastcol=lastcol, prev_wte=prev_wte)

# ───────────────────────── input adapters ─────────────────────────
def read_logger(path):
    df = pd.read_csv(path)
    cols = {c.lower(): c for c in df.columns}
    def col(*names):
        for n in names:
            if n in cols: return cols[n]
        return None
    c_id = col('wellid', 'well', 'id'); c_d = col('depth_m', 'depth')
    c_w = col('wte_maod', 'wte'); c_dt = col('date', 'datedisplay')
    out = {}
    for _, r in df.iterrows():
        w = NORM(r[c_id]); depth = _num(r[c_d])
        if not w or depth is None: continue
        out[w] = dict(depth=depth, wte_logger=_num(r[c_w]) if c_w else None,
                      date=r[c_dt] if c_dt else None, raw=str(r[c_id]).strip())
    dates = [pd.to_datetime(v['date']) for v in out.values() if v['date']]
    coldate = max(dates) if dates else None
    return out, coldate

def read_recordsheet(path, target_month):
    d = pd.read_excel(path, engine='odf', sheet_name='Sheet1', header=None)
    col, coldate = None, None
    for c in range(1, d.shape[1]):
        v = d.iat[0, c]
        if pd.isna(v): continue
        try:
            if bucket_month(v) == target_month:
                col, coldate = c, pd.to_datetime(v); break
        except Exception:
            pass
    if col is None:
        return {}, None
    out = {}
    for ri in range(1, len(d)):
        w = NORM(d.iat[ri, 0])
        if not w or w == 'nan': continue
        cm = _num(d.iat[ri, col])
        if cm is None: continue
        out[w] = dict(depth=cm / 100.0, wte_logger=None, date=coldate, raw=str(d.iat[ri, 0]).strip())
    return out, coldate

# ───────────────────────── compute + QA ─────────────────────────
def compute(master, readings, tol, outlier):
    geom, prev = master['geom'], master['prev_wte']
    vals = {}          # well -> dict(depth, wte, dfs)
    qa = dict(unmatched=[], no_geometry=[], crosscheck=[], outliers=[])
    for w, r in readings.items():
        g = geom.get(w)
        if g is None:
            qa['unmatched'].append(r['raw']); continue
        if g['pipe'] is None or g['upstand'] is None:
            qa['no_geometry'].append(r['raw']); continue
        depth = r['depth']
        wte = round(g['pipe'] - depth, 3)
        dfs = round(g['upstand'] - depth, 3)
        vals[w] = dict(depth=round(depth, 3), wte=wte, dfs=dfs, raw=r['raw'])
        if r['wte_logger'] is not None and abs(wte - r['wte_logger']) > tol:
            qa['crosscheck'].append((r['raw'], wte, r['wte_logger'], round(wte - r['wte_logger'], 3)))
        if w in prev and abs(wte - prev[w]) > outlier:
            qa['outliers'].append((r['raw'], prev[w], wte, round(wte - prev[w], 3)))
    read_wells = set(readings)
    qa['missing'] = sorted(w for w in master['rows']['al'] if w not in read_wells)
    return vals, qa

def write_qa(qa, path, month, coldate, n_written):
    L = [f"# Intake QA — {month}", "",
         f"Reading date in column: **{coldate.date() if coldate is not None else 'n/a'}**",
         f"Wells written: **{n_written}**", ""]
    def sec(title, items, fmt):
        L.append(f"## {title} ({len(items)})")
        L.extend(fmt(x) for x in items) if items else L.append("_none_")
        L.append("")
    sec("Unmatched — in input, no master row (add these)", qa['unmatched'], lambda x: f"- {x}")
    sec("No geometry in master (cannot compute)", qa['no_geometry'], lambda x: f"- {x}")
    sec("Cross-check fails (computed wte vs logger wte > tol)", qa['crosscheck'],
        lambda x: f"- {x[0]}: computed {x[1]}  logger {x[2]}  diff {x[3]} m")
    sec("Outliers (month-over-month change beyond threshold)", qa['outliers'],
        lambda x: f"- {x[0]}: {x[1]} -> {x[2]} m (change {x[3]} m)")
    sec("Master wells with no reading this month", qa['missing'], lambda x: f"- {x}")
    open(path, 'w').write("\n".join(L))

# ───────────────────────── LibreOffice (UNO) write ─────────────────────────
def uno_write(master_path, out_path, master, vals, coldate, port=2002):
    import uno
    from com.sun.star.beans import PropertyValue
    profile = 'file:///tmp/nw_lo_profile'
    proc = subprocess.Popen(
        ['soffice', '--headless', '--norestore', '--nologo', '--invisible',
         '--nofirststartwizard', '-env:UserInstallation=' + profile,
         f'--accept=socket,host=127.0.0.1,port={port};urp;StarOffice.ServiceManager'],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    local = uno.getComponentContext()
    resolver = local.ServiceManager.createInstanceWithContext(
        "com.sun.star.bridge.UnoUrlResolver", local)
    ctx = None
    for _ in range(60):
        try:
            ctx = resolver.resolve(
                f"uno:socket,host=127.0.0.1,port={port};urp;StarOffice.ComponentContext"); break
        except Exception:
            time.sleep(0.5)
    if ctx is None:
        raise RuntimeError("Could not connect to LibreOffice")
    smgr = ctx.ServiceManager
    desktop = smgr.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
    def pv(n, v):
        p = PropertyValue(); p.Name = n; p.Value = v; return p
    doc = desktop.loadComponentFromURL("file://" + os.path.abspath(master_path),
                                        "_blank", 0, (pv("Hidden", True),))
    try:
        sheets = doc.Sheets
        iso = coldate.strftime('%Y-%m-%d') if coldate is not None else dt.date.today().isoformat()
        plan = [('measured', 'measured', master['lastcol']['measured'] + 1, 'depth'),
                ('Absolute Level', 'al', master['lastcol']['al'] + 1, 'wte'),
                ('depth from surface', 'dfs', master['lastcol']['dfs'] + 1, 'dfs')]
        for sheet_name, key, newcol, field in plan:
            sh = sheets.getByName(sheet_name)
            sh.getCellByPosition(newcol, 1).setString(iso)        # date header in row 1
            rmap = master['rows'][key]
            for w, v in vals.items():
                ri = rmap.get(w)
                if ri is None: continue
                sh.getCellByPosition(newcol, ri).setValue(v[field])
        doc.calculateAll()
        doc.storeToURL("file://" + os.path.abspath(out_path), (pv("FilterName", "calc8"),))
    finally:
        doc.close(False)
        try: desktop.terminate()
        except Exception: pass

# ───────────────────────── main ─────────────────────────
def main():
    ap = argparse.ArgumentParser(description="Newborough monthly intake")
    ap.add_argument('--master', required=True)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument('--logger', help='well-levels-YYYY-MM.csv from the field logger')
    src.add_argument('--recordsheet', help='recordsheet.ods (cm readings)')
    ap.add_argument('--month', help='YYYY-MM (required for --recordsheet; for --logger, derived if omitted)')
    ap.add_argument('--tolerance', type=float, default=0.005, help='logger cross-check tolerance, m')
    ap.add_argument('--outlier', type=float, default=0.5, help='month-over-month outlier flag, m')
    ap.add_argument('--outdir', default='.')
    args = ap.parse_args()

    master = load_master(args.master)

    if args.logger:
        readings, coldate = read_logger(args.logger)
        month = args.month or (bucket_month(coldate) if coldate is not None else None)
    else:
        if not args.month:
            ap.error("--month YYYY-MM is required with --recordsheet")
        readings, coldate = read_recordsheet(args.recordsheet, args.month)
        month = args.month
        if not readings:
            print(f"No recordsheet column buckets to {args.month}"); sys.exit(2)

    vals, qa = compute(master, readings, args.tolerance, args.outlier)

    os.makedirs(args.outdir, exist_ok=True)
    base = os.path.splitext(os.path.basename(args.master))[0]
    out_ods = os.path.join(args.outdir, f"{base}_{month}_intake.ods")
    out_qa  = os.path.join(args.outdir, f"intake_QA_{month}.md")

    uno_write(args.master, out_ods, master, vals, coldate)
    write_qa(qa, out_qa, month, coldate, len(vals))

    print(f"  wrote {len(vals)} wells for {month} (column date {coldate.date() if coldate is not None else 'n/a'})")
    print(f"  -> {out_ods}")
    print(f"  -> {out_qa}")
    for k in ('unmatched', 'no_geometry', 'crosscheck', 'outliers'):
        if qa[k]:
            print(f"  ! {len(qa[k])} {k} — see QA")

if __name__ == '__main__':
    main()
