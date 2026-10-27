"""Build watch images for the adult build: every CG, including the uncensored originals.

Sources (all read-only):
  BASE/probe/extracted     0.1.9 decoded base assets (backgrounds, faces, censored CG)
  BASE/probe/cg-json       0.1.9 PIMG descriptors
  PROBE/adult              extra PNG/JPG from adult.xp3
  PROBE/adult2, PROBE/cg-json  uncensored PIMG descriptors + layer PNGs from adult2.xp3
"""
from pathlib import Path
from PIL import Image, ImageChops
import json
import re
import hashlib
import io
import os
import sys

PORT = Path(__file__).resolve().parents[1]
BASE = Path(r'D:/codex/2026-10-26/senren-rw5')
PROBE = Path(r'D:/DSH/work/port/probe')
E = BASE / 'probe/extracted'
DEST = PORT / 'src/common/images'
DEST.mkdir(parents=True, exist_ok=True)
assert PORT.name == 'senren-rw5', PORT

# Reuse the 0.1.9 files byte-for-byte: identical renders keep their existing path.
next_serial = 0
bytes_total = 0
byhash = {}
for old in sorted(DEST.rglob('*')):
    if not old.is_file():
        continue
    rel = old.relative_to(DEST).as_posix()
    byhash[hashlib.sha256(old.read_bytes()).hexdigest()] = rel
    bytes_total += old.stat().st_size
    next_serial = max(next_serial, int(old.parent.name) * 48 + int(old.stem) + 1)

req = json.loads((PORT / 'converted/image-requests.json').read_text('utf8'))
portraits = json.loads((PORT / 'reports/portrait-plan.json').read_text('utf8'))
tlg_plan = json.loads((PORT / 'reports/tlg-plan.json').read_text('utf8'))
decoded = {}
for d in tlg_plan:
    decoded[str(Path(d['input']).relative_to(E / 'fgimage'))] = Path(d['output'])

pngs = {}
for folder in ['data', 'bgimage', 'fgimage', 'evimage']:
    for p in (E / folder).rglob('*'):
        if p.suffix.lower() == '.png':
            pngs[p.stem.lower()] = p
for p in (E / 'evimage').rglob('*'):
    if p.suffix.lower() == '.png' and p.stem.lower().endswith('_cn'):
        pngs[p.stem.lower().removesuffix('_cn')] = p
# extra single-image assets shipped only in adult.xp3
for p in (PROBE / 'extracted/adult').rglob('*'):
    if p.suffix.lower() in ('.png', '.jpg'):
        pngs.setdefault(p.stem.lower(), p)

# PIMG descriptors: drop every censored variant, add the uncensored originals, and
# let the loose decensor patch files win over the archive copies with the same name.
pimgs = []
for p in sorted((BASE / 'probe/cg-json').glob('*.json')):
    if '.resx.' in p.name or 'censored' in p.name.lower():
        continue
    pimgs.append((p, json.loads(p.read_text('utf8'))))
for p in sorted((PROBE / 'cg-json').glob('*.json')):
    if '.resx.' in p.name:
        continue
    pimgs.append((p, json.loads(p.read_text('utf8'))))

# exact stem -> rig, later sources overriding earlier ones
rig_by_stem = {}
for path, data in pimgs:
    rig_by_stem[path.stem.lower()] = (path, data)
decensored = 0
for p in sorted((PROBE / 'cg-json-patch').glob('*.json')):
    if '.resx.' in p.name:
        continue
    if p.stem.lower() in rig_by_stem:
        decensored += 1
    rig_by_stem[p.stem.lower()] = (p, json.loads(p.read_text('utf8')))

pimg_index = []
for path, data in pimgs:
    pimg_index.append((path.stem.lower().replace('_', ''), path, data))

layers = {}
mapping = {}
failures = []
groups = {}


def opened(path):
    key = str(path)
    if key not in layers:
        if len(layers) > 160:
            layers.clear()
        layers[key] = Image.open(path).convert('RGBA')
    return layers[key]


def overlay(canvas, part, xy, kind=13, opacity=255):
    if opacity != 255:
        part = part.copy()
        part.putalpha(part.getchannel('A').point(lambda n: n * opacity // 255))
    if kind == 16:
        x, y = xy
        under = canvas.crop((x, y, x + part.width, y + part.height))
        blend = ImageChops.overlay(under.convert('RGB'), part.convert('RGB')).convert('RGBA')
        blend.putalpha(part.getchannel('A'))
        canvas.alpha_composite(blend, xy)
    else:
        canvas.alpha_composite(part, xy)


def portrait(aid):
    plan = portraits[aid]
    selected = []
    for layer in plan['layers']:
        im = opened(decoded[layer['id']])
        selected.append((layer, im))
    box = (min(l['left'] for l, i in selected), min(l['top'] for l, i in selected),
           max(l['left'] + i.width for l, i in selected), max(l['top'] + i.height for l, i in selected))
    height = min(box[3] - box[1], round(plan['canvas'][0] * 2 / 3))
    box = (box[0], box[1], box[2], box[1] + height)
    canvas = Image.new('RGBA', (box[2] - box[0], box[3] - box[1]))
    body = canvas.copy()
    for l, im in selected:
        overlay(canvas, im, (l['left'] - box[0], l['top'] - box[1]), l['type'], l['opacity'])
        if not l['face']:
            overlay(body, im, (l['left'] - box[0], l['top'] - box[1]), l['type'], l['opacity'])
    w = max(1, round(canvas.width * 272 / canvas.height))
    canvas = canvas.resize((w, 272), Image.Resampling.LANCZOS)
    body = body.resize((w, 272), Image.Resampling.LANCZOS)
    diff = ImageChops.difference(canvas, body)
    bands = diff.split()
    mask = bands[0]
    for band in bands[1:]:
        mask = ImageChops.lighter(mask, band)
    patchbox = mask.getbbox()
    patch = canvas.crop(patchbox) if patchbox else None
    return body, patch, patchbox, box


def store(im, fmt):
    global bytes_total, next_serial
    if fmt == 'PNG':
        im = im.quantize(colors=192, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE)
    b = io.BytesIO()
    im.save(b, format=fmt, optimize=True,
            **({'quality': int(os.environ.get('SENREN_JPEG_QUALITY', '36')), 'subsampling': 2} if fmt == 'JPEG' else {}))
    raw = b.getvalue()
    h = hashlib.sha256(raw).hexdigest()
    if h not in byhash:
        n = next_serial
        next_serial += 1
        relative = f'{n // 48:02d}/{n % 48:02d}' + ('.png' if fmt == 'PNG' else '.jpg')
        p = DEST / relative
        p.parent.mkdir(exist_ok=True)
        p.write_bytes(raw)
        byhash[h] = relative
        bytes_total += len(raw)
    return '/common/images/' + byhash[h]


def static(file):
    name = file.lower()
    p = pngs.get(name)
    if name == 'sd203ic':
        return opened(BASE / 'probe/reconstructed/SD203IC.png').copy(), {'source': 'original sd203.mtn, SD203IC first frame'}
    if p:
        return opened(p).copy(), {'source': str(p)}
    if name in ['画面_黒', '暗転', '黒画面']:
        return Image.new('RGBA', (1920, 1080), 'black'), {'source': 'original solid black'}
    if name in ['画面_白', '白画面']:
        return Image.new('RGBA', (1920, 1080), 'white'), {'source': 'original solid white'}
    env = (E / 'data/main/envinit.tjs.utf8.txt').read_text('utf8')
    m = re.search(r'"' + re.escape(name) + r'"[^\n]+altStorage:"([^"]+)"', env, re.I)
    if m and m[1].lower() in pngs:
        return opened(pngs[m[1].lower()]).copy(), {'source': 'original SD altStorage', 'alternative': m[1]}
    prefix = re.match(r'ev\d+', name)
    if not prefix:
        raise ValueError('No original static resource: ' + name)
    # Request names are the PIMG stem plus the layer variant: ev101+aa -> ev101a/Aa.
    # A stem that carries the underscore (ev204_aa) addresses the separate ev204_a
    # rig, which is a different artwork, so resolve the stem exactly instead of
    # guessing by prefix.
    rest = name[len(prefix[0]):]
    if rest.startswith('_'):
        stem_key = (prefix[0] + '_a').lower()
        suffix = rest[1:].lower()
    else:
        stem_key = (prefix[0] + 'a').lower()
        suffix = rest.lower()
    candidates = []
    rig = rig_by_stem.get(stem_key)
    if rig:
        path, data = rig
        for layer in data['layers']:
            if layer.get('layer_type') == 0 and layer.get('name', '').lower() == suffix:
                candidates.append((path, data, layer))
    if not candidates:
        for stem_norm, path, data in pimg_index:
            if path.stem.lower() != stem_key:
                continue
            for layer in data['layers']:
                if layer.get('layer_type') == 0 and layer.get('name', '').lower() == suffix:
                    candidates.append((path, data, layer))
    if not candidates:
        for stem_norm, path, data in pimg_index:
            if not stem_norm.startswith(prefix[0]):
                continue
            for layer in data['layers']:
                if layer.get('layer_type') == 0 and layer.get('name', '').lower() == suffix:
                    candidates.append((path, data, layer))
    if not candidates:
        raise ValueError('No original PIMG layer: ' + name)
    path, data, chosen = candidates[0]
    canvas = Image.new('RGBA', (data['width'], data['height']))
    base_layer = suffix[0] + 'a'
    selected = [l for l in data['layers']
                if l.get('layer_type') == 0 and l.get('name', '').lower() in {base_layer, suffix}]
    selected.sort(key=lambda l: 0 if l['name'].lower() == base_layer else 1)
    for layer in selected:
        lid = layer.get('same_image', layer['layer_id'])
        part = opened(path.parent / path.stem / (str(lid) + '.png'))
        overlay(canvas, part, (layer.get('left', 0), layer.get('top', 0)),
                layer.get('type', 13), layer.get('opacity', 255))
    return canvas, {'source': path.stem, 'layers': [l['layer_id'] for l in selected],
                    'layerNames': [l['name'] for l in selected]}


for i, (aid, v) in enumerate(req.items()):
    try:
        isportrait = v['file'].endswith('.stand')
        if isportrait:
            im, patch, patchbox, box = portrait(aid)
            fmt = 'PNG'
            detail = {'source': 'original stand composition with reusable body and expression patch', 'crop': box}
            if patch is not None:
                detail.update(patch=store(patch, 'PNG'),
                              patchRect=[patchbox[0], patchbox[1], patch.width, patch.height])
        else:
            im, detail = static(v['file'])
            im.thumbnail((432, 286), Image.Resampling.LANCZOS)
            back = Image.new('RGB', im.size, 'white')
            back.paste(im, mask=im.getchannel('A'))
            im = back
            fmt = 'JPEG'
        mapping[aid] = {'src': store(im, fmt), 'width': im.width, 'height': im.height,
                        'portrait': isportrait, 'original': v, **detail}
    except Exception as err:
        failures.append({'asset': aid, 'request': v, 'error': str(err)})
    if i % 500 == 0:
        print('IMAGES', i, len(byhash), bytes_total, flush=True)

(PORT / 'converted/image-map.json').write_text(json.dumps(mapping, ensure_ascii=False, separators=(',', ':')), 'utf8')
(PORT / 'reports/image-failures.json').write_text(json.dumps(failures, ensure_ascii=False, indent=2), 'utf8')

groups = {}
for v in mapping.values():
    if not v['portrait'] and re.match(r'^(ev|sd)\d+', v['original']['file'], re.I):
        key = re.match(r'^((?:ev|sd)\d+)', v['original']['file'], re.I)[1].lower()
        groups.setdefault(key, [])
        if v['src'] not in groups[key]:
            groups[key].append(v['src'])
gallery = [{'label': key.upper(), 'variants': values} for key, values in groups.items()]
(PORT / 'src/common/gallery.txt').write_text(json.dumps(gallery, ensure_ascii=False, separators=(',', ':')), 'utf8')

# Drop files that no request references any more (e.g. the replaced censored CG).
used = {v['src'].replace('/common/images/', '') for v in mapping.values()}
used |= {v['patch'].replace('/common/images/', '') for v in mapping.values() if v.get('patch')}
removed = 0
for p in list(DEST.rglob('*')):
    if p.is_file() and p.relative_to(DEST).as_posix() not in used:
        p.unlink()
        removed += 1

report = {'requested': len(req), 'mapped': len(mapping), 'uniqueFiles': len(byhash),
          'imageBytes': bytes_total, 'unresolved': len(failures), 'galleryGroups': len(gallery),
          'removedUnused': removed}
(PORT / 'reports/images.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), 'utf8')
print(json.dumps(report, ensure_ascii=False))
print(json.dumps(failures[:10], ensure_ascii=False)[:2000])
