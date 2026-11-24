"""Run `python3 build.py` after editing data.json. Writes static HTML, sitemap.xml, robots.txt."""
import json, os, html
from datetime import date
D = json.load(open("data.json", encoding="utf-8")); S = D["site"]
e = html.escape; URL = S["url"].rstrip("/")
PAGES = [("Home", "index.html"), ("Publications", "publications.html"), ("Posters", "posters.html"), ("CV", "cv.html"), ("Astrophotography", "astrophotography.html")]
links = lambda ls: "".join(f'<a href="{e(l["url"])}">{e(l["label"])}</a>' for l in ls)

def page(file, title, desc, body, extra=""):
    path = "/" if file == "index.html" else "/" + file
    full = S["name"] if file == "index.html" else f'{title} | {S["name"]}'
    nav = "".join(f'<a class="tag" href="{f}"{" aria-current=\"page\"" if f == file else ""}>{l}</a>' for l, f in PAGES)
    open(file, "w", encoding="utf-8").write(f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(full)}</title><meta name="description" content="{e(desc)}"><meta name="author" content="{e(S["name"])}">
<link rel="canonical" href="{URL}{path}"><meta name="theme-color" content="#0e6b78">
<meta property="og:type" content="website"><meta property="og:title" content="{e(full)}"><meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{URL}{path}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;600&family=Newsreader:wght@400;500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="style.css">{extra}</head>
<body><header id="nav"><a class="brand" href="index.html">{e(S["name"])}</a><nav aria-label="Main">{nav}</nav></header>
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
        fig, body = p.get("figure") or {}, "".join(f"<p>{e(x)}</p>" for x in p.get("summary", "").split("\n\n") if x.strip())
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

def photos(items):
    out = ""
    for p in items:
        s = p.get("src", "").lstrip("/")
        if not s or not os.path.exists(s): continue
        det = f"<span>{e(p['details'])}</span>" if p.get("details") else ""
        out += (f'<figure class="photo" itemscope itemtype="https://schema.org/ImageObject"><a href="{e(s)}">'
                f'<img loading="lazy" itemprop="contentUrl" src="{e(s)}" alt="{e(p.get("alt") or p.get("title", ""))}"></a>'
                f'<figcaption><strong itemprop="name">{e(p.get("title", ""))}</strong>{det}</figcaption></figure>')
    return f'<div class="gallery">{out}</div>' if out else ""

# Home
media = S.get("hero_media", "").lstrip("/")
if media and not os.path.exists(media): media = ""   # file not uploaded yet: fall back to the animation
poster = S.get("hero_poster", "").lstrip("/")
if media.endswith((".mp4", ".webm")):
    pa = f' poster="{e(poster)}"' if poster and os.path.exists(poster) else ""
    stage = f'<div class="stage media"><video src="{e(media)}"{pa} loop muted playsinline{" controls" if S.get("hero_controls") else " disablepictureinpicture"} preload="metadata"></video></div>'
elif media: stage = f'<div class="stage media"><img src="{e(media)}" alt="{e(S.get("hero_alt", "Illustration of my research"))}"></div>'
else: stage = '<div class="stage"><canvas id="stage" role="img" aria-label="Animated network of drifting points"></canvas></div>'
figs = "".join(
    f'<figure>{"<img loading=lazy src=%s alt=%s>" % (chr(34)+e(f["src"])+chr(34), chr(34)+e(f["alt"])+chr(34)) if os.path.exists(f["src"]) else "<div class=ph>" + e(f["src"]) + "</div>"}'
    f'<figcaption>{e(f["caption"])}</figcaption></figure>' for f in D["figures"])
_r = S["role"].rsplit(", ", 1)   # keep the last part (the institution) on one line
role_html = f'{e(_r[0])}, <span style="white-space:nowrap">{e(_r[1])}</span>' if len(_r) == 2 else e(S["role"])
delay = int(float(S.get("hero_delay", 2.5)) * 1000)   # seconds before the video starts, set "hero_delay" in data.json
if not media: herojs = '<script src="anim.js" defer></script>'
elif media.endswith((".mp4", ".webm")):
    herojs = ("<script>var v=document.querySelector('.stage video');"
              "if(v&&!matchMedia('(prefers-reduced-motion: reduce)').matches)setTimeout(function(){v.play().catch(function(){})}," + str(delay) + ");</script>")
else: herojs = ""
person = json.dumps({"@context": "https://schema.org", "@type": "Person", "name": S["name"], "jobTitle": S["role"], "url": URL + "/",
                     "email": S["email"], "sameAs": [l["url"] for l in S["links"]]})
page("index.html", "Home", S["description"], f'''<section class="hero"><div><h1>{e(S["name"])}</h1><p class="role">{role_html}</p>
<p>{e(S["intro"])}</p><p class="links">{links(S["links"])}</p></div>{stage}</section>
{'<section><h2>Figures from my research</h2><div class="figs">' + figs + '</div></section>' if figs else ''}
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
