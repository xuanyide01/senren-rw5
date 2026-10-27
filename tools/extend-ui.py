"""The maintained reader is src/pages/index/index.ux; it is not regenerated.
Initial derivation is archived in revisions; preserve the verified current source.
"""
from pathlib import Path
import json
r=Path(__file__).resolve().parents[1]
s=(r/"src/pages/index/index.ux").read_text("utf8")
assert "opening-sheet{position:absolute;top:0px;left:0px;width:384px;height:216px;object-fit:contain;}" in s
assert "title-cache" not in s and "TITLE_CALLS" not in s
m=json.loads((r/"src/manifest.json").read_text("utf8"))
assert m["versionName"]==json.loads((r/"package.json").read_text("utf8"))["version"]
print("MAINTAINED_UI_VALIDATED",m["versionName"])
