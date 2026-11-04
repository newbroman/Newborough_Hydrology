import csv,re,sys
sys.path.insert(0,'/home/user/Newborough_Hydrology/tools')
from field_convert import field_name
rows={r['field']:r for r in csv.DictReader(open('/home/user/Newborough_Hydrology/tools/number_fields.csv',encoding='utf8'))}
s=open(sys.argv[1],encoding='utf8').read()
bad=[]
def sub(m):
    n=m.group(1)
    r=rows.get(n)
    if not r: bad.append(('missing',n)); return m.group(0)
    spec=[f"dp{r['dp']}"]
    if r['scale'] not in ('','1'): spec.append('x'+r['scale'])
    if r['abs']: spec.append('abs')
    if r['plus']: spec.append('plus')
    if r['minus']=='-': spec.append('hy')
    if r['thousands']: spec.append('th')
    sp=' '.join(spec)
    from field_md_build import spec_of
    if field_name(r['key'],spec_of(sp))!=n: bad.append(('namemismatch',n,field_name(r['key'],spec_of(sp))))
    return f"⟪{r['source_csv']}|{r['key']}|{sp}⟫"
out=re.sub(r'\{\{([^}]+)\}\}',sub,s)
open(sys.argv[2],'w',encoding='utf8').write(out)
print(len(re.findall(r'\{\{',s)),'placeholders;',bad or 'all resolved')
