"""Rebuild the embedded font subset for the adult text (SIL OFL source font)."""
from pathlib import Path
import json

from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
source = Path('D:/codex/2026-10-08/zhe/work/summer-name-fix/NotoSansMonoCJKsc-Regular.otf')
chars = set(chr(x) for x in range(32, 127))


def collect(value):
    if isinstance(value, str):
        chars.update(value)
    elif isinstance(value, list):
        for x in value:
            collect(x)
    elif isinstance(value, dict):
        for x in value.values():
            collect(x)


collect(json.loads((ROOT / 'converted/text-source.json').read_text('utf8')))
chars.update((ROOT / 'converted/graph.json').read_text('utf8'))
chars.update((ROOT / 'src/pages/index/index.ux').read_text('utf8'))
chars.update((ROOT / 'src/common/gallery.txt').read_text('utf8'))
chars.discard('\ufeff')

font = TTFont(source)
cmap = font.getBestCmap()
missing = sorted(c for c in chars if not c.isspace() and ord(c) >= 32 and ord(c) not in cmap)
assert not missing, repr(missing)
coverage = {ord(c) for c in chars if ord(c) in cmap}
options = subset.Options()
options.layout_features = []
options.drop_tables += ['BASE', 'GSUB', 'GPOS', 'VORG', 'vhea', 'vmtx']
options.desubroutinize = True
options.hinting = False
subsetter = subset.Subsetter(options=options)
subsetter.populate(unicodes=coverage)
subsetter.subset(font)
for name in font['name'].names:
    if name.nameID in (1, 3, 4, 6, 16):
        name.string = 'SenrenWatchText'.encode(name.getEncoding(), errors='replace')
if 'CFF ' in font:
    font['CFF '].cff.fontNames = ['SenrenWatchText']
output = ROOT / 'src/common/senren-text.otf'
font.save(output)
assert coverage == set(TTFont(output).getBestCmap())
assert output.stat().st_size < 1500000, 'Font exceeds conservative single-resource budget'
report = {'font': 'SenrenWatchText', 'codepoints': len(coverage),
          'glyphs': len(font.getGlyphOrder()), 'fontBytes': output.stat().st_size,
          'allStoryTextCovered': True, 'license': 'SIL OFL 1.1'}
(ROOT / 'reports/text-font.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
print(json.dumps(report, ensure_ascii=False))
