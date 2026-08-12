import os, re, json, zipfile, hashlib
from lxml import etree
NRG=os.path.expanduser("~/mnt/NRG")
DAT=json.load(open("/tmp/figref/figmap.json"))
NS={'draw':'urn:oasis:names:tc:opendocument:xmlns:drawing:1.0','xlink':'http://www.w3.org/1999/xlink','text':'urn:oasis:names:tc:opendocument:xmlns:text:1.0'}
def q(t): p,l=t.split(':'); return '{%s}%s'%(NS[p],l)
odt="report_edits/odt/report9.odt"; key="report9.odt"
z=zipfile.ZipFile(os.path.join(NRG,odt))
root=etree.fromstring(z.read('content.xml'))
srcpath={os.path.basename(s):s for s in DAT[key]}
known=set(srcpath)
srchash={}
for s in DAT[key]:
    full=os.path.join(NRG,s)
    if os.path.exists(full): srchash[hashlib.sha1(open(full,'rb').read()).hexdigest()]=os.path.basename(s)
def jt(el): return re.sub(r'\s+',' ',''.join(el.itertext()))
P=q('text:p')
def near_p(img):
    p=img
    while p is not None and p.tag!=P: p=p.getparent()
    return p
imgs=[im for im in root.iter(q('draw:image')) if 'Pictures/' in (im.get(q('xlink:href')) or '')]
swaps=[]; issues=[]
for i,im in enumerate(imgs):
    href=im.get(q('xlink:href'))
    eh=hashlib.sha1(z.read(href)).hexdigest()
    true=srchash.get(eh)   # basename if this image already == some current source
    p=near_p(im)
    A=[b for b in known if b in jt(p)] if p is not None else []
    status="?"
    if len(A)==1:
        src=A[0]
        if true==src: status="UNCHANGED"
        elif true is None: status="CHANGED->swap"; swaps.append((i,href,srcpath[src]))
        else: status=f"CONFLICT true={true} capA={src}"; issues.append((i,href,status))
    elif len(A)==0:
        status="NO-CAPTION(extra?)"; issues.append((i,href,"A empty; true=%s"%true))
    else:
        status="MULTI:%s"%A; issues.append((i,href,"multi %s; true=%s"%(A,true)))
    print(f"[{i:2}] {href[-16:]} true={true} A={A} => {status}")
print("\n=== SWAPS (changed, unambiguous): %d ==="%len(swaps))
for i,h,s in swaps: print(f"  [{i}] {h[-16:]} <- {s}")
print("\n=== ISSUES: %d ==="%len(issues))
for i,h,s in issues: print(f"  [{i}] {h[-16:]} {s}")
json.dump([{"idx":i,"href":h,"src":s} for i,h,s in swaps], open("/tmp/figref/report9_swaps.json","w"))
