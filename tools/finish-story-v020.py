"""Write runtime story chunks and graph.js from the compiled adult graph (0.1.9 chunk format)."""
import json
import os
from pathlib import Path

PORT = Path(__file__).resolve().parents[1]
D = PORT / 'src/common/story'
D.mkdir(parents=True, exist_ok=True)
graph = json.loads((PORT / 'converted/graph.json').read_text('utf8'))
images = json.loads((PORT / 'converted/image-map.json').read_text('utf8'))


def dump(x):
    return json.dumps(x, ensure_ascii=False, separators=(',', ':'))


for old in D.rglob('*'):
    if old.is_file():
        old.unlink()

missing = []
count = 0
largest = 0
chunks = 0

for key, n in graph['nodes'].items():
    raw = json.loads((PORT / 'converted' / (key + '.json')).read_text('utf8'))
    frames = []
    for f in raw:
        if f.get('kind') == 'op':
            frames.append(f)
            continue
        a = f['art']
        bg = images.get(a['background'])
        if not bg:
            missing.append(a['background'])
            continue
        sprites = []
        for s in a['sprites']:
            im = images[s['asset']]
            scale = 310 / 272
            w = round(im['width'] * scale)
            h = 310
            original = {'左': -240, '右': 240, '中': 0, '左中': -180, '右中': 180, '左近': -130,
                        '右近': 130, '左奥': -280, '右奥': 280, '左外': -340, '右外': 340,
                        '左大外': -400, '右大外': 400}
            center = 216 + (original.get(s['position'], 0) + float(s.get('x', 0))) * 432 / 1280
            left = round(center - w / 2)
            top = 0
            v = {'src': im['src'], 'width': w, 'height': h, 'left': left, 'top': top,
                 'opacity': s.get('opacity', 255) / 255}
            if im.get('patch'):
                x, y, pw, ph = im['patchRect']
                v.update(patch=im['patch'], patchWidth=round(pw * scale),
                         patchHeight=round(ph * scale), patchLeft=left + round(x * scale),
                         patchTop=top + round(y * scale))
                atlas = im.get('patchAtlas', [pw, ph, 0, 0])
                v.update(patchAtlasWidth=round(atlas[0] * scale),
                         patchAtlasHeight=round(atlas[1] * scale),
                         patchImageLeft=-round(atlas[2] * scale),
                         patchImageTop=-round(atlas[3] * scale))
            sprites.append(v)
        frames.append({'speaker': f['speaker'], 'text': f['text'],
                       'art': {'background': bg['src'], 'sprites': sprites}})
        count += 1
    n['chunks'] = []
    part = []
    size = 2

    def save():
        global chunks, largest, part, size
        if not part:
            return
        file = f'{chunks // 48:02d}/{chunks % 48:02d}.txt'
        p = D / file
        p.parent.mkdir(exist_ok=True)
        text = dump(part)
        p.write_text(text, 'utf8')
        largest = max(largest, len(text.encode('utf8')))
        n['chunks'].append({'file': file, 'count': len(part)})
        chunks += 1
        part = []
        size = 2

    for f in frames:
        b = len(dump(f).encode('utf8')) + 1
        if size + b > int(os.environ.get('SENREN_CHUNK_BYTES', '24576')):
            save()
        part.append(f)
        size += b
    save()

assert not missing, missing[:5]
(PORT / 'src/common/graph.js').write_text('export const graph=' + dump(graph) + ';\n', 'utf8')
report = {'textRecords': count, 'chunks': chunks, 'maximumChunkBytes': largest,
          'storyBytes': sum(p.stat().st_size for p in D.rglob('*.txt')),
          'graphBytes': (PORT / 'src/common/graph.js').stat().st_size}
(PORT / 'reports/story-final.json').write_text(json.dumps(report, indent=2), 'utf8')
print(json.dumps(report))
