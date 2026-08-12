import os,sys,json,zipfile,re,hashlib,subprocess,shutil
from lxml import etree
NRG=os.path.expanduser("~/mnt/NRG")
spec=json.load(open(sys.argv[1])); out=sys.argv[2]
odt=spec["odt"]; swaps=spec["swaps"]
src_odt=os.path.join(NRG,odt)
zin=zipfile.ZipFile(src_odt)
orig={info.filename: zin.read(info.filename) for info in zin.infolist()}
names=[info.filename for info in zin.infolist()]
assert names[0]=='mimetype', "mimetype not first in original: %s"%names[0]
href2src={s["href"]:os.path.join(NRG,s["src"]) for s in swaps}
# sanity: hrefs exist uniquely
content=orig['content.xml'].decode('utf-8')
for s in swaps:
    assert s["href"] in orig, "missing entry %s"%s["href"]
    assert content.count('xlink:href="%s"'%s["href"])==1, "href not unique in content.xml: %s"%s["href"]
# frame-height recompute for adjust swaps
adjusted=[]
for s in swaps:
    if not s.get("adjust_height"): continue
    href=s["href"]; sd=s["src_dim"]
    if not sd: continue
    marker='xlink:href="%s"'%href
    mi=content.index(marker)
    fs=content.rfind('<draw:frame', 0, mi)
    fe=content.index('>', fs)
    tag=content[fs:fe+1]
    mw=re.search(r'svg:width="([0-9.]+)([a-z]*)"',tag); mh=re.search(r'svg:height="([0-9.]+)([a-z]*)"',tag)
    assert mw and mh, "no w/h in frame for %s: %s"%(href,tag[:120])
    w=float(mw.group(1)); unit=mw.group(2)
    newh=w*sd[1]/sd[0]
    newtag=tag[:mh.start()]+'svg:height="%.3f%s"'%(newh,mh.group(2))+tag[mh.end():]
    content=content[:fs]+newtag+content[fe+1:]
    adjusted.append((href, mh.group(0), 'svg:height="%.3f%s"'%(newh,mh.group(2))))
content_b=content.encode('utf-8')
# build new zip
if os.path.exists(out): os.remove(out)
zout=zipfile.ZipFile(out,'w')
mi=zipfile.ZipInfo('mimetype'); mi.compress_type=zipfile.ZIP_STORED
zout.writestr(mi, orig['mimetype'])
for info in zin.infolist():
    fn=info.filename
    if fn=='mimetype': continue
    if fn=='content.xml': data=content_b
    elif fn in href2src: data=open(href2src[fn],'rb').read()
    else: data=orig[fn]
    zout.writestr(info, data, compress_type=info.compress_type)
zout.close()
# ---- verify ----
zc=zipfile.ZipFile(out); ci=zc.infolist()
assert ci[0].filename=='mimetype' and ci[0].compress_type==zipfile.ZIP_STORED, "mimetype not first/stored"
assert zc.read('mimetype')==b'application/vnd.oasis.opendocument.text', "bad mimetype bytes"
etree.fromstring(zc.read('content.xml'))  # well-formed
changed=set()
for s in swaps:
    exp=hashlib.sha1(open(href2src[s['href']],'rb').read()).hexdigest()
    got=hashlib.sha1(zc.read(s['href'])).hexdigest()
    assert exp==got, "swap mismatch %s"%s['href']
    changed.add(s['href'])
changed.add('content.xml')
for info in zin.infolist():
    fn=info.filename
    if fn in changed or fn=='mimetype': continue
    assert hashlib.sha1(zc.read(fn)).hexdigest()==hashlib.sha1(orig[fn]).hexdigest(), "unexpected change %s"%fn
# content.xml diff sanity: if no adjust, identical
if not adjusted:
    assert zc.read('content.xml')==orig['content.xml'], "content.xml changed unexpectedly"
print("BUILD+HASH VERIFY OK: swaps=%d adjusted=%d bytes_in=%d bytes_out=%d"%(len(swaps),len(adjusted),os.path.getsize(src_odt),os.path.getsize(out)))
for a in adjusted: print("   height:",a[0][-24:],a[1],"->",a[2])
# soffice open-test
if os.environ.get("FIGREF_NO_SOFFICE"):
    print("SOFFICE SKIPPED (build+hash verified)"); sys.exit(0)
tmpd="/tmp/figref/soffice_%s"%os.path.basename(out); os.makedirs(tmpd,exist_ok=True)
r=subprocess.run(["soffice","--headless","--convert-to","pdf","--outdir",tmpd,out],capture_output=True,timeout=600)
pdf=os.path.join(tmpd,os.path.splitext(os.path.basename(out))[0]+".pdf")
ok=os.path.exists(pdf) and os.path.getsize(pdf)>1000
print("SOFFICE OPEN:", "OK pdf=%d bytes"%os.path.getsize(pdf) if ok else "FAILED\n"+r.stderr.decode()[:500])
sys.exit(0 if ok else 2)
