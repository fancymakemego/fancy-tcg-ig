import json, re, io
d = json.load(io.open("data.json", encoding="utf-8"))
for g in d:
    for k in ("name", "set"):
        g[k] = re.sub(r"\bEx\b", "ex", g[k]).replace("Starter Deck ex", "Starter Deck EX")
io.open("data.json", "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False))
print([g["name"] for g in d][:6])
