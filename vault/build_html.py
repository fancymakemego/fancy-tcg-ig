# -*- coding: utf-8 -*-
"""data.json + template.html → fancy-tcg-vault.html（Artifact に公開するページ）"""
import io
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).parent
updated = sys.argv[1] if len(sys.argv) > 1 else datetime.now().strftime("%B %d, %Y").replace(" 0", " ")
t = io.open(HERE / "template.html", encoding="utf-8").read()
d = io.open(HERE / "data.json", encoding="utf-8").read().replace("</", "<\/")
io.open(HERE / "fancy-tcg-vault.html", "w", encoding="utf-8").write(t.replace("__DATA__", d).replace("__UPDATED__", updated))
print("ok", updated)
