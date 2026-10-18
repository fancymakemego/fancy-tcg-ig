# -*- coding: utf-8 -*-
import base64, io, json, textwrap
from PIL import Image, ImageDraw, ImageFont
OUT = str(__import__("pathlib").Path(__file__).resolve().parent.parent / "topic_images")
BG=(18,20,28); FG=(245,246,250); ACCENT=(255,203,5); SUB=(150,157,175); CARD=(30,33,44)
def F(s,b=False): return ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf" if b else "C:/Windows/Fonts/segoeui.ttf", s)
d=json.load(io.open("data.json",encoding="utf-8"))
slabs=sum(len(g["certs"]) for g in d)
def base():
    W,H=1080,1350; im=Image.new("RGB",(W,H),BG); dr=ImageDraw.Draw(im)
    dr.rectangle([0,0,W,14],fill=ACCENT); dr.rectangle([0,H-14,W,H],fill=ACCENT)
    dr.text((80,H-118),"@fancy_tcg_japan",font=F(34,True),fill=ACCENT)
    dr.text((80,H-74),"Japanese cards, shipped from Japan",font=F(28),fill=SUB)
    return im,dr
# slide 1
im,dr=base()
dr.text((80,110),"NEW  ·  PSA VAULT TO VAULT",font=F(32,True),fill=ACCENT)
y=165
for ln in ["Buy my PSA slabs","vault to vault"]:
    dr.text((80,y),ln,font=F(80,True),fill=FG); y+=100
dr.text((80,y+5),"{} slabs · {} cards already stored in the PSA Vault".format(slabs,len(d)),font=F(34),fill=SUB)
# collage: pick top cards with distinct names
seen=set(); pick=[]
for g in d:
    if g["name"] in seen: continue
    seen.add(g["name"]); pick.append(g)
    if len(pick)==8: break
cw,ch=208,330; gap=16; x0=80; y0=470
for i,g in enumerate(pick):
    r,c=divmod(i,4); x=x0+c*(cw+gap); yy=y0+r*(ch+gap+30)
    img=Image.open(io.BytesIO(base64.b64decode(g["img"].split(",",1)[1]))).convert("RGB")
    img.thumbnail((cw,ch)); 
    dr.rounded_rectangle([x,yy,x+cw,yy+ch],12,fill=CARD)
    im.paste(img,(x+(cw-img.width)//2, yy+(ch-img.height)//2))
    dr.text((x+4,yy+ch+4),"PSA {}".format(g["grade"]),font=F(24,True),fill=ACCENT)
im.save(OUT+r"\vault-to-vault-1.jpg","JPEG",quality=92)
# slide 2
im,dr=base()
dr.text((80,110),"HOW IT WORKS",font=F(32,True),fill=ACCENT)
y=165
for ln in ["Skip the shipping","from Japan"]:
    dr.text((80,y),ln,font=F(80,True),fill=FG); y+=100
y=500
for b in ["These slabs already sit in the PSA Vault in the US",
          "Ownership moves vault to vault — nothing has to cross the ocean",
          "No international shipping wait, no import duty on a box from Japan",
          "Keep it in the Vault, or have PSA ship it to you whenever you like",
          "Full list: link in bio · DM me for prices"]:
    dr.ellipse([84,y+16,100,y+32],fill=ACCENT)
    for ln in textwrap.wrap(b,width=36):
        dr.text((124,y),ln,font=F(38),fill=FG); y+=50
    y+=26
im.save(OUT+r"\vault-to-vault-2.jpg","JPEG",quality=92)
print("ok",slabs,len(d),[g["name"] for g in pick])
