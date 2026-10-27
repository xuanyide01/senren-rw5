"""Rebuild the CG gallery from the original cglist files (base + adult patch).

Group order, titles and per-group variant order follow the original game, so the
watch gallery shows the same groups the game's CG mode shows; variants we did not
convert (the original lists 3,758 names, the port carries 1,195) are skipped.
"""
import json
from pathlib import Path

P = Path(r'D:\DSH\work\port')
BASE = Path(r'D:\codex\2026-10-26\senren-rw5')
LISTS = [BASE / 'probe/extracted/data/main/cglist.csv.utf8.txt',
         P / 'probe/extracted/adult/cglist_0.csv.utf8.txt']


def parse(path):
    groups = []
    for line in path.read_text('utf8').splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        parts = [x.strip() for x in line.replace('\t', ',').split(',')]
        if len(parts) < 2 or parts[0] == ':':
            continue
        groups.append((parts[0], parts[1], [x for x in parts[2:] if x]))
    return groups


map = json.loads((P / 'senren-rw5/converted/image-map.json').read_text('utf8'))
by_file = {}
for v in map.values():
    by_file.setdefault(v['original']['file'].lower(), v['src'])

out = []
seen_titles = set()
skipped_groups = []
for path in LISTS:
    for thumb, title, images in parse(path):
        if title in seen_titles:
            continue
        variants = []
        for name in images:
            for alt in name.split('|'):
                key = alt.strip().lstrip('*').lower()
                src = by_file.get(key)
                if src and src not in variants:
                    variants.append(src)
        if not variants:
            skipped_groups.append((thumb, title))
            continue
        seen_titles.add(title)
        out.append({'label': title, 'thumb': thumb, 'variants': variants})

(P / 'senren-rw5/src/common/gallery.txt').write_text(
    json.dumps(out, ensure_ascii=False, separators=(',', ':')), 'utf8')

report = {'groups': len(out), 'variants': sum(len(g['variants']) for g in out),
          'skippedGroups': skipped_groups,
          'sourceLists': [str(x) for x in LISTS]}
(P / 'senren-rw5/reports/gallery-v021.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), 'utf8')
print(json.dumps(report, ensure_ascii=False)[:800])
