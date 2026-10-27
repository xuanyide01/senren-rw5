from pathlib import Path
import json,io,zipfile,re
from PIL import Image
from fontTools.ttLib import TTFont
from rpk_signature import audit
r=Path(__file__).resolve().parents[1];m=json.loads((r/'src/manifest.json').read_text('utf8'));p=r/'dist'/f'{m["package"]}.debug.{m["versionName"]}.rpk';report=audit(p);assert report['bytes']<25000000
z=zipfile.ZipFile(p);assert json.loads(z.read('manifest-watch.json'))==m;assert m['name']=='千恋万花';images=0
for name in z.namelist():
 if name.endswith('/'):continue
 if name.startswith('common/'):assert z.read(name)==(r/'src'/name).read_bytes(),name
 if name.lower().endswith(('.png','.jpg')):
  im=Image.open(io.BytesIO(z.read(name)));im.load();images+=1
  assert (im.size==(224,126) if name.startswith('common/opening/') else im.width<=432 and im.height<=286),(name,im.size)
icon=Image.open(io.BytesIO(z.read('common/logo.png')));assert icon.size==(192,192)and icon.mode=='RGBA';assert all(icon.getpixel(q)[3]==0 for q in [(0,0),(191,0),(0,191),(191,191)])
font=TTFont(io.BytesIO(z.read('common/senren-text.otf'))).getBestCmap();strings=[]
def visit(v):
 if isinstance(v,str):strings.append(v)
 elif isinstance(v,list):
  for x in v:visit(x)
 elif isinstance(v,dict):
  for x in v.values():visit(x)
for n in z.namelist():
 if n.startswith('common/')and n.endswith('.txt'):visit(json.loads(z.read(n)))
for s in strings:assert all(c.isspace()or ord(c)<32 or ord(c)in font or c=='\ufeff' for c in s),repr(s)
rows=json.loads(z.read('common/gallery.txt'));report.update(commonFilesMatchSource=True,decodedImages=images,fontCoverageStrings=len(strings),circularIcon=True,galleryGroups=len(rows),galleryImages=sum(len(g['variants'])for g in rows),physicalDeviceTested=False)
(r/'reports/package-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8');print(json.dumps(report,ensure_ascii=False))
