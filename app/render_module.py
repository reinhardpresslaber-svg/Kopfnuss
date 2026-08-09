"""
Kopfnuss Render-Modul
======================
Baut aus 9 Slide-Inhalten die interaktive HTML-Vorschau sowie die 9 einzelnen
Export-HTMLs (spaeter per wkhtmltoimage zu PNG konvertiert).

Gleiche Logik wie das urspruengliche Projektvorgaben/build_carousel.py, aber
als aufrufbare Funktion statt Skript mit fest eingetragenen Texten.
"""

import html as html_module
import os
import re

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

with open(os.path.join(ASSETS_DIR, "style_with_icon.css"), encoding="utf-8") as f:
    STYLE_BLOCK = f.read()
with open(os.path.join(ASSETS_DIR, "logo_full_transparent_b64.txt")) as f:
    LOGO_B64 = f.read().strip()

# Gruenes Farbthema: ueberschreibt nur die Akzentfarben (--rust, --gold, --moss).
# Leerer String = klassisches Terrakotta/Gold-Theme (Standard-CSS unveraendert).
GREEN_THEME_OVERRIDE = """
:root{
  --rust: #235C3D;
  --gold: #4C7A40;
  --moss: #6FA283;
}
.blob{
  opacity: 0.34;
}
"""

THEMES = {
    "klassisch": "",
    "gruen": GREEN_THEME_OVERRIDE,
}

BGMAP = {"bg": "#FBF6EF", "bg-alt": "#F2E6D3"}

BOOKMARK_ICON_SVG = (
    '<svg width="30" height="30" viewBox="0 0 24 24" fill="none" '
    'stroke="currentColor" stroke-width="2.4" stroke-linecap="round" '
    'stroke-linejoin="round" style="flex-shrink:0; vertical-align:-6px;">'
    '<path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>'
    '</svg>'
)

SHARE_ICON_SVG = (
    '<svg width="30" height="30" viewBox="0 0 24 24" fill="none" '
    'stroke="currentColor" stroke-width="2.4" stroke-linecap="round" '
    'stroke-linejoin="round" style="flex-shrink:0;">'
    '<path d="M22 2 11 13"/>'
    '<path d="M22 2 15 22 11 13 2 9 22 2Z"/>'
    '</svg>'
)

REPOST_ICON_SVG = (
    '<svg width="30" height="30" viewBox="0 0 24 24" fill="currentColor" '
    'style="flex-shrink:0;">'
    '<path d="M7 7h10v3l5-4-5-4v3H5v6h2V7zm10 10H7v-3l-5 4 5 4v-3h12v-6h-2v4z"/>'
    '</svg>'
)

FOLLOW_ICON_SVG = (
    '<svg width="30" height="30" viewBox="0 0 24 24" fill="none" '
    'stroke="currentColor" stroke-width="2.4" stroke-linecap="round" '
    'stroke-linejoin="round" style="flex-shrink:0; vertical-align:-6px;">'
    '<path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>'
    '<circle cx="8.5" cy="7" r="4"/>'
    '<line x1="20" y1="8" x2="20" y2="14"/>'
    '<line x1="23" y1="11" x2="17" y2="11"/>'
    '</svg>'
)

# Farbe fest auf --ink gesetzt (statt currentColor), damit das Herz
# garantiert dunkel/schwarz bleibt statt in Emoji-Rot zu erscheinen.
HEART_ICON_SVG = (
    '<svg width="20" height="20" viewBox="0 0 24 24" fill="#2C2420" '
    'style="flex-shrink:0; vertical-align:-3px; margin-left:4px;">'
    '<path d="M12 21s-7.44-4.35-10-9.03C0.28 8.62 1.7 5 5.4 5c2.1 0 3.6 1.2 4.6 2.73'
    'C11 6.2 12.5 5 14.6 5c3.7 0 5.12 3.62 3.4 6.97C19.44 16.65 12 21 12 21z"/>'
    '</svg>'
)

# Vordefinierte, alternierende Hintergrund-"Blobs" fuer die 9 Slides.
BLOBS = [
    '<div class="blob" style="width:640px;height:640px;background:var(--rust);top:-180px;right:-200px;"></div><div class="blob" style="width:420px;height:420px;background:var(--gold);bottom:-140px;left:-140px;"></div>',
    '<div class="blob" style="width:500px;height:500px;background:var(--moss);top:-160px;left:-180px;"></div>',
    '<div class="blob" style="width:460px;height:460px;background:var(--gold);top:-140px;right:-160px;"></div>',
    '<div class="blob" style="width:520px;height:520px;background:var(--rust);bottom:-180px;right:-160px;"></div>',
    '<div class="blob" style="width:460px;height:460px;background:var(--moss);top:-140px;left:-160px;"></div>',
    '<div class="blob" style="width:480px;height:480px;background:var(--gold);bottom:-160px;left:-160px;"></div>',
    '<div class="blob" style="width:500px;height:500px;background:var(--rust);top:-160px;right:-180px;"></div>',
    '<div class="blob" style="width:460px;height:460px;background:var(--moss);bottom:-140px;right:-160px;"></div>',
    '<div class="blob" style="width:640px;height:640px;background:var(--gold);bottom:-220px;left:-200px;"></div><div class="blob" style="width:380px;height:380px;background:var(--rust);top:-140px;right:-140px;"></div>',
]
BGS = ["bg", "bg-alt", "bg", "bg-alt", "bg", "bg-alt", "bg", "bg-alt", "bg"]


def build_cover_slide(cover_frage, bild_b64=None):
    """Baut Slide 1 (Cover): Logo + Cover-Frage, optional mit generiertem
    Motiv als zusaetzliche Bildebene (zwischen den Blobs und dem Text)."""
    bild_layer = ""
    if bild_b64:
        bild_layer = (
            f'<img src="data:image/png;base64,{bild_b64}" alt="" '
            f'style="position:absolute; top:-90px; left:-84px; width:1080px; height:1350px; '
            f'object-fit:contain; opacity:0.5; z-index:1; pointer-events:none;"/>'
        )
    return {
        "eyebrow": "01 / 09",
        "body": f'''
        {bild_layer}
        <div class="content-mid" style="align-items:flex-start;">
          <img class="cover-logo" src="data:image/png;base64,{LOGO_B64}" alt="Kopfnuss Logo"/>
          <div class="headline" style="font-size:56px; margin-top:30px;">{cover_frage}</div>
        </div>
        ''',
        "footer": "@KopfnussPsychologie",
    }


def build_cta_slide(fazit_html):
    """Baut Slide 9 (Fazit + CTA): fazit_html ist der freie Fazit-Text, Rest (Icons/Claim) ist fest."""
    return {
        "eyebrow": "09 / 09 &mdash; Fazit",
        "body": f'''
        <div class="content-mid">
          <div class="headline">Fazit</div>
          {fazit_html}
          <p class="cta-line" style="margin-top:45px;">{BOOKMARK_ICON_SVG} Speichern</p>
          <p class="cta-line" style="margin-top:14px;">{SHARE_ICON_SVG} Interessant? Danke f&uuml;rs Teilen {HEART_ICON_SVG}</p>
          <p class="cta-line" style="margin-top:14px;">{REPOST_ICON_SVG} Interessant? Danke f&uuml;rs Reposten {HEART_ICON_SVG}</p>
          <p class="cta-line" style="margin-top:14px;">{FOLLOW_ICON_SVG} Folge @KopfnussPsychologie</p>
          <p class="cta-line" style="margin-top:2px;">Wissenswertes aus Psychologie &amp; Coaching</p>
        </div>
        ''',
        "footer": "@KopfnussPsychologie",
    }


def make_slide_div(i, s, active=False):
    active_cls = " active" if active else ""
    bg = BGS[i]
    blobs = BLOBS[i]
    nutmark = '<div class="nutmark" style="position:absolute; top:80px; right:84px; width:74px; height:74px; z-index:3;"></div>'
    return f'''
    <div class="slide{active_cls}" data-bg="{bg}" id="slide-{i}">
      <div class="frame">
        {blobs}
        {nutmark if i != 0 else ''}
        <div class="eyebrow">{s['eyebrow']}</div>
        {s['body']}
        <div class="footer-brand"><div class="line"></div><span>{s['footer']}</span></div>
      </div>
    </div>'''


def render_carousel(slides, topic_slug, topic_title, theme="klassisch", output_dir=None):
    """
    Baut die interaktive HTML-Vorschau und die 9 Export-HTMLs fuer ein Karussell.

    slides: Liste von genau 9 Dicts mit "eyebrow", "body" (HTML-String) und
            optional "footer". Slide 1 und Slide 9 lassen sich bequem mit
            build_cover_slide() / build_cta_slide() erzeugen.
    topic_slug: kurzer Bezeichner fuer Dateinamen (z.B. "tsst-vr")
    topic_title: Titel fuer die Vorschau-Seite (z.B. "Open TSST-VR")
    theme: "klassisch" oder "gruen"
    output_dir: Zielordner fuer die erzeugten Dateien (Standard: aktueller Ordner)

    Gibt ein Dict mit den erzeugten Pfaden zurueck.
    """
    if len(slides) != 9:
        raise ValueError(f"Es werden genau 9 Slides erwartet, bekommen: {len(slides)}")
    if theme not in THEMES:
        raise ValueError(f"Unbekanntes Theme '{theme}', erlaubt: {list(THEMES)}")

    green_override = THEMES[theme]
    output_dir = output_dir or os.getcwd()
    os.makedirs(output_dir, exist_ok=True)

    slides_html_viewer = "\n".join(make_slide_div(i, s, active=(i == 0)) for i, s in enumerate(slides))

    viewer_template = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<title>Kopfnuss &ndash; {topic_title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,900&family=Karla:ital,wght@0,400;0,500;0,700;1,400&display=swap" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
<style>
{STYLE_BLOCK}
{green_override}
</style>
</head>
<body>
<div class="app">
  <h1 class="app-title">&#129358; Kopfnuss</h1>
  <p class="app-sub">Karussell: {topic_title} &mdash; 9 Slides, Format 4:5</p>

  <div class="preview-wrap" id="previewWrap">
{slides_html_viewer}
  </div>

  <div class="controls">
    <button onclick="go(-1)" aria-label="Vorherige Slide">&lsaquo;</button>
    <div class="counter" id="counter">1 / 9</div>
    <button onclick="go(1)" aria-label="N&auml;chste Slide">&rsaquo;</button>
  </div>

  <div class="dots" id="dots"></div>

  <div class="actions">
    <button onclick="downloadCurrent()">Slide als PNG</button>
    <button class="primary" onclick="downloadAll()">Alle 9 als PNG</button>
  </div>
  <p class="hint">Export erzeugt 1080&times;1350 px PNGs &mdash; passend f&uuml;r Instagram-Karussells (4:5).</p>
</div>

<script>
  const slides = document.querySelectorAll('.slide');
  const bgMap = {{ bg: '#FBF6EF', 'bg-alt': '#F2E6D3' }};
  let current = 0;

  function applyBg(el){{ el.style.background = bgMap[el.dataset.bg] || '#FBF6EF'; }}
  slides.forEach(applyBg);

  const dotsWrap = document.getElementById('dots');
  slides.forEach((_, i) => {{
    const d = document.createElement('span');
    if(i===0) d.classList.add('active');
    d.onclick = () => {{ current = i; render(); }};
    dotsWrap.appendChild(d);
  }});

  function render(){{
    slides.forEach((s, i) => s.classList.toggle('active', i === current));
    document.getElementById('counter').textContent = (current+1) + ' / ' + slides.length;
    [...dotsWrap.children].forEach((d, i) => d.classList.toggle('active', i === current));
  }}

  function go(delta){{
    current = (current + delta + slides.length) % slides.length;
    render();
  }}

  function captureSlide(el){{
    return new Promise((resolve) => {{
      const clone = el.cloneNode(true);
      clone.style.transform = 'none';
      clone.style.display = 'block';
      clone.style.position = 'fixed';
      clone.style.left = '-99999px';
      clone.style.top = '0';
      applyBg(clone);
      document.body.appendChild(clone);
      html2canvas(clone, {{ width: 1080, height: 1350, scale: 1, useCORS: true }}).then(canvas => {{
        document.body.removeChild(clone);
        resolve(canvas);
      }});
    }});
  }}

  function triggerDownload(canvas, filename){{
    const link = document.createElement('a');
    link.download = filename;
    link.href = canvas.toDataURL('image/png');
    link.click();
  }}

  function downloadCurrent(){{
    captureSlide(slides[current]).then(canvas => {{
      triggerDownload(canvas, `kopfnuss-slide-${{current+1}}.png`);
    }});
  }}

  async function downloadAll(){{
    for(let i=0; i<slides.length; i++){{
      const canvas = await captureSlide(slides[i]);
      triggerDownload(canvas, `kopfnuss-slide-${{i+1}}.png`);
      await new Promise(r => setTimeout(r, 350));
    }}
  }}

  render();
</script>
</body>
</html>"""

    preview_path = os.path.join(output_dir, f"carousel_{topic_slug}.html")
    with open(preview_path, "w", encoding="utf-8") as f:
        f.write(viewer_template)

    export_dir = os.path.join(output_dir, f"slides_export_{topic_slug}")
    os.makedirs(export_dir, exist_ok=True)

    export_template = """<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,900&family=Karla:ital,wght@0,400;0,500;0,700;1,400&display=swap" rel="stylesheet">
<style>
{style}
{green_override}
html,body{{ margin:0; padding:0; }}
.slide{{ display:block !important; transform:none !important; width:1080px !important; height:1350px !important; background:{bg} !important; }}
</style>
</head>
<body>
{slide_html}
</body>
</html>"""

    slide_html_paths = []
    for i, s in enumerate(slides):
        bg_color = BGMAP[BGS[i]]
        slide_div = make_slide_div(i, s, active=True)
        html = export_template.format(style=STYLE_BLOCK, green_override=green_override, bg=bg_color, slide_html=slide_div)
        slide_path = os.path.join(export_dir, f"slide-{i + 1}.html")
        with open(slide_path, "w", encoding="utf-8") as f:
            f.write(html)
        slide_html_paths.append(slide_path)

    return {
        "preview_html": preview_path,
        "export_dir": export_dir,
        "slide_htmls": slide_html_paths,
    }


def render_cover_preview_html(cover_frage, bild_b64=None, theme="klassisch"):
    """
    Baut eine kompakte Vorschau NUR von Slide 1 (Cover) - z.B. um ein
    generiertes Cover-Bild direkt im Zusammenspiel mit Logo/Ueberschrift
    zu pruefen, ohne gleich alle 9 Slides generieren zu muessen.
    """
    green_override = THEMES[theme]
    slide = build_cover_slide(cover_frage, bild_b64=bild_b64)
    slide_html = make_slide_div(0, slide, active=True)
    return f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,900&family=Karla:ital,wght@0,400;0,500;0,700;1,400&display=swap" rel="stylesheet">
<style>
{STYLE_BLOCK}
{green_override}
html, body{{ margin:0; padding:0; background:transparent; }}
body{{ display:flex; justify-content:center; }}
</style>
</head>
<body>
<div class="preview-wrap">
{slide_html}
</div>
</body>
</html>"""


def export_pngs(slide_html_paths):
    """
    Wandelt die Export-HTML-Dateien einer Slide-Liste (aus render_carousel(),
    "slide_htmls") in echte PNG-Dateien um - per Playwright (ein unsichtbarer
    Chrome-Browser macht einen 1080x1350px-Screenshot jeder Slide).

    Gibt die Liste der erzeugten PNG-Pfade zurueck (gleicher Ordner, gleicher
    Dateiname, nur mit .png statt .html).
    """
    from pathlib import Path

    from playwright.sync_api import sync_playwright

    png_paths = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1080, "height": 1350})
        for html_path in slide_html_paths:
            page.goto(Path(html_path).resolve().as_uri())
            page.wait_for_load_state("networkidle")
            png_path = os.path.splitext(html_path)[0] + ".png"
            page.screenshot(path=png_path)
            png_paths.append(png_path)
        browser.close()
    return png_paths


_INLINE_TAG_RE = re.compile(r"</?(?:em|strong|b|i)>", re.IGNORECASE)


def _strip_inline_tags(text):
    """
    Entfernt vereinzelte Formatierungs-Tags (<em>, <strong>, <b>, <i>), die
    Claude gelegentlich trotz Prompt-Anweisung in den Text mischt. Die
    Text-Bearbeitung ist als reines Plaintext-Feld gedacht - ohne diesen
    Schritt wuerden solche Tags beim naechsten Rendern als sichtbarer Text
    ("<em>...</em>") statt als Formatierung erscheinen.
    """
    return _INLINE_TAG_RE.sub("", text)


_TRIO_ITEM_RE = re.compile(r'<div class="item"><h4>(.*?)</h4><p>(.*?)</p></div>', re.DOTALL)
_HEADLINE_RE = re.compile(r'<div class="headline"[^>]*>(?P<headline>.*?)</div>', re.DOTALL)
_CARD_RE = re.compile(
    r'<div class="content-mid"[^>]*>\s*<div class="headline"[^>]*>(?P<headline>.*?)</div>\s*'
    r'<div class="card">\s*<p class="body-text"[^>]*>(?P<body>.*?)</p>\s*</div>\s*</div>',
    re.DOTALL,
)
_SIMPLE_RE = re.compile(
    r'<div class="content-mid"[^>]*>\s*<div class="headline"[^>]*>(?P<headline>.*?)</div>\s*'
    r'<p class="body-text"[^>]*>(?P<body>.*?)</p>\s*</div>',
    re.DOTALL,
)


def parse_slide_body(body_html):
    """
    Zerlegt den HTML-Body einer Slide (2-8) in einfache Textfelder zur
    Bearbeitung - erkennt die 3 Baukasten-Varianten aus text_module.py
    (einfacher Text, Beispiel-Karte, Drei-Punkte-Vergleich). Unbekannte
    Struktur wird unveraendert als Rohtext durchgereicht (type "raw"),
    damit nichts verloren geht.
    """
    if '<div class="trio">' in body_html:
        items = _TRIO_ITEM_RE.findall(body_html)
        headline_m = _HEADLINE_RE.search(body_html)
        if len(items) == 3 and headline_m:
            return {
                "type": "trio",
                "headline": _strip_inline_tags(html_module.unescape(headline_m.group("headline")).strip()),
                "items": [
                    {
                        "titel": _strip_inline_tags(html_module.unescape(t).strip()),
                        "text": _strip_inline_tags(html_module.unescape(p).strip()),
                    }
                    for t, p in items
                ],
            }
    if '<div class="card">' in body_html:
        m = _CARD_RE.search(body_html)
        if m:
            return {
                "type": "card",
                "headline": _strip_inline_tags(html_module.unescape(m.group("headline")).strip()),
                "body": _strip_inline_tags(html_module.unescape(m.group("body")).strip()),
            }
    m = _SIMPLE_RE.search(body_html)
    if m:
        return {
            "type": "simple",
            "headline": _strip_inline_tags(html_module.unescape(m.group("headline")).strip()),
            "body": _strip_inline_tags(html_module.unescape(m.group("body")).strip()),
        }
    return {"type": "raw", "html": body_html}


def build_slide_body(parsed):
    """Baut aus den (moeglicherweise bearbeiteten) Textfeldern wieder den
    HTML-Body zusammen - Gegenstueck zu parse_slide_body()."""
    if parsed["type"] == "trio":
        items_html = "".join(
            f'<div class="item"><h4>{html_module.escape(item["titel"])}</h4>'
            f'<p>{html_module.escape(item["text"])}</p></div>'
            for item in parsed["items"]
        )
        return (
            '<div class="content-mid">\n'
            f'  <div class="headline">{html_module.escape(parsed["headline"])}</div>\n'
            f'  <div class="trio">{items_html}</div>\n'
            "</div>"
        )
    if parsed["type"] == "card":
        return (
            '<div class="content-mid">\n'
            f'  <div class="headline">{html_module.escape(parsed["headline"])}</div>\n'
            '  <div class="card">\n'
            f'    <p class="body-text" style="margin-top:0;">{html_module.escape(parsed["body"])}</p>\n'
            "  </div>\n"
            "</div>"
        )
    if parsed["type"] == "simple":
        return (
            '<div class="content-mid">\n'
            f'  <div class="headline">{html_module.escape(parsed["headline"])}</div>\n'
            f'  <p class="body-text">{html_module.escape(parsed["body"])}</p>\n'
            "</div>"
        )
    return parsed["html"]


_FAZIT_RE = re.compile(r'<p class="body-text"[^>]*>(?P<body>.*?)</p>', re.DOTALL)


def parse_fazit_body(fazit_html):
    """Extrahiert den reinen Text aus dem Fazit-Paragraph (Slide 9)."""
    m = _FAZIT_RE.search(fazit_html)
    if m:
        return _strip_inline_tags(html_module.unescape(m.group("body")).strip())
    return fazit_html


def build_fazit_body(text):
    """Baut den Fazit-Paragraph (Slide 9) aus reinem Text - Gegenstueck
    zu parse_fazit_body()."""
    return f'<p class="body-text">{html_module.escape(text)}</p>'
