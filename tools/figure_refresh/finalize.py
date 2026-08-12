import os,json,zipfile,struct,hashlib
from lxml import etree
NRG=os.path.expanduser("~/mnt/NRG")
NS={'draw':'urn:oasis:names:tc:opendocument:xmlns:drawing:1.0','xlink':'http://www.w3.org/1999/xlink'}
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
    if b[:8]==b'\x89PNG\r\n\x1a\n': return list(struct.unpack('>II',b[16:24]))
    if b[:2]==b'\xff\xd8': 
        d=jpg_dims(b); return list(d) if d else None
    return None
def imglist(odt):
    z=zipfile.ZipFile(os.path.join(NRG,odt)); root=etree.fromstring(z.read('content.xml'))
    return [im.get(q('xlink:href')) for im in root.iter(q('draw:image')) if 'Pictures/' in (im.get(q('xlink:href')) or '')], z

os.makedirs("/tmp/figref/final",exist_ok=True)
plans=json.load(open("/tmp/figref/plans.json"))

def make(odt, idx_src):
    hrefs,z=imglist(odt)
    out=[]
    for idx,src in idx_src.items():
        href=hrefs[idx]; eb=z.read(href); sb=open(os.path.join(NRG,src),'rb').read()
        ed=dims(eb); sd=dims(sb)
        adj = bool(ed and sd and abs(ed[0]/ed[1]-sd[0]/sd[1])>0.02)
        out.append({"idx":idx,"href":href,"src":src,"emb_dim":ed,"src_dim":sd,"adjust_height":adj})
    return out

SMALL={
 "report_edits/odt/report7.odt":{1:"outputs/13_figure_experimental_design/13_01_experimental_setup_map.png"},
 "report_edits/odt/report8.odt":{0:"outputs/01_data_prep/01_coverage_states_reference.png",1:"outputs/01_data_prep/01_coverage_states_extended.png"},
 "report_edits/odt/report10.odt":{0:"outputs/14_climate_projections/14b_year_of_crossing.png",1:"outputs/21_forestry_scenarios/21_forestry_01_hydrograph.png",4:"outputs/11b_spatial_thresholds/11c_pflood_achievability.png"},
 "docs/academic_summaries/academic_Summary_v1_4.odt":{3:"outputs/20_spatial_figures/20_msl5_change_2017_2023.png"},
}
final={}
for odt,m in SMALL.items():
    final[odt]=make(odt,m)
# report9 from plans.json swaps (already have href,src,aspect_change)
r9=[]
for s in plans["report9.odt"]["swaps"]:
    r9.append({"idx":s["idx"],"href":s["href"],"src":s["src"],"emb_dim":s["emb_dim"],"src_dim":s["src_dim"],"adjust_height":bool(s["aspect_change"])})
final["report_edits/odt/report9.odt"]=r9
for odt,sw in final.items():
    key=os.path.basename(odt)
    json.dump({"odt":odt,"swaps":sw}, open(f"/tmp/figref/final/{key}.json","w"), indent=1)
    nadj=sum(1 for x in sw if x["adjust_height"])
    print(f"{key}: {len(sw)} swaps, {nadj} height-adjust")
