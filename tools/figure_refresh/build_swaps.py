import os, re, json, zipfile, hashlib, struct
from lxml import etree
NRG=os.path.expanduser("~/mnt/NRG")
DAT=json.load(open("/tmp/figref/figmap.json"))
NS={'draw':'urn:oasis:names:tc:opendocument:xmlns:drawing:1.0','xlink':'http://www.w3.org/1999/xlink','text':'urn:oasis:names:tc:opendocument:xmlns:text:1.0'}
def q(t): p,l=t.split(':'); return '{%s}%s'%(NS[p],l)
def jpg_dims(data):
    i=2
    while i<len(data)-9:
        if data[i]!=0xFF: i+=1; continue
        m=data[i+1]
        if 0xC0<=m<=0xCF and m not in (0xC4,0xC8,0xCC):
            h=struct.unpack('>H',data[i+5:i+7])[0]; w=struct.unpack('>H',data[i+7:i+9])[0]; return (w,h)
        l=struct.unpack('>H',data[i+2:i+4])[0]; i+=2+l
    return None
def dims(b):
    if b[:8]==b'\x89PNG\r\n\x1a\n': return struct.unpack('>II',b[16:24])
    if b[:2]==b'\xff\xd8': return jpg_dims(b)
    return None
TARGETS={"report7.odt":"report_edits/odt/report7.odt","report8.odt":"report_edits/odt/report8.odt",
 "report10.odt":"report_edits/odt/report10.odt","report9.odt":"report_edits/odt/report9.odt",
 "academic_Summary_v1_4.odt":"docs/academic_summaries/academic_Summary_v1_4.odt"}
OVERRIDES={"report9.odt":{
  47:"outputs/07_spatial_coefficients/07_coeff_01_beta1_recharge.png",
  48:"outputs/07_spatial_coefficients/07_coeff_04_r2_quality.png",
  49:"outputs/07_spatial_coefficients/07_coeff_03_beta3_drainage.png",
  50:"outputs/07_spatial_coefficients/07_coeff_02_beta2_atm_draw.png",
}}
def basemap(paths):
    return {os.path.basename(p):p for p in paths}
def jt(el): return re.sub(r'\s+',' ',''.join(el.itertext()))
def build(key):
    odt=TARGETS[key]; z=zipfile.ZipFile(os.path.join(NRG,odt))
    root=etree.fromstring(z.read('content.xml'))
    ov=OVERRIDES.get(key,{})
    pool=basemap(DAT[key]); 
    for p in ov.values(): pool[os.path.basename(p)]=p
    known=set(pool)
    P=q('text:p')
    def near_p(img):
        p=img
        while p is not None and p.tag!=P: p=p.getparent()
        return p
    imgs=[im for im in root.iter(q('draw:image')) if 'Pictures/' in (im.get(q('xlink:href')) or '')]
    swaps=[]; flags=[]; assigned={}
    for i,im in enumerate(imgs):
        href=im.get(q('xlink:href')); eb=z.read(href); eh=hashlib.sha1(eb).hexdigest(); ed=dims(eb)
        if i in ov: src=ov[i]
        else:
            p=near_p(im); A=[pool[b] for b in known if b in jt(p)] if p is not None else []
            if len(A)==1: src=A[0]
            else:
                flags.append((i,href,f"paragraph names {len(A)} sources: {[os.path.basename(a) for a in A]}")); 
                continue
        full=os.path.join(NRG,src); sb=open(full,'rb').read(); sh=hashlib.sha1(sb).hexdigest(); sd=dims(sb)
        assigned.setdefault(src,[]).append(i)
        if eh==sh: continue  # unchanged
        ar_flag=False
        if ed and sd and abs(ed[0]/ed[1]-sd[0]/sd[1])>0.02: ar_flag=True
        swaps.append({"idx":i,"href":href,"src":src,"emb_dim":ed,"src_dim":sd,"aspect_change":ar_flag})
    # duplicate-source guard (two images -> same source)
    dups={s:v for s,v in assigned.items() if len(v)>1}
    return {"key":key,"odt":odt,"n_images":len(imgs),"swaps":swaps,"flags":flags,"dups":dups}
allplans={}
for k in TARGETS:
    pl=build(k); allplans[k]=pl
    print(f"### {k}: images={pl['n_images']} swaps={len(pl['swaps'])} flags={len(pl['flags'])} dup_sources={len(pl['dups'])}")
    asp=[s['idx'] for s in pl['swaps'] if s['aspect_change']]
    if asp: print(f"    aspect-change swaps (frame height will be recomputed): {asp}")
    if pl['flags']:
        for i,h,m in pl['flags']: print(f"    FLAG img[{i}] {h[-14:]}: {m}")
    if pl['dups']:
        for s,v in pl['dups'].items(): print(f"    DUP {os.path.basename(s)} <- images {v}")
json.dump(allplans, open("/tmp/figref/plans.json","w"), indent=0)
print("\nplans.json written")
