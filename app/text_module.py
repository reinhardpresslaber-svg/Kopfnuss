"""
Kopfnuss Text-Modul
====================
Ruft Claude (Anthropic API) auf, um
  a) 3 Cover-Frage-Vorschlaege (Slide 1) und
  b) die Slide-Texte 2-8, den Fazit-Text (Slide 9) und die Caption
zu generieren - jeweils streng nach den Regeln aus
Projektvorgaben/kopfnuss-design-system.md, das komplett als System-Prompt
mitgegeben wird.
"""

import os
import re

import anthropic
from dotenv import load_dotenv

from render_module import build_cover_slide, build_cta_slide

load_dotenv()

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(MODULE_DIR)
DESIGN_SYSTEM_PATH = os.path.join(PROJECT_ROOT, "Projektvorgaben", "kopfnuss-design-system.md")

MODEL = "claude-sonnet-5"

HTML_BAUKASTEN = """
Verfuegbare HTML-Bausteine fuer den "body" jeder Slide (2-8). Nutze IMMER
diese CSS-Klassen, erfinde keine eigenen. Genau EIN <div class="content-mid">
als aeusserster Container pro Slide.

1) Einfacher Fliesstext:
<div class="content-mid">
  <div class="headline">Kurze Headline</div>
  <p class="body-text">Fliesstext...</p>
</div>

2) Beispiel-Slide mit Karte (typischerweise Slide 2, "Beispiel"):
<div class="content-mid">
  <div class="headline">Stell dir vor:</div>
  <div class="card">
    <p class="body-text" style="margin-top:0;">Konkrete Alltagssituation...</p>
  </div>
</div>

3) Drei-Punkte-Vergleich (Trio, z.B. fuer drei Typen/Unterscheidungen):
<div class="content-mid">
  <div class="headline">Headline</div>
  <div class="trio">
    <div class="item"><h4>Titel 1</h4><p>Text 1</p></div>
    <div class="item"><h4>Titel 2</h4><p>Text 2</p></div>
    <div class="item"><h4>Titel 3</h4><p>Text 3</p></div>
  </div>
</div>
Wichtig bei diesem Baustein: Text 1, Text 2 und Text 3 muessen etwa
gleich lang sein (max. ca. 12 Woerter, ein kurzer Satz) - die drei
Kaestchen werden nebeneinander gerendert, bei stark unterschiedlicher
Laenge entstehen haessliche leere Flaechen in den kuerzeren Kaestchen.

Sonderzeichen NUR in den Slide-"body"-Feldern (nicht in der Caption!) als
HTML-Entities schreiben (&uuml; &auml; &ouml; &szlig; &ndash; &mdash; &bdquo;
&ldquo; &rsquo;), das macht das PNG-Rendering zuverlaessiger - siehe
bestehende Posts als Vorbild.

Verwende in den Text-Feldern (Headline, Fliesstext, Titel/Text der
Bausteine) AUSSCHLIESSLICH reinen Text, KEINE zusaetzlichen Inline-Tags
wie <em>, <strong>, <b> oder <i> - diese werden von der App nicht
unterstuetzt und wuerden im fertigen Bild als sichtbarer Text
("<em>...</em>") statt als Formatierung erscheinen.
"""


def _load_design_system():
    with open(DESIGN_SYSTEM_PATH, encoding="utf-8") as f:
        return f.read()


def _client():
    return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def _system_prompt():
    return (
        "Du bist die Text-Redaktion fuer den Instagram-Kanal @KopfnussPsychologie "
        "(Betreiber: Diplom-Psychologe). Halte dich EXAKT an folgendes Design-System "
        "(Struktur, Sprache, Ton, redaktionelle Regeln):\n\n"
        + _load_design_system()
        + "\n\n"
        + HTML_BAUKASTEN
    )


COVER_TOOL = {
    "name": "cover_vorschlaege",
    "description": "Reicht genau 3 Formulierungsvorschlaege fuer die Cover-Frage (Slide 1) ein.",
    "strict": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "vorschlaege": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Genau 3 Formulierungsvorschlaege.",
            }
        },
        "required": ["vorschlaege"],
        "additionalProperties": False,
    },
}

SLIDES_TOOL = {
    "name": "slide_texte",
    "description": "Reicht die Slide-Texte 2-8, den Fazit-Text (Slide 9) und die Caption ein.",
    "strict": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "slides_2_bis_8": {
                "type": "array",
                "description": "Genau 7 Slide-Objekte (fuer Slides 2 bis 8).",
                "items": {
                    "type": "object",
                    "properties": {
                        "label": {
                            "type": "string",
                            "description": "Kurzes Eyebrow-Label, z.B. 'Beispiel' - leerer String wenn kein Label passt",
                        },
                        "body": {
                            "type": "string",
                            "description": "HTML-Body der Slide nach den vorgegebenen Bausteinen",
                        },
                    },
                    "required": ["label", "body"],
                    "additionalProperties": False,
                },
            },
            "fazit_body": {
                "type": "string",
                "description": 'Ein <p class="body-text">...</p> mit dem Fazit-Satz fuer Slide 9 (ohne CTA-Zeilen, die werden automatisch ergaenzt)',
            },
            "caption": {
                "type": "string",
                "description": (
                    "Die Instagram-Caption nach Design-System Abschnitt 3 (inkl. 5 Hashtags). "
                    "WICHTIG: normaler Klartext mit echten Umlauten (ü, ä, ö, ß) - "
                    "KEINE HTML-Entities, die Caption wird 1:1 bei Instagram eingefuegt."
                ),
            },
        },
        "required": ["slides_2_bis_8", "fazit_body", "caption"],
        "additionalProperties": False,
    },
}


_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def _clean(value):
    """Entfernt vereinzelt auftretende Steuerzeichen (z.B. \\r), die Claude
    manchmal statt eines Sonderzeichens wie eines Gedankenstrichs erzeugt."""
    if isinstance(value, str):
        return _CONTROL_CHARS.sub("", value)
    if isinstance(value, list):
        return [_clean(v) for v in value]
    if isinstance(value, dict):
        return {k: _clean(v) for k, v in value.items()}
    return value


def _tool_input(resp):
    tool_use = next(b for b in resp.content if b.type == "tool_use")
    return _clean(tool_use.input)


def generate_cover_optionen(thema, kontext=""):
    """Generiert 3 Cover-Frage-Vorschlaege (nur Text, kein Layout) fuer Slide 1."""
    user_msg = (
        f"Thema: {thema}\n\n"
        + (f"Rechercheergebnisse/Kontext:\n{kontext}\n\n" if kontext else "")
        + "Erzeuge 3 Formulierungsvorschlaege fuer die Cover-Frage auf Slide 1 "
        "(catchy, spricht mit 'du' an, siehe Design-System Abschnitt 1). "
        "Reiche sie ueber das Werkzeug 'cover_vorschlaege' ein."
    )
    resp = _client().messages.create(
        model=MODEL,
        max_tokens=1024,
        system=_system_prompt(),
        tools=[COVER_TOOL],
        tool_choice={"type": "tool", "name": "cover_vorschlaege"},
        messages=[{"role": "user", "content": user_msg}],
    )
    return _tool_input(resp)["vorschlaege"]


def generate_slides_und_caption(thema, cover_frage, kontext=""):
    """Generiert Slides 2-8 (HTML), den Fazit-Text fuer Slide 9 und die Caption."""
    user_msg = (
        f"Thema: {thema}\n"
        f"Freigegebene Cover-Frage (Slide 1): {cover_frage}\n\n"
        + (f"Rechercheergebnisse/Kontext:\n{kontext}\n\n" if kontext else "")
        + "Erzeuge jetzt genau 7 Slides fuer die Positionen 2 bis 8 (Beispiel -> "
        "Kerngedanke/Definition -> Mechanismus in mehreren Teilen -> Aha-Satz -> "
        "Alltagsrelevanz, siehe Design-System Abschnitt 1), den Fazit-Text fuer "
        "Slide 9 sowie die Caption. "
        "Reiche alles ueber das Werkzeug 'slide_texte' ein."
    )
    resp = _client().messages.create(
        model=MODEL,
        max_tokens=4096,
        system=_system_prompt(),
        tools=[SLIDES_TOOL],
        tool_choice={"type": "tool", "name": "slide_texte"},
        messages=[{"role": "user", "content": user_msg}],
    )
    return _tool_input(resp)


def assemble_slides(cover_frage, slides_2_bis_8, fazit_body, bild_b64=None):
    """Baut die vollstaendige 9er-Slide-Liste fuer render_carousel() zusammen."""
    slides = [build_cover_slide(cover_frage, bild_b64=bild_b64)]
    for i, s in enumerate(slides_2_bis_8, start=2):
        eyebrow = f"{i:02d} / 09"
        if s.get("label"):
            eyebrow += f" &mdash; {s['label']}"
        slides.append({"eyebrow": eyebrow, "body": s["body"], "footer": "@KopfnussPsychologie"})
    slides.append(build_cta_slide(fazit_body))
    return slides
