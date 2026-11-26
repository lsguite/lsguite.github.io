"""Run `python3 build.py` after editing data.json. Writes static HTML, sitemap.xml, robots.txt."""
import json, os, html, re
from datetime import date
D = json.load(open("data.json", encoding="utf-8")); S = D["site"]
e = html.escape; URL = S["url"].rstrip("/")
PAGES = [("Home", "index.html"), ("Publications", "publications.html"), ("Posters", "posters.html"), ("CV", "cv.html"), ("Astrophotography", "astrophotography.html")]
links = lambda ls: "".join(f'<a href="{e(l["url"])}">{e(l["label"])}</a>' for l in ls)

def rich(t):   # **word** -> bold + accent colour
    return re.sub(r"\*\*(.+?)\*\*", r'<strong style="color:var(--accent)">\1</strong>', e(t))

def page(file, title, desc, body, extra=""):
    path = "/" if file == "index.html" else "/" + file
    full = S["name"] if file == "index.html" else f'{title} | {S["name"]}'
    nav = "".join(f'<a class="tag" href="{f}"{" aria-current=\"page\"" if f == file else ""}>{l}</a>' for l, f in PAGES)
    home = file == "index.html"   # on the home page the big name replaces the small one in the header
    brand = "" if home else f'<a class="brand" href="index.html">{e(S["name"])}</a>'
    navstyle = ' style="margin-left:auto"' if home else ""
    open(file, "w", encoding="utf-8").write(f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(full)}</title><meta name="description" content="{e(desc)}"><meta name="author" content="{e(S["name"])}">
<link rel="canonical" href="{URL}{path}"><meta name="theme-color" content="#0e6b78">
<meta property="og:type" content="website"><meta property="og:title" content="{e(full)}"><meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{URL}{path}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;600&family=Newsreader:wght@400;500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="style.css">{extra}</head>
<body><header id="nav">{brand}<nav aria-label="Main"{navstyle}>{nav}</nav></header>
<main>{body}</main>
<footer id="foot"><span>&copy; {date.today().year} {e(S["name"])}</span><a href="mailto:{e(S["email"])}">{e(S["email"])}</a></footer>
</body></html>''')

def by_year(items, kind):
    out = ""
    for y in sorted({i["year"] for i in items}, reverse=True):
        out += f'<section class="year"><h2>{y}</h2>'
        for i in (x for x in items if x["year"] == y):
            out += (f'<article class="entry" itemscope itemtype="https://schema.org/{kind}"><h3 itemprop="name">{e(i["title"])}</h3>'
                    f'<p>{e(i.get("authors",""))}<br><em>{e(i.get("venue",""))}</em></p><meta itemprop="datePublished" content="{y}">'
                    f'<p class="links">{links(i.get("links",[]))}</p></article>')
        out += "</section>"
    return out

def pubs(items):
    out, cat = "", None
    for n, p in enumerate(items, 1):
        c = p.get("category", "")
        if n == 1 or c != cat:
            out += ("</section>" if n > 1 else "") + '<section class="cat">' + (f"<h2>{e(c)}</h2>" if c else ""); cat = c
        doi = p.get("doi", ""); href = p.get("url") or (f"https://doi.org/{doi}" if doi else "")
        t = e(p["title"]); t = f'<a href="{e(href)}">{t}</a>' if href else t
        auth = e(p.get("authors", ""))
        for me in S.get("me", []): auth = auth.replace(e(me), f"<strong>{e(me)}</strong>")
        badges = "".join(f"<li>{e(h)}</li>" for h in p.get("highlights", []))
        fig, body = p.get("figure") or {}, "".join(f"<p>{rich(x)}</p>" for x in p.get("summary", "").split("\n\n") if x.strip())
        if fig.get("src") and os.path.exists(fig["src"]):
            body += f'<figure><img loading="lazy" src="{e(fig["src"])}" alt="{e(fig.get("alt",""))}"><figcaption>{e(fig.get("caption",""))}</figcaption></figure>'
        lk = p.get("links", [])
        out += (f'<article class="entry pub" itemscope itemtype="https://schema.org/ScholarlyArticle">'
                f'<h3><span class="num">[{n}]</span> <span itemprop="name">{t}</span></h3><p class="auth">{auth}</p>'
                f'<p><em>{e(p.get("venue",""))}</em>, {p["year"]}</p><meta itemprop="datePublished" content="{p["year"]}">'
                + (f'<ul class="badges">{badges}</ul>' if badges else "")
                + (f'<details><summary>Summary</summary><div class="abs">{body}</div></details>' if body else "")
                + (f'<p class="links">{links(lk)}</p>' if lk else "") + '</article>')
    return out + "</section>" if items else ""

import re, subprocess
def posters(items):
    out = ""
    os.makedirs("previews", exist_ok=True)
    for p in items:
        pdf = p.get("pdf", "").lstrip("/"); has = bool(pdf) and os.path.exists(pdf)
        prev = "previews/" + os.path.splitext(os.path.basename(pdf))[0] if has else ""
        if has and not os.path.exists(prev + ".png"):   # auto preview from page 1 (needs poppler-utils; skipped if missing)
            try: subprocess.run(["pdftoppm", "-png", "-singlefile", "-f", "1", "-l", "1", "-scale-to-x", "600", "-scale-to-y", "-1", pdf, prev], check=True, capture_output=True)
            except Exception: pass
        t = e(p["title"]); t = f'<a href="{e(pdf)}">{t}</a>' if has else t
        auth = e(p.get("authors", ""))
        for me in S.get("me", []): auth = auth.replace(e(me), f"<strong>{e(me)}</strong>")
        thumb = f'<a class="thumb" href="{e(pdf)}"><img loading="lazy" src="{e(prev)}.png" alt="Preview of the poster: {e(p["title"])}"></a>' if has and os.path.exists(prev + ".png") else ""
        yr = (re.findall(r"\d{4}", p.get("date", "")) or [""])[0]
        out += (f'<article class="poster" itemscope itemtype="https://schema.org/CreativeWork">{thumb}<div>'
                f'<h3 itemprop="name">{t}</h3><p class="auth">{auth}</p><p><em>{e(p.get("event",""))}</em>, {e(p.get("date",""))}</p>'
                f'<meta itemprop="datePublished" content="{yr}">'
                + (f'<ul class="badges"><li>{e(p["note"])}</li></ul>' if p.get("note") else "") + "</div></article>")
    return f'<div class="poster-grid">{out}</div>' if out else ""

try:
    from PIL import Image, ImageOps
    Image.MAX_IMAGE_PIXELS = None
except ImportError:
    Image = None

def photo_info(s):
    """Return (path to show, width, height). Big photos get a ~1000 px thumbnail in thumbs/ (the click-through keeps the original)."""
    if not Image: return s, 0, 0
    try:
        with Image.open(s) as im:
            im = ImageOps.exif_transpose(im); w, h = im.size
            if w <= 1100: return s, w, h
            t = "thumbs/" + s.replace("/", "_").rsplit(".", 1)[0] + ".jpg"
            if not os.path.exists(t):
                os.makedirs("thumbs", exist_ok=True)
                im.convert("RGB").resize((1000, round(h * 1000 / w)), Image.LANCZOS).save(t, quality=82, optimize=True, progressive=True)
            return t, 1000, round(h * 1000 / w)
    except Exception:
        return s, 0, 0

def photos(items):
    figs = []
    for p in items:
        s = p.get("src", "").lstrip("/")
        if not s or not os.path.exists(s): continue
        t, w, h = photo_info(s)
        det = f"<span>{e(p['details'])}</span>" if p.get("details") else ""
        ratio = f"aspect-ratio:{w}/{h};" if w and h else ""      # reserves the space so the page doesn't jump while images load
        load = "eager" if len(figs) < 4 else "lazy"
        figs.append(f'<figure class="photo" style="order:{len(figs)}" itemscope itemtype="https://schema.org/ImageObject"><link itemprop="contentUrl" href="{e(s)}"><a href="{e(s)}">'
                    f'<img loading="{load}" decoding="async" src="{e(t)}" style="{ratio}background:var(--line)" alt="{e(p.get("alt") or p.get("title", ""))}"></a>'
                    f'<figcaption><strong itemprop="name">{e(p.get("title", ""))}</strong>{det}</figcaption></figure>')
    if not figs: return ""
    # entries alternate left, right, left, right... (1st left, 2nd right, 3rd left under the 1st, ...)
    return '<div class="gallery"><div class="gcol">' + "".join(figs[0::2]) + '</div><div class="gcol">' + "".join(figs[1::2]) + '</div></div>'

# Home
media = S.get("hero_media", "").lstrip("/")
if media and not os.path.exists(media): media = ""   # file not uploaded yet: fall back to the animation
poster = S.get("hero_poster", "").lstrip("/")
if media.endswith((".mp4", ".webm")):
    pa = f' poster="{e(poster)}"' if poster and os.path.exists(poster) else ""
    stage = f'<div class="stage media"><video src="{e(media)}"{pa} loop muted playsinline{" controls" if S.get("hero_controls") else " disablepictureinpicture"} preload="metadata"></video></div>'
elif media: stage = f'<div class="stage media"><img src="{e(media)}" alt="{e(S.get("hero_alt", "Illustration of my research"))}"></div>'
else: stage = '<div class="stage"><canvas id="stage" role="img" aria-label="Animated network of drifting points"></canvas></div>'
def hl_card(src, alt, cap, href="", title="", meta=""):
    t, w, h = photo_info(src)
    ratio = f"aspect-ratio:{w}/{h};" if w and h else "aspect-ratio:auto;"
    img = f'<img loading="lazy" decoding="async" src="{e(t)}" alt="{e(alt)}" style="{ratio}object-fit:contain;background:var(--line)">'
    if href: img = f'<a href="{e(href)}">{img}</a>'
    c = f'<span style="display:block;color:var(--ink)">{rich(cap)}</span>' if cap else ""
    s = f'<span style="display:block">From <a href="{e(href)}">{e(title)}</a>, {e(meta)}</span>' if title and href else ""
    return f"<figure>{img}<figcaption>{c}{s}</figcaption></figure>"

# Research highlights: figures listed in "figures" (data.json) if any, otherwise the figure of each first-author paper (max 3)
cards = [hl_card(f["src"].lstrip("/"), f.get("alt", ""), f.get("caption", ""), f.get("url", "")) for f in D.get("figures", []) if os.path.exists(f.get("src", "").lstrip("/"))]
if not cards:
    for p in D["publications"]:
        fg = p.get("figure") or {}; src = fg.get("src", "").lstrip("/")
        if p.get("category") == "First author" and src and os.path.exists(src):
            href = p.get("url") or (f"https://doi.org/{p['doi']}" if p.get("doi") else "")
            cards.append(hl_card(src, fg.get("alt", ""), fg.get("caption", ""), href, p["title"], f'{p.get("venue", "")} {p["year"]}'))
highlights = ('<section style="margin-bottom:3rem"><h2>Research highlights</h2><div class="figs">' + "".join(cards[:3]) + "</div></section>") if cards else ""
_r = S["role"].rsplit(", ", 1)   # keep the last part (the institution) on one line
role_html = f'{e(_r[0])}, <span style="white-space:nowrap">{e(_r[1])}</span>' if len(_r) == 2 else e(S["role"])
delay = int(float(S.get("hero_delay", 2.5)) * 1000)   # seconds before the first video starts ("hero_delay" in data.json)
bm = S.get("banner_media", "").lstrip("/")
if bm and not os.path.exists(bm): bm = ""
banner = ""
if bm:
    bp = S.get("banner_poster", "").lstrip("/")
    pa = f' poster="{e(bp)}"' if bp and os.path.exists(bp) else ""
    cap = f'<figcaption>{rich(S["banner_caption"])}</figcaption>' if S.get("banner_caption") else ""
    ctl = " controls" if S.get("hero_controls") else " disablepictureinpicture"
    banner = (f'<figure class="banner" style="margin:0 0 3rem"><video src="{e(bm)}"{pa} loop muted playsinline{ctl} preload="metadata" '
              f'style="width:100%;height:auto;display:block;border-radius:14px"></video>{cap}</figure>')
# Only one video plays at a time: the one most visible on screen, and only after the start delay
PLAYER = """<script>(function(){
var reduce=matchMedia('(prefers-reduced-motion: reduce)').matches,ready=false,vis=new Map();
var vids=[document.querySelector('.stage video'),document.querySelector('.banner video')].filter(Boolean);
function update(){if(reduce||!ready)return;var best=null,r=0;
vids.forEach(function(v){var x=vis.get(v)||0;if(x>r){r=x;best=v}});
vids.forEach(function(v){if(v===best){if(v.paused)v.play().catch(function(){})}else if(!v.paused)v.pause()})}
var io=new IntersectionObserver(function(es){es.forEach(function(e){vis.set(e.target,e.intersectionRatio>=.3?e.intersectionRatio:0)});update()},{threshold:[0,.3,.5,.75,1]});
vids.forEach(function(v){io.observe(v)});
setTimeout(function(){ready=true;update()},DELAY);
})();</script>"""
herojs = '<script src="anim.js" defer></script>' if not media else ""
if media.endswith((".mp4", ".webm")) or bm: herojs += PLAYER.replace("DELAY", str(delay))
person = json.dumps({"@context": "https://schema.org", "@type": "Person", "name": S["name"], "jobTitle": S["role"], "url": URL + "/",
                     "email": S["email"], "sameAs": [l["url"] for l in S["links"]]})
page("index.html", "Home", S["description"], f'''<section class="hero"><div><h1>{e(S["name"])}</h1><p class="role">{role_html}</p>
<p>{rich(S["intro"])}</p><p class="links">{links(S["links"])}</p></div>{stage}</section>
{highlights}
{banner}
{herojs}''', f'<script type="application/ld+json">{person}</script>')

page("publications.html", "Publications", f'Peer-reviewed papers and preprints by {S["name"]}.',
     '<h1 class="page-title">Publications</h1>' + (pubs(D["publications"]) or "<p>Coming soon.</p>"))
page("posters.html", "Posters", f'Conference posters by {S["name"]}.',
     '<h1 class="page-title">Posters</h1>' + (posters(D["posters"]) or "<p>Coming soon.</p>"))
cv = "".join(f'<section class="year"><h2>{e(s["title"])}</h2><div>' + "".join(
    f'<article class="entry"><span class="when">{e(i["when"])}</span><h3>{e(i["what"])}</h3><p>{e(i["where"])}</p></article>'
    for i in s["items"]) + "</div></section>" for s in D["cv"])
page("cv.html", "CV", f'Curriculum vitae of {S["name"]}: education, experience and awards.',
     f'<h1 class="page-title">CV</h1>' + (f'<a class="btn" href="{e(S["cv_pdf"])}">Download CV (PDF)</a>' if os.path.exists(S["cv_pdf"]) else "") + (cv or "<p>Coming soon.</p>"))

page("astrophotography.html", "Astrophotography", f'Astrophotography by {S["name"]}.',
     '<h1 class="page-title">Astrophotography</h1>' + (photos(D.get("photos", [])) or "<p>Coming soon.</p>"))

open("sitemap.xml", "w").write('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' +
    "".join(f'<url><loc>{URL}{"/" if f=="index.html" else "/"+f}</loc><lastmod>{date.today()}</lastmod></url>' for _, f in PAGES) + "</urlset>")
open("robots.txt", "w").write(f"User-agent: *\nAllow: /\nSitemap: {URL}/sitemap.xml\n")
print("Built:", ", ".join(f for _, f in PAGES))
