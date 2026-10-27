"""Compile the R18 (adult) PSB scenes into the watch reader graph.

Source of truth: adult.xp3 / adult2.xp3, byte-identical in the Steam and I: roots.
Node ids of scenes that already existed in 0.1.9 keep their old id so old saves
still resolve; new scenes are appended after the highest existing id.
"""
from pathlib import Path
import json
import re
import sys

from tjs_data import loads
from story_text import normalize_dialogue

PORT = Path(__file__).resolve().parents[1]
BASE = Path(r'D:/codex/2026-10-26/senren-rw5')          # read-only 0.1.9 project
ADULT = Path(r'D:/DSH/work/port/probe/adult-json')
O = PORT / 'converted'


def compact(x):
    return json.dumps(x, ensure_ascii=False, separators=(',', ':'))


# ---------- original tables ----------
chart = loads((BASE / 'probe/extracted/data/main/scnchartdata.tjs.utf8.txt').read_text('utf8'))
translations = {}
flow = BASE / 'probe/extracted/data/main/flow_texts_cn.ini.utf8.txt'
if flow.exists():
    for line in flow.read_text('utf8').splitlines():
        if not line or line.startswith('#'):
            continue
        parts = re.split(r'\t+', line)
        if len(parts) >= 2:
            translations[parts[0].strip()] = parts[1].strip()


def local(s):
    return translations.get(s, s).replace('\u3000', ' ')


# ---------- load adult scripts ----------
scripts = {}
for p in sorted(ADULT.glob('*.json')):
    if p.name.startswith('decoded') or p.name.endswith('.resx.json'):
        continue
    d = json.loads(p.read_text('utf8'))
    if 'scenes' not in d:
        continue
    scripts[d['name']] = d

print('adult scripts', len(scripts), flush=True)

# ---------- node id plan ----------
old_graph = json.loads((BASE / 'converted/graph.json').read_text('utf8'))
old_ids = {}
for nid, node in old_graph['nodes'].items():
    src = node.get('source')
    if src:
        old_ids[(src[0].lower(), src[1].lower())] = nid
next_id = max(int(k[1:]) for k in old_graph['nodes']) + 1

scene_ids = {}
for name in scripts:
    for scene in scripts[name]['scenes']:
        key = (name.lower(), scene['label'].lower())
        if key in old_ids:
            scene_ids[key] = old_ids[key]
        else:
            scene_ids[key] = 'n' + str(next_id)
            next_id += 1

new_count = sum(1 for k, v in scene_ids.items() if k not in old_ids)
print('nodes', len(scene_ids), 'new', new_count, flush=True)


def dest(storage, target=''):
    storage = storage if storage.lower().endswith('.ks') else storage.replace('.ks.scn', '.ks')
    if storage.lower() == 'start.ks':
        return '@end'
    if not target:
        for name in scripts:
            if name.lower() == storage.lower():
                return scene_ids[(name.lower(), scripts[name]['scenes'][0]['label'].lower())]
        raise ValueError('Unknown original script ' + storage)
    key = (storage.lower(), target.lower())
    if key not in scene_ids:
        raise ValueError('Unknown original scene ' + repr(key))
    return scene_ids[key]


images = {}
requests = {}


def request(file, options=None):
    key = compact([file, options or {}])
    if key not in requests:
        aid = 'a' + str(len(requests))
        requests[key] = aid
        images[aid] = {'file': file, 'options': options or {}}
    return requests[key]


def action(o):
    out = {}
    for a in o.get('action', []) or []:
        if a and isinstance(a, list) and len(a) > 1 and isinstance(a[1], (int, float, str)):
            out[a[0]] = a[1]
    return out


def art(env):
    active = []
    for name, cls, o in env.get('data', []) or []:
        if cls not in ['stage', 'event', 'centerlayer', 'character', 'character2']:
            continue
        if o.get('showmode') not in [1, 3] or not o.get('redraw'):
            continue
        f = o['redraw'].get('imageFile') or {}
        file = f.get('file')
        if not file:
            continue
        ac = action(o)
        if ac.get('opacity', 255) == 0:
            continue
        active.append({'file': file, 'options': f.get('options') or {}, 'class': cls,
                       'position': o['redraw'].get('posName'), 'action': ac,
                       'z': ac.get('zpos', 233 if cls == 'stage' else 0)})
    backs = [o for o in active if o['class'] in ['stage', 'event', 'centerlayer']]
    back = min(backs, key=lambda o: o['z']) if backs else {'file': '画面_黒', 'options': {}, 'z': 999}
    bg = request(back['file'], back['options'])
    sprites = []
    for o in sorted(active, key=lambda o: -float(o['z'])):
        if o['class'] not in ['character', 'character2'] or o['z'] > back['z']:
            continue
        ac = o['action']
        a = request(o['file'], o['options'])
        sprites.append({'asset': a, 'position': o['position'], 'x': ac.get('xpos', 0),
                        'y': ac.get('ypos', 0), 'zx': ac.get('zoomx', 100), 'zy': ac.get('zoomy', 100),
                        'z': o['z'], 'opacity': ac.get('opacity', 255)})
    return {'background': bg, 'sprites': sprites}


def title(x, scene):
    t = scene.get('title', '')
    if isinstance(t, list):
        t = t[2] or t[0]
    if t:
        return local(t)
    tag = 's' + re.match(r'(\d+[ab]?)', x['name']).group(1)
    cap = chart['captions'].get(tag, [])
    return ' · '.join(local(v) for v in cap)


def route_of(script):
    number = re.match(r'(\d+[ab]?)', script).group(1)
    base = int(re.match(r'\d+', number).group())
    if base < 100:
        return 'common'
    if base < 200:
        return 'yoshino'
    if base < 300:
        return 'mako'
    if base < 400:
        return 'murasame'
    if base < 500:
        return 'lena'
    return 'sub'


SELECT_EXP = re.compile(r'SetBranchFlags\("([^"]+)",\s*(\d+)\)')
FLAG_TEST = re.compile(r'(!?)CheckBranchFlags\("(.+)"\)')
SEL_SET = re.compile(r'f\.sel_flag=(\d+)')
SEL_FLAG = re.compile(r'f\.sel_flag\s*==\s*(\d+)')

nodes = {}
frames_total = 0
choices_total = 0
warnings = []
alltexts = []
maxsprites = 0
ops_nodes = []
omitted = []

for name in sorted(scripts):
    x = scripts[name]
    route = route_of(name)
    for s in x['scenes']:
        key = scene_ids[(name.lower(), s['label'].lower())]
        frames = []
        ops = []
        texts = s.get('texts', []) or []
        ints = [l for l in s['lines'] if isinstance(l, int)]
        if ints != list(range(1, len(texts) + 1)):
            warnings.append({'scene': key, 'issue': 'line/text index mismatch',
                             'ints': len(ints), 'texts': len(texts)})
        for line in s['lines']:
            if isinstance(line, int):
                if line - 1 >= len(texts):
                    warnings.append({'scene': key, 'issue': 'out of range text index', 'index': line})
                    continue
                t = texts[line - 1]
                cn = t[2][2] if len(t) > 2 and t[2] and len(t[2]) > 2 else None
                if cn is None:
                    warnings.append({'scene': key, 'issue': 'missing chinese text', 'index': line})
                    continue
                speaker = cn[0] or ''
                text = normalize_dialogue(cn[1] or '')
                a = art(t[5])
                maxsprites = max(maxsprites, len(a['sprites']))
                frames.append({'speaker': speaker, 'text': text, 'art': a,
                               'chapter': local((t[5].get('showdate') or {}).get('date') or title(x, s))})
                frames_total += 1
                alltexts.append([speaker, text])
            elif isinstance(line, list) and line[0] == 'sysmovie':
                if 'SelectMovieFile("OP_")' in str(line):
                    ops.append(len(frames))
                    frames.append({'kind': 'op'})
                else:
                    omitted.append({'scene': key, 'order': len(frames)})

        choices = []
        for opt in s.get('selects', []) or []:
            exp = opt.get('exp', '') or ''
            m = SELECT_EXP.fullmatch(exp.replace(' ', ''))
            sm = SEL_SET.fullmatch(exp.replace(' ', ''))
            cn = (opt.get('language') or [None] * 3)[2]
            label = (cn or {}).get('text') or opt.get('text') or ''
            item = {'text': label, 'to': dest(opt['storage'], opt.get('target', '')),
                    'effect': [m.group(1), int(m.group(2))] if m
                    else ['sel_flag', int(sm.group(1))] if sm else None}
            if m is None and sm is None:
                warnings.append({'scene': key, 'issue': 'unparsed select effect', 'exp': exp})
                item['effect'] = ['sel_unparsed', 0]
            choices.append(item)
            choices_total += 1
        if len(choices) == 1:
            warnings.append({'scene': key, 'issue': 'single-option choice'})

        nexts = []
        for n in s.get('nexts', []) or []:
            cond = (n.get('eval') or '').strip()
            test = None
            if cond:
                fm = FLAG_TEST.fullmatch(cond)
                sm = SEL_FLAG.fullmatch(cond)
                if fm:
                    test = [fm.group(2), bool(fm.group(1))]
                elif sm:
                    test = ['sel_flag == ' + sm.group(1), False]
                else:
                    warnings.append({'scene': key, 'issue': 'unparsed next condition', 'eval': cond})
                    test = None
            nexts.append({'to': dest(n['storage'], n.get('target', '')), 'when': test})

        complete = []
        if any(n['to'] == '@end' for n in nexts):
            number = re.match(r'(\d+[ab]?)', name).group(1)
            if route in ('common', 'sub'):
                complete = ['koharu' if number == '512' or number == '513'
                            else 'roka' if number == '522' or number == '523' else 'normal']
            else:
                complete = [route]

        nodes[key] = {'title': title(x, s), 'chapter': title(x, s), 'route': route,
                      'count': len(frames), 'ops': ops, 'next': nexts, 'choices': choices,
                      'complete': complete, 'source': [x['name'], s['label']]}
        if ops:
            ops_nodes.append(key)
        (O / (key + '.json')).write_text(compact(frames), 'utf8')

chapters = []
# The six "after" scripts are extra adult content that the original unlocks once
# the heroine's own route is cleared, so they are listed separately and gated.
AFTER = {'115': ('yoshino', '芳乃后日谈'), '211': ('mako', '茉子后日谈'),
         '317': ('murasame', '丛雨后日谈'), '429': ('lena', '蕾娜后日谈'),
         '513': ('koharu', '小春后日谈'), '523': ('roka', '芦花后日谈')}
after_stories = []
for name in sorted(scripts):
    n = scene_ids[(name.lower(), scripts[name]['scenes'][0]['label'].lower())]
    number = re.match(r'(\d+[ab]?)', name).group(1)
    requires, label = AFTER.get(number, (None, None))
    entry = {'node': n, 'title': nodes[n]['title'], 'route': nodes[n]['route']}
    if requires:
        entry.update(after=True, requires=requires, label=label)
        after_stories.append({'node': n, 'title': label, 'chapter': nodes[n]['title'],
                              'route': nodes[n]['route'], 'requires': requires})
    chapters.append(entry)

initial = dest('001・アーサー王ver1.07.ks', '*com_part_1')
# 0.1.9 saves may point at scenes the adult script replaced. Only one scene in
# the 0.1.9 graph has no counterpart: 113 *yos_part_13:3 (censored variant) was
# expanded into the *chapterH3yos scene chain, so old saves resume there.
migrations = {}
for (script, label), nid in old_ids.items():
    if (script, label) not in scene_ids:
        target = scene_ids.get((script, '*chapterH3yos'))
        if target:
            migrations[nid] = target
graph = {'initial': initial, 'nodes': nodes, 'flagRules': chart['flags'], 'chapters': chapters,
         'afterStories': after_stories, 'migrations': migrations,
         'version': 2, 'content': 'senren-adult-0.1.10'}
(O / 'graph.json').write_text(compact(graph), 'utf8')
(O / 'image-requests.json').write_text(compact(images), 'utf8')
(O / 'text-source.json').write_text(compact(alltexts), 'utf8')

report = {'result': 'compiled-intermediate', 'sourceArchives': ['adult', 'adult2'],
          'scripts': len(scripts), 'nodes': len(nodes), 'newNodes': new_count,
          'texts': frames_total, 'choiceOptions': choices_total, 'imageRequests': len(images),
          'maxVisibleSprites': maxsprites, 'openingNodes': ops_nodes,
          'omittedEndingMovies': omitted, 'warnings': warnings[:50], 'warningCount': len(warnings)}
(PORT / 'reports/story-intermediate-v020.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), 'utf8')
print(json.dumps(report, ensure_ascii=False)[:1500])
