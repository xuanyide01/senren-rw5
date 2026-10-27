"""Plan portrait layer stacks for every .stand request of the adult build (read-only inputs)."""
from pathlib import Path
import json
import csv

from tjs_data import loads

PORT = Path(r'D:\DSH\work\port\senren-rw5')
BASE = Path(r'D:\codex\2026-10-26\senren-rw5')
FG = BASE / 'probe/extracted/fgimage'
requests = json.loads((PORT / 'converted/image-requests.json').read_text('utf8'))
cache = {}
plans = {}
missing = []
needed = {}
optional = []


def table(base):
    if base in cache:
        return cache[base]
    info = FG / (('face白狗a' if base == '白狗a' else base) + '_info.txt.utf8.txt')
    dress = {}
    face = {}
    for line in info.read_text('utf8').splitlines():
        a = line.split('\t')
        if len(a) >= 5 and a[0] == 'dress':
            dress.setdefault((a[1], a[3]), []).append(a[4])
        if len(a) >= 4 and a[0] == 'face':
            face.setdefault(a[1], []).append(a[3])
    files = list(FG.rglob(base + '_0.txt.utf8.txt')) or list(FG.rglob(base + '.txt.utf8.txt'))
    assert len(files) == 1, (base, files)
    desc = files[0]
    rows = list(csv.reader(desc.read_text('utf8').splitlines(), delimiter='\t'))
    header = [s.lstrip('#') for s in rows[0]]
    layers = []
    for row in rows[2:]:
        d = dict(zip(header, row))
        if d.get('layer_id'):
            layers.append(d)
    byid = {d['layer_id']: d for d in layers}
    bypath = {}

    def path(d):
        parent = d.get('group_layer_id')
        return (path(byid[parent]) + '/' if parent in byid else '') + d['name'].replace('/', '_')

    for d in layers:
        bypath[path(d)] = d
    prefix = desc.name.removesuffix('.txt.utf8.txt')
    val = {'dress': dress, 'face': face, 'layers': layers, 'bypath': bypath, 'prefix': prefix,
           'dir': desc.parent, 'canvas': [int(rows[1][4]), int(rows[1][5])]}
    cache[base] = val
    return val


for aid, req in requests.items():
    if not req['file'].endswith('.stand'):
        continue
    try:
        name = Path(req['file']).stem
        stand = loads((FG / (name + '.stand.utf8.txt')).read_text('utf8'))
        op = req['options']
        pose = str(op.get('pose', '1'))
        found = None
        for item in stand:
            base = item['filename']
            t = table(base)
            key = (str(op.get('dress', '')), pose)
            if not op:
                key = next(iter(t['dress']))
            if key in t['dress']:
                found = (base, t, key, item)
                break
        if found is None:
            raise ValueError('No matching original pose/dress')
        base, t, key, item = found
        select = t['dress'][key] + t['face'].get(str(op.get('face', '00')), [])
        resolved = []
        for path in select:
            d = t['bypath'].get(path)
            if d is None:
                raise ValueError('Missing layer ' + path)
            if d['layer_type'] != '0':
                raise ValueError('Unsupported group layer ' + path)
            p = t['dir'] / (t['prefix'] + '_' + d['layer_id'] + '.tlg')
            if not p.exists():
                replacement = FG / '裸加工' / p.with_suffix('.png').name
                if replacement.exists():
                    p = replacement
                elif int(d['type']) == 16 or d['name'].endswith('光'):
                    optional.append({'asset': aid, 'originalMissingOverlay': path, 'layer': d['layer_id']})
                    continue
                else:
                    raise ValueError('Missing TLG ' + str(p))
            nid = str(p.relative_to(FG))
            needed[nid] = {'input': str(p),
                           'output': str(Path(r'D:/DSH/work/port/probe/decoded-layers') / Path(nid).with_suffix('.png'))}
            resolved.append({'id': nid, 'left': int(d['left']), 'top': int(d['top']),
                             'type': int(d['type']), 'opacity': int(d['opacity']),
                             'order': t['layers'].index(d), 'name': path,
                             'face': path in t['face'].get(str(op.get('face', '00')), []) and path not in t['dress'][key]})
        plans[aid] = {'base': base, 'canvas': t['canvas'],
                      'layers': sorted(resolved, key=lambda x: -x['order']),
                      'original': req, 'offset': item}
    except Exception as err:
        missing.append({'id': aid, 'request': req, 'error': str(err)})

(PORT / 'reports/portrait-plan.json').write_text(json.dumps(plans, ensure_ascii=False, indent=2), 'utf8')
(PORT / 'reports/tlg-plan.json').write_text(json.dumps(list(needed.values()), ensure_ascii=False, indent=2), 'utf8')
(PORT / 'reports/portrait-plan-missing.json').write_text(json.dumps(missing, ensure_ascii=False, indent=2), 'utf8')
(PORT / 'reports/portrait-optional-overlays.json').write_text(json.dumps(optional, ensure_ascii=False, indent=2), 'utf8')
old = json.loads((BASE / 'reports/portrait-plan.json').read_text('utf8'))
print(json.dumps({'plannedPortraits': len(plans), 'oldPlans': len(old),
                  'requiredLayers': len(needed), 'missing': len(missing),
                  'examples': [m['error'] + ' ' + str(m['request']) for m in missing[:8]]}, ensure_ascii=False))
