"""
Kopfnuss Karussell-Generator
============================
Wiederverwendbares Script fuer neue Instagram-Karussell-Posts im Kopfnuss-Design.

BENUTZUNG:
1. Unten bei "SLIDES BEFUELLEN" die 9 Slides mit neuem Inhalt ueberschreiben.
2. TOPIC_SLUG anpassen (z.B. "eustress", "lazarus", "gelernte-hilflosigkeit")
   -> wird fuer Dateinamen verwendet.
3. Script ausfuehren: python3 build_carousel.py
   Erzeugt:
     - carousel_<TOPIC_SLUG>.html          (interaktive Vorschau zum Durchklicken)
     - slides_export_<TOPIC_SLUG>/slide-1.html ... slide-9.html  (fuer PNG-Export)
4. Jede slide-N.html rendern:
     wkhtmltoimage --width 1080 --height 1350 --disable-smart-width slide-N.html slide-N.png

BENOETIGTE DATEIEN IM SELBEN ORDNER:
- style_with_icon.css          (CSS inkl. eingebettetem Logo-Icon)
- logo_full_transparent_b64.txt (Base64 des grossen Logos fuer Slide 1)

FARBTHEMA (nur fuer diesen Post):
Dieser Post nutzt eine gruene Akzentfarbe statt der Standard-Terrakotta/Gold-Kombi
aus dem Design-System. Das Basis-CSS (style_with_icon.css) bleibt dabei unveraendert;
die Akzentfarben werden ueber eine kleine CSS-Variablen-Ueberschreibung (GREEN_THEME_OVERRIDE)
nur fuer die Slides dieses Posts angepasst.
"""

import os

# ---------------------------------------------------------------------------
# KONFIGURATION
# ---------------------------------------------------------------------------
TOPIC_SLUG = "tsst-vr"
TOPIC_TITLE = "Open TSST-VR"

# ---------------------------------------------------------------------------
# ASSETS LADEN (nicht aendern)
# ---------------------------------------------------------------------------
with open('style_with_icon.css', encoding='utf-8') as f:
    style_block = f.read()
with open('logo_full_transparent_b64.txt') as f:
    logo_b64 = f.read().strip()

# Gruenes Farbthema fuer diesen Post: ueberschreibt nur die Akzentfarben
# (--rust und --gold), die im Standard-CSS fuer Eyebrow-Label, Footer-Linie,
# Trio-Rahmen und Blobs verwendet werden. --moss und --forest (bereits gruen)
# bleiben unveraendert.
GREEN_THEME_OVERRIDE = """
:root{
  --rust: #235C3D;   /* ersetzt Terrakotta durch kraeftiges, dunkles Tannengruen */
  --gold: #4C7A40;   /* ersetzt Gold durch kraeftiges Olivgruen */
  --moss: #6FA283;   /* etwas kraeftigeres Salbeigruen als Standard */
}
/* Blobs im Standard-CSS sind auf 16% Deckkraft gesetzt und wirken dadurch
   blass. Fuer den kraeftigeren Look hier hoeher gesetzt. */
.blob{
  opacity: 0.34;
}
"""

bgmap = {"bg": "#FBF6EF", "bg-alt": "#F2E6D3"}

# Instagram-typisches Speichern-Icon (Bookmark-Umriss) als Inline-SVG.
# Erbt die Textfarbe (stroke="currentColor") und passt sich damit automatisch
# an cta-line an. Wiederverwendbar fuer Slide 9 in jedem neuen Post.
BOOKMARK_ICON_SVG = (
    '<svg width="30" height="30" viewBox="0 0 24 24" fill="none" '
    'stroke="currentColor" stroke-width="2.4" stroke-linecap="round" '
    'stroke-linejoin="round" style="flex-shrink:0; vertical-align:-6px;">'
    '<path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>'
    '</svg>'
)

# Instagram-typisches Teilen-Icon (Papierflieger-Umriss) als Inline-SVG.
# Erbt die Textfarbe (stroke="currentColor"). Gehoert zusammen mit
# REPOST_ICON_SVG in die .cta-row auf Slide 9 (siehe unten).
SHARE_ICON_SVG = (
    '<svg width="30" height="30" viewBox="0 0 24 24" fill="none" '
    'stroke="currentColor" stroke-width="2.4" stroke-linecap="round" '
    'stroke-linejoin="round" style="flex-shrink:0;">'
    '<path d="M22 2 11 13"/>'
    '<path d="M22 2 15 22 11 13 2 9 22 2Z"/>'
    '</svg>'
)

# Repost-Icon (zwei gegenlaeufige Pfeile, wie bei Instagram-Reposts) als
# Inline-SVG. Anders als die Umriss-Icons ist dieses Symbol im Original
# durchgehend gefuellt, daher fill="currentColor" statt stroke.
REPOST_ICON_SVG = (
    '<svg width="30" height="30" viewBox="0 0 24 24" fill="currentColor" '
    'style="flex-shrink:0;">'
    '<path d="M7 7h10v3l5-4-5-4v3H5v6h2V7zm10 10H7v-3l-5 4 5 4v-3h12v-6h-2v4z"/>'
    '</svg>'
)

# Vordefinierte, alternierende Hintergrund-"Blobs" fuer die 9 Slides.
# Kann 1:1 uebernommen werden, muss nicht pro Post neu erfunden werden.
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


def slide(eyebrow, body_html, footer="@KopfnussPsychologie"):
    """Hilfsfunktion: baut ein Slide-Dict. bg/blobs werden automatisch nach Position vergeben."""
    return {"eyebrow": eyebrow, "body": body_html, "footer": footer}


# ---------------------------------------------------------------------------
# SLIDES BEFUELLEN
# ---------------------------------------------------------------------------
SLIDES = []

# --- Slide 1: Cover mit catchy Frage ---
cover_frage = "Kannst du dich in einer virtuellen Welt genauso stressen wie im echten Leben?"
SLIDES.append({
    "eyebrow": "01 / 09",
    "body": f'''
    <div class="content-mid" style="align-items:flex-start;">
      <img class="cover-logo" src="data:image/png;base64,{logo_b64}" alt="Kopfnuss Logo"/>
      <div class="headline" style="font-size:56px; margin-top:30px;">{cover_frage}</div>
    </div>
    ''',
    "footer": "@KopfnussPsychologie"
})

# --- Slide 2: Beispiel ---
SLIDES.append(slide("02 / 09 &mdash; Beispiel", '''
<div class="content-mid">
  <div class="headline">Stell dir vor:</div>
  <div class="card">
    <p class="body-text" style="margin-top:0;">Du sitzt mit einer VR-Brille im Labor. Deine Aufgabe: Halte spontan eine &Uuml;berzeugungsrede vor einer Jury &ndash; die Jury sitzt nicht im Raum, sie existiert nur in deinem Headset.</p>
  </div>
</div>
'''))

# --- Slide 3: Kerngedanke / Definition ---
SLIDES.append(slide("03 / 09", '''
<div class="content-mid">
  <div class="headline">Der Klassiker unter Stresstests</div>
  <p class="body-text">Der Trier Social Stress Test (TSST) gilt seit den 1990ern als Goldstandard, um im Labor echten Stress auszul&ouml;sen: freie Rede und Kopfrechnen vor einer kritischen Jury. Katrin Linnig und Kolleg:innen (2024) haben nun eine frei verf&uuml;gbare VR-Version entwickelt und getestet &ndash; den Open TSST-VR.</p>
</div>
'''))

# --- Slide 4: Mechanismus Teil 1 ---
SLIDES.append(slide("04 / 09", '''
<div class="content-mid">
  <div class="headline">Warum &uuml;berhaupt VR?</div>
  <p class="body-text">Die klassische Version ist aufwendig: Sie braucht echte Pr&uuml;fer:innen und reagiert empfindlich auf kleinste Unterschiede in deren Verhalten. Das erschwert es, Studien weltweit zu vergleichen.</p>
</div>
'''))

# --- Slide 5: Mechanismus Teil 2 (Studiendesign) ---
SLIDES.append(slide("05 / 09", '''
<div class="content-mid">
  <div class="headline">So lief die Studie</div>
  <p class="body-text">50 M&auml;nner wurden zuf&auml;llig entweder der TSST-VR-Gruppe oder einer neutralen VR-Kontrollbedingung zugeteilt. Gemessen wurden Herzrate, Speichelcortisol und subjektives Stressempfinden &ndash; vor und nach der Aufgabe.</p>
</div>
'''))

# --- Slide 6: Vertiefung (Ergebnis) ---
SLIDES.append(slide("06 / 09", '''
<div class="content-mid">
  <div class="headline">Und, hat's funktioniert?</div>
  <p class="body-text">Ja: Die Stressgruppe zeigte einen deutlich st&auml;rkeren Anstieg von subjektivem Stress <strong>und</strong> Cortisol als die Kontrollgruppe. Der K&ouml;rper reagierte also wirklich biologisch &ndash; nicht nur gef&uuml;hlt.</p>
</div>
'''))

# --- Slide 7: Kernaussage / Zuspitzung ---
SLIDES.append(slide("07 / 09", '''
<div class="content-mid">
  <div class="headline">Dein K&ouml;rper macht keinen Unterschied</div>
  <p class="body-text">Eine virtuelle Jury kann eine genauso echte Stressreaktion ausl&ouml;sen wie eine echte. F&uuml;r dein Nervensystem z&auml;hlt offenbar vor allem: Werde ich gerade bewertet?</p>
</div>
'''))

# --- Slide 8: Warum relevant ---
SLIDES.append(slide("08 / 09", '''
<div class="content-mid">
  <div class="headline">Warum dich das interessieren sollte</div>
  <p class="body-text">Ein g&uuml;nstigerer, besser standardisierbarer Stresstest hilft der Forschung zu Burnout, Angstst&ouml;rungen und Therapieans&auml;tzen &ndash; weltweit vergleichbar, ohne Jury-Kosten.</p>
</div>
'''))

# --- Slide 9: Fazit + offizieller CTA (Claim nicht aendern!) ---
SLIDES.append(slide("09 / 09 &mdash; Fazit", f'''
<div class="content-mid">
  <div class="headline">Fazit</div>
  <p class="body-text">Selbst virtuelle Bewertung geht &bdquo;unter die Haut&ldquo; &ndash; dein K&ouml;rper reagiert, als w&auml;re sie echt.</p>
  <p class="cta-line">{BOOKMARK_ICON_SVG} Speichern</p>
  <div class="cta-row">
    <span class="cta-item">{SHARE_ICON_SVG} Teilen</span>
    <span class="cta-item">{REPOST_ICON_SVG} Repost</span>
  </div>
  <p class="cta-line" style="margin-top:6px;">&#128073; Folge @KopfnussPsychologie | Wissenswertes aus Psychologie &amp; Coaching</p>
</div>
'''))

# ---------------------------------------------------------------------------
# AB HIER NICHTS MEHR AENDERN (reine Generierungslogik)
# ---------------------------------------------------------------------------

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


slides_html_viewer = "\n".join(make_slide_div(i, s, active=(i == 0)) for i, s in enumerate(SLIDES))

viewer_template = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<title>Kopfnuss &ndash; {TOPIC_TITLE}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,900&family=Karla:ital,wght@0,400;0,500;0,700;1,400&display=swap" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
<style>
{style_block}
{GREEN_THEME_OVERRIDE}
</style>
</head>
<body>
<div class="app">
  <h1 class="app-title">&#129358; Kopfnuss</h1>
  <p class="app-sub">Karussell: {TOPIC_TITLE} &mdash; 9 Slides, Format 4:5</p>

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

with open(f'carousel_{TOPIC_SLUG}.html', 'w', encoding='utf-8') as f:
    f.write(viewer_template)

export_dir = f'slides_export_{TOPIC_SLUG}'
os.makedirs(export_dir, exist_ok=True)

export_template = """<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<style>
{style}
{green_override}
html,body{{ margin:0; padding:0; }}
*{{ font-family:'DejaVu Sans', sans-serif !important; }}
.headline, .cover-sub, .item h4 {{ font-family:'DejaVu Serif', serif !important; }}
.slide{{ display:block !important; transform:none !important; width:1080px !important; height:1350px !important; background:{bg} !important; }}
</style>
</head>
<body>
{slide_html}
</body>
</html>"""

for i, s in enumerate(SLIDES):
    bg_color = bgmap[BGS[i]]
    slide_div = make_slide_div(i, s, active=True)
    html = export_template.format(style=style_block, green_override=GREEN_THEME_OVERRIDE, bg=bg_color, slide_html=slide_div)
    with open(f'{export_dir}/slide-{i+1}.html', 'w', encoding='utf-8') as f:
        f.write(html)

print(f"Fertig: {len(SLIDES)} Slides erzeugt.")
print(f"Vorschau: carousel_{TOPIC_SLUG}.html")
print(f"Export-HTMLs: {export_dir}/slide-1.html ... slide-9.html")
print("Als PNG rendern mit:")
print(f"  cd {export_dir} && for i in 1 2 3 4 5 6 7 8 9; do wkhtmltoimage --width 1080 --height 1350 --disable-smart-width slide-$i.html slide-$i.png; done")
