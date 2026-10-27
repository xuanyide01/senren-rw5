"""Move expression patches into 256x256 palette atlases (adult build)."""
from pathlib import Path
from PIL import Image
import json
import os

PORT = Path(__file__).resolve().parents[1]
SOURCE = PORT / 'src/common/images'
DEST = PORT / 'src/common/faces'
DEST.mkdir(exist_ok=True)
mpath = PORT / 'converted/image-map.json'
m = json.loads(mpath.read_text('utf8'))
backup = PORT / 'reports/image-map-before-atlas.json'
if backup.exists():
    raise RuntimeError('Expression atlases already prepared; do not pack twice')
backup.write_text(json.dumps(m, ensure_ascii=False, separators=(',', ':')), 'utf8')

for old in DEST.rglob('*'):
    if old.is_file():
        old.unlink()

patches = sorted({v['patch'] for v in m.values() if v.get('patch')})
translation = {}
atlas_count = 0
before = 0
after = 0
for start in range(0, len(patches), 4):
    canvas = Image.new('RGBA', (256, 256))
    for i, src in enumerate(patches[start:start + 4]):
        p = PORT / 'src' / src.lstrip('/')
        im = Image.open(p).convert('RGBA')
        assert im.width <= 128 and im.height <= 128
        x = (i % 2) * 128
        y = (i // 2) * 128
        canvas.paste(im, (x, y))
        before += p.stat().st_size
        translation[src] = {'atlas': f'/common/faces/{atlas_count // 48:02d}/{atlas_count % 48:02d}.png',
                            'rect': [x, y, im.width, im.height]}
    p = DEST / f'{atlas_count // 48:02d}/{atlas_count % 48:02d}.png'
    p.parent.mkdir(exist_ok=True)
    canvas.quantize(colors=int(os.environ.get('SENREN_ATLAS_COLORS', '256')), method=Image.Quantize.FASTOCTREE).save(p, optimize=True)
    after += p.stat().st_size
    atlas_count += 1

for v in m.values():
    if v.get('patch'):
        t = translation[v['patch']]
        v['patch'] = t['atlas']
        v['patchAtlas'] = [256, 256, t['rect'][0], t['rect'][1]]
mpath.write_text(json.dumps(m, ensure_ascii=False, separators=(',', ':')), 'utf8')

other = {v['src'] for v in m.values()}
for src in patches:
    if src in other:
        continue
    p = (PORT / 'src' / src.lstrip('/')).resolve()
    assert p.is_relative_to(SOURCE.resolve())
    p.unlink()

report = {'expressions': len(patches), 'atlases': atlas_count, 'pixelIdenticalTiles': False,
          'paletteColors': int(os.environ.get('SENREN_ATLAS_COLORS', '256')), 'atlasSize': [256, 256], 'beforeBytes': before, 'afterBytes': after}
(PORT / 'reports/expression-atlases.json').write_text(json.dumps(report, indent=2), 'utf8')
print(json.dumps(report))
