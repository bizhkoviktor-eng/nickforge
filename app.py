from flask import Flask, render_template, request, jsonify, Response
import random, re, sqlite3, os
from datetime import datetime

app = Flask(__name__)
DB = "nickforge.db"
BASE_URL = "https://nickforge.onrender.com"

STYLES = {
    "cyber": ("Cyber", ["Neo","Cyber","Byte","Glitch","Neon","Zero","Hex","Nova","Vex","Syn"], ["404","X","2077","AI","Core","OS"]),
    "dark": ("Dark", ["Void","Shadow","Night","Grim","Phantom","Raven","Abyss","Ghost","Dread","Noir"], ["X","Shade","Reaper","Soul","Wraith","666"]),
    "pro": ("Pro", ["Clutch","Fury","Prime","Aim","Rush","Elite","Ace","Sharp","Peak","Rival"], ["GG","FPS","HD","OP","X","YT","TV"]),
    "fantasy": ("Fantasy", ["Drake","Elder","Mystic","Rune","Fae","Dragon","Storm","Ember","Moon","Frost"], ["Lord","Knight","Mage","Born","Fang","Fire","Wolf","X"]),
    "funny": ("Funny", ["Potato","Pickle","Goofy","Waffle","Bongo","Noodle","Chonky","Bonk","Muffin","Taco"], ["XD","Bro","Lol","King","GG","UwU"]),
    "anime": ("Anime", ["Kage","Yuki","Akira","Ryu","Hoshi","Kuro","Sora","Ren","Kitsune","Shiro"], ["Senpai","Kun","Chan","X","Yoru","Zero"]),
    "space": ("Space", ["Cosmo","Astro","Lunar","Orbit","Stellar","Mars","Solar","Quasar","Comet","Void"], ["X","Prime","Nova","Core","One","GG"]),
    "royal": ("Royal", ["Royal","King","Crown","Duke","Lord","Emperor","Prince","Queen","Noble"], ["X","Prime","GG","VII","Elite"]),
    "horror": ("Horror", ["Scream","Blood","Crypt","Doom","Haunt","Grave","Feral","Banshee","Rot","Wicked"], ["X","666","Night","Soul","Fang"]),
    "luxury": ("Luxury", ["Velvet","Gold","Diamond","Luxe","Royal","Opal","Silk","Platinum","Pearl","Elite"], ["X","Prime","Club","One","VII"]),
    "minimal": ("Minimal", ["Nox","Vex","Zed","Kyn","Lux","Zen","Rex","Nyx","Vyn","Axo"], ["X","7","9","0","Z","V","FX"])
}

def init_db():
    con=sqlite3.connect(DB)
    con.execute("CREATE TABLE IF NOT EXISTS generated (nickname TEXT PRIMARY KEY, created_at TEXT NOT NULL)")
    con.execute("CREATE TABLE IF NOT EXISTS popularity (nickname TEXT PRIMARY KEY, views INTEGER NOT NULL DEFAULT 0, copies INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL)")
    con.commit(); con.close()

def clean(v): return re.sub(r"[^A-Za-z0-9]", "", v or "")[:15]

def make_name(style, word="", separator=False, numbers=False):
    _, prefixes, suffixes=STYLES.get(style, STYLES["cyber"])
    word=clean(word); p=random.choice(prefixes); s=random.choice(suffixes)
    pool=[f"{p}{s}",f"{p}{random.choice(['X','Z','V'])}{s}",f"{p}{word}" if word else f"{p}{s}",f"{word}{p}" if word else f"{p}{s}",f"{p}{word}{s}" if word else f"{p}{s}",f"{p}{random.randint(10,999)}"]
    result=random.choice(pool)
    if separator and len(result)>5:
        pos=max(1,len(result)//2); result=result[:pos]+"_"+result[pos:]
    if numbers and random.random()<.65: result+=str(random.randint(1,999))
    return result[:20]

def unique_name(style,word,separator,numbers):
    con=sqlite3.connect(DB)
    for _ in range(100):
        n=make_name(style,word,separator,numbers)
        if not con.execute("SELECT 1 FROM generated WHERE nickname=?",(n,)).fetchone():
            now=datetime.utcnow().isoformat(); con.execute("INSERT INTO generated VALUES (?,?)",(n,now)); con.execute("INSERT OR IGNORE INTO popularity(nickname,created_at) VALUES (?,?)",(n,now)); con.commit(); con.close(); return n
    con.close(); return make_name(style,word,separator,True)

@app.route("/")
def index(): return render_template("index.html", styles=STYLES, page="home", base_url=BASE_URL)

@app.route("/popular")
def popular():
    con=sqlite3.connect(DB); rows=con.execute("SELECT nickname, views, copies FROM popularity ORDER BY (views + copies*3) DESC, nickname LIMIT 100").fetchall(); con.close()
    return render_template("popular.html", rows=rows, base_url=BASE_URL)

@app.route("/style/<style>")
def style_page(style):
    if style not in STYLES: return render_template("index.html", styles=STYLES, page="home", base_url=BASE_URL), 404
    return render_template("index.html", styles=STYLES, page="style", preset=style, base_url=BASE_URL)

@app.post("/generate")
def generate():
    data=request.get_json(silent=True) or {}; style=data.get("style","cyber"); word=data.get("word","")
    count=min(max(int(data.get("count",12)),1),50); separator=bool(data.get("separator")); numbers=bool(data.get("numbers"))
    names=[]
    while len(names)<count:
        n=unique_name(style,word,separator,numbers)
        if n not in names: names.append(n)
    return jsonify(names=names)

@app.post("/track")
def track():
    data=request.get_json(silent=True) or {}; n=clean(data.get("nickname",""))
    if not n: return jsonify(ok=False)
    field="copies" if data.get("event")=="copy" else "views"
    con=sqlite3.connect(DB); con.execute(f"UPDATE popularity SET {field}={field}+1 WHERE nickname=?",(n,)); con.commit(); con.close()
    return jsonify(ok=True)

@app.get("/check")
def check():
    n=clean(request.args.get("nickname",""))
    if not n: return jsonify(ok=False,message="Введите ник")
    con=sqlite3.connect(DB); row=con.execute("SELECT 1 FROM generated WHERE nickname=?",(n,)).fetchone(); con.close()
    return jsonify(ok=True,nickname=n,local_used=bool(row),message="Ник уже встречался в базе NickForge" if row else "Ник не найден в локальной базе NickForge")

@app.get("/robots.txt")
def robots(): return Response(f"User-agent: *\nAllow: /\nSitemap: {BASE_URL}/sitemap.xml\n",mimetype="text/plain")

@app.get("/sitemap.xml")
def sitemap():
    urls=[BASE_URL+"/",BASE_URL+"/popular"]+[BASE_URL+f"/style/{k}" for k in STYLES]
    xml='<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join(f'<url><loc>{u}</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>' for u in urls)+'</urlset>'
    return Response(xml,mimetype="application/xml")

init_db()
if __name__=="__main__": app.run(host="0.0.0.0",port=int(os.environ.get("PORT",5000)))
