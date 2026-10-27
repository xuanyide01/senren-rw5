"""Bind the native test to the package actually installed, without clearing data."""
from pathlib import Path
import subprocess,json,hashlib,zipfile
R=Path(__file__).resolve().parents[1];P=R/'dist/com.codex.senren.rw5.debug.0.1.9.rpk';O=R/'reports/installed-v019';O.mkdir(exist_ok=True)
ADB='D:/codex/2026-10-08/zhe/work/starry-rw5/node_modules/@miwt/adb/bin/win/adb.exe'
def adb(*args):return subprocess.check_output([ADB,'-s','emulator-5564',*args],stderr=subprocess.STDOUT)
adb('wait-for-device');rows=[]
with zipfile.ZipFile(P)as z:
    names=['pages/index/index.js','manifest-watch.json','common/title_bg.png','common/title_panel.png','common/title_logo.png','common/title_divider.png','common/title-original.opus','common/opening/frames/0000.jpg','common/opening/frames/0324.jpg','common/opening/frames/0647.jpg','common/opening/op.mp3']
    for name in names:
        dest=O/name;dest.parent.mkdir(parents=True,exist_ok=True)
        adb('pull','/data/app/com.codex.senren.rw5/'+name,str(dest))
        assert dest.read_bytes()==z.read(name),name;rows.append(name)
report=dict(result='passed',version='0.1.9',sha256=hashlib.sha256(P.read_bytes()).hexdigest(),installedFilesMatchPackage=rows,physicalDeviceTested=False)
(R/'reports/installed-final.json').write_text(json.dumps(report,indent=2),'utf8');print(json.dumps(report))
