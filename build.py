"""Run `python3 build.py` after editing data.json. Writes static HTML, sitemap.xml, robots.txt."""
import json, os, html
from datetime import date
D = json.load(open("data.json", encoding="utf-8")); S = D["site"]
e = html.escape; URL = S["url"].rstrip("/")
PAGES = [("Home", "index.html"), ("Publications", "publications.html"), ("Posters", "posters.html"), ("CV", "cv.html")]
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

# Home
media = S["hero_media"]
if media.endswith((".mp4", ".webm")): stage = f'<div class="stage"><video src="{e(media)}" autoplay loop muted playsinline></video></div>'
elif media: stage = f'<div class="stage"><img src="{e(media)}" alt="Illustration of my research"></div>'
else: stage = '<div class="stage"><canvas id="stage" role="img" aria-label="Animated network of drifting points"></canvas></div>'
figs = "".join(
    f'<figure>{"<img loading=lazy src=%s alt=%s>" % (chr(34)+e(f["src"])+chr(34), chr(34)+e(f["alt"])+chr(34)) if os.path.exists(f["src"]) else "<div class=ph>" + e(f["src"]) + "</div>"}'
    f'<figcaption>{e(f["caption"])}</figcaption></figure>' for f in D["figures"])
person = json.dumps({"@context": "https://schema.org", "@type": "Person", "name": S["name"], "jobTitle": S["role"], "url": URL + "/",
                     "email": S["email"], "sameAs": [l["url"] for l in S["links"]]})
page("index.html", "Home", S["description"], f'''<section class="hero"><div><h1>{e(S["name"])}</h1><p class="role">{e(S["role"])}</p>
<p>{e(S["intro"])}</p><p class="links">{links(S["links"])}</p></div>{stage}</section>
<section><h2>Figures from my research</h2><div class="figs">{figs}</div></section>
{'<script src="anim.js" defer></script>' if not media else ''}''', f'<script type="application/ld+json">{person}</script>')

page("publications.html", "Publications", f'Peer-reviewed papers and preprints by {S["name"]}.',
     '<h1 class="page-title">Publications</h1>' + by_year(D["publications"], "ScholarlyArticle"))
page("posters.html", "Posters", f'Conference posters by {S["name"]}.',
     '<h1 class="page-title">Posters</h1>' + by_year(D["posters"], "CreativeWork"))
cv = "".join(f'<section class="year"><h2>{e(s["title"])}</h2><div>' + "".join(
    f'<article class="entry"><span class="when">{e(i["when"])}</span><h3>{e(i["what"])}</h3><p>{e(i["where"])}</p></article>'
    for i in s["items"]) + "</div></section>" for s in D["cv"])
page("cv.html", "CV", f'Curriculum vitae of {S["name"]}: education, experience and awards.',
     f'<h1 class="page-title">CV</h1><a class="btn" href="{e(S["cv_pdf"])}">Download CV (PDF)</a>' + cv)

open("sitemap.xml", "w").write('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' +
    "".join(f'<url><loc>{URL}{"/" if f=="index.html" else "/"+f}</loc><lastmod>{date.today()}</lastmod></url>' for _, f in PAGES) + "</urlset>")
open("robots.txt", "w").write(f"User-agent: *\nAllow: /\nSitemap: {URL}/sitemap.xml\n")
print("Built:", ", ".join(f for _, f in PAGES))
