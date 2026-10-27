"""Check typing captures and illustrate a conservative rounded-screen mask."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import numpy as np,json
R=Path(__file__).resolve().parents[1];N=R/'native-test-results/0.1.9'
report=json.loads((N/'layout-preparation.json').read_text('utf8'))
times=report['typingCapturesMs'];counts=[];lines=[]
def ink(im):
    a=np.asarray(im.convert('RGB'));return (a[:,:,0]<190)&(a[:,:,1]<160)&(a[:,:,2]<145)
for t in times:
    im=Image.open(N/f'typed-{t:04d}.png');mask=ink(im)
    counts.append(int(mask[328:438,32:400].sum()))
    lines.append([int(mask[328+i*34:362+i*34,32:400].sum())for i in range(3)])
assert len(set(counts))>=3 and counts[-1]>counts[1]*2,(counts,lines)
assert all(x>150 for x in lines[-1]),lines[-1]
mask=Image.new('L',(432,514),0);ImageDraw.Draw(mask).rounded_rectangle((0,0,431,513),radius=80,fill=255)
outside=np.asarray(mask)==0
def clipped(p,reading=False):
    hits=ink(Image.open(p))&outside
    if reading:hits[:286]=False
    return int(hits.sum())
stats={}
for name in ['routes','slots','reading']:
    before=R/'reports/ui-safe-before-v019'/f'{name}.png';after=N/f'safe-{name}.png'
    stats[name]=dict(before=clipped(before,name=='reading'),after=clipped(after,name=='reading'))
assert all(v['after']==0 for v in stats.values()),stats
report.update(result='passed',typingInkCounts=counts,fullTextInkPerLine=lines[-1],typedRowsVisuallyComplete=True,illustrativeRadiusPx=80,cornerTextInk=stats,radiusNote='R80 is a conservative illustrative mask, not a calibration of the physical watch. Art is intentionally full bleed; reading comparison measures only dialogue/control regions.',physicalDeviceTested=False)
(N/'layout.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8')
font=lambda n:ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',n)
canvas=Image.new('RGB',(1424,1220),'#101c1a');d=ImageDraw.Draw(canvas)
d.text((40,22),'《千恋＊万花》· 圆角文字安全区',font=font(30),fill='#e4f3ec')
d.text((40,68),'R80 示意遮罩（非实机标定）；上排调整前，下排调整后',font=font(20),fill='#a3c4b5')
for col,(name,label)in enumerate([('reading','阅读 / 上一句、下一句'),('routes','路线目录 / 标题、翻页'),('slots','存读档 / 标题、翻页')]):
    x=40+col*464;d.text((x,110),label,font=font(19),fill='#82d4b4')
    for row,p in enumerate([R/'reports/ui-safe-before-v019'/f'{name}.png',N/f'safe-{name}.png']):
        im=Image.open(p).convert('RGB');base=Image.new('RGB',im.size,'#000000');base.paste(im,(0,0),mask);canvas.paste(base,(x,148+row*528))
canvas.save(R/'reports/UI-safe-before-after-v019.png')
stages=Image.new('RGB',(1424,650),'#101c1a');d=ImageDraw.Draw(stages)
d.text((40,22),'逐字显示 · 丛雨 CHAPTER 6-2',font=font(28),fill='#e4f3ec')
for col,t in enumerate([180,800,1700]):
    x=40+col*464;d.text((x,72),f'{t} ms',font=font(20),fill='#82d4b4');stages.paste(Image.open(N/f'typed-{t:04d}.png').convert('RGB'),(x,110))
stages.save(R/'reports/Typing-before-completion-v019.png')
print(json.dumps({k:v for k,v in report.items()if k not in ['typingCapturesMs']},ensure_ascii=False))
