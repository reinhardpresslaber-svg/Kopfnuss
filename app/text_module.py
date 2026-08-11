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

from render_module import (
    build_cover_slide,
    build_cta_slide,
    parse_slide_body,
    build_slide_body,
    parse_fazit_body,
    build_fazit_body,
)

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
    "description": (
        "Reicht genau 3 Formulierungsvorschlaege fuer die Cover-Frage (Slide 1) "
        "ein, jeweils aufgeteilt in teil1 und teil2."
    ),
    "strict": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "vorschlaege": {
                "type": "array",
                "description": "Genau 3 Formulierungsvorschlaege, jeweils als teil1/teil2.",
                "items": {
                    "type": "object",
                    "properties": {
                        "teil1": {
                            "type": "string",
                            "description": "Erster Teil der Cover-Frage (Aufbau/Kontext).",
                        },
                        "teil2": {
                            "type": "string",
                            "description": (
                                "Zweiter, kurzer Teil (die Pointe/der Clou) - wird auf der "
                                "Slide farblich hervorgehoben, daher kurz halten (max. ca. "
                                "5-6 Woerter). Muss sich natuerlich an teil1 anschliessen, "
                                "wenn man beide mit einem Leerzeichen aneinanderhaengt "
                                "(eigenes Satzzeichen/Gedankenstrich am Anfang mitliefern, "
                                "falls fuer den Anschluss noetig)."
                            ),
                        },
                    },
                    "required": ["teil1", "teil2"],
                    "additionalProperties": False,
                },
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
        + "Erzeuge 3 Formulierungsvorschlaege fuer die Cover-Frage auf Slide 1 - "
        "soll ein echter Scroll-Stopper sein (spricht mit 'du' an, siehe "
        "Design-System Abschnitt 1). Nutze fuer die 3 Vorschlaege bewusst "
        "unterschiedliche Hook-Techniken: (a) Curiosity-Gap-Frage, die eine "
        "konkrete Wissensluecke oeffnet statt nur generisch 'Warum...?' zu "
        "fragen, (b) ueberraschende oder kontraere Behauptung, die einem "
        "verbreiteten Irrglauben widerspricht, (c) eine konkrete Zahl/"
        "Zeitangabe statt einer vagen Formulierung (z.B. '3 Sekunden' statt "
        "'ganz kurz'). Bleib dabei seriös und fachlich fundiert (Diplom-"
        "Psychologe als Absender) - kein reisserisches Clickbait, sondern "
        "neugierig machende Praezision.\n\n"
        "Jeder Vorschlag besteht aus teil1 (Aufbau/Kontext) und teil2 (die "
        "kurze Pointe/der Clou zum Schluss, z.B. die Zahl, die Frage oder "
        "die Ueberraschung) - teil2 wird auf der Slide farblich hervorgehoben, "
        "daher kurz halten. Reiche sie ueber das Werkzeug 'cover_vorschlaege' "
        "ein."
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


REEL_TEXT_TOOL = {
    "name": "reel_zeilen",
    "description": "Reicht genau 6 kurze Textzeilen fuer ein Reel ein.",
    "strict": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "zeilen": {
                "type": "array",
                "description": (
                    "Genau 6 kurze Textzeilen, die im Reel nacheinander "
                    "eingeblendet werden (jede bleibt stehen, der Text baut "
                    "sich also zeilenweise auf)."
                ),
                "items": {"type": "string"},
            }
        },
        "required": ["zeilen"],
        "additionalProperties": False,
    },
}

REEL_TEXT_ANWEISUNG = """
Erstelle genau 6 sehr kurze, catchy Textzeilen fuer ein Reel im
Kinetic-Typography-Stil: die Zeilen werden nacheinander ueber dem
9:16-Reel-Hintergrundbild eingeblendet, jede neue Zeile bleibt stehen,
sodass sich der Text zeilenweise aufbaut, bis der Bildschirm gefuellt
ist. Jede Zeile: max. 5-6 Woerter, in lesbarer Groesse gedacht (nicht
zu lang, sonst passt der Text nicht auf den Bildschirm).

Aufbau wie ein Mini-Spannungsbogen:
1. Hook (passend zur Cover-Frage)
2-4. Zentraler Kernbefund/Mechanismus der Studie, auf 2-3 knappe
     Zeilen heruntergebrochen
5. Kurzer Payoff/Aha-Moment
6. CTA, z.B. "Folge @KopfnussPsychologie fuer mehr"

Ton wie im Design-System: seriös, klar, mit 'du' angesprochen - kein
Clickbait. Reiche die 6 Zeilen ueber das Werkzeug 'reel_zeilen' ein.
"""


def _editorial_system_prompt():
    return (
        "Du bist die Text-Redaktion fuer den Instagram-Kanal @KopfnussPsychologie "
        "(Betreiber: Diplom-Psychologe). Halte dich an Ton, Sprache und Themenwahl "
        "aus folgendem Design-System:\n\n" + _load_design_system()
    )


def generate_reel_text_lines(thema, cover_frage, caption, kontext=""):
    """Generiert 6 kurze Textzeilen (Kinetic-Typography-Stil), die im Reel
    nacheinander ueber dem 9:16-Hintergrundbild eingeblendet werden - fasst
    den fertigen Post (Cover-Frage + Caption als inhaltliche Grundlage)
    catchy zusammen."""
    user_msg = (
        f"Thema: {thema}\n"
        f"Cover-Frage (Slide 1): {cover_frage}\n"
        f"Caption des fertigen Posts:\n{caption}\n\n"
        + (f"Rechercheergebnisse/Kontext:\n{kontext}\n\n" if kontext else "")
        + REEL_TEXT_ANWEISUNG
    )
    resp = _client().messages.create(
        model=MODEL,
        max_tokens=800,
        system=_editorial_system_prompt(),
        tools=[REEL_TEXT_TOOL],
        tool_choice={"type": "tool", "name": "reel_zeilen"},
        messages=[{"role": "user", "content": user_msg}],
    )
    return _tool_input(resp)["zeilen"]


PROOFREAD_TOOL = {
    "name": "korrekturen",
    "description": (
        "Reicht fuer jedes eingereichte Textfeld die korrigierte Fassung ein "
        "- IMMER fuer jede ID einen Eintrag zurueckgeben, auch wenn der Text "
        "unveraendert bleibt."
    ),
    "strict": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "korrekturen": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "description": "Identische ID wie im Eingabetext"},
                        "text": {
                            "type": "string",
                            "description": (
                                "Korrigierter Text - nur kaputte/fehlende Umlaute, "
                                "Grammatikfehler und fehlende Woerter beheben, "
                                "inhaltlich und im Ton unveraendert lassen."
                            ),
                        },
                    },
                    "required": ["id", "text"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["korrekturen"],
        "additionalProperties": False,
    },
}


def _sammle_proofreading_items(slides_ergebnis, caption):
    """
    Zerlegt alle bearbeitbaren Text-Bausteine (Slide-Headlines/Bodies bzw.
    Trio-Items, Fazit, Caption) in eine flache Liste von (id, text) fuer eine
    gemeinsame Proofreading-Runde. Nutzt dieselbe parse_slide_body()-Logik
    wie die manuelle Text-Bearbeitung, damit HTML sicher rund-trippt.
    Slides mit unbekannter Struktur (type "raw") werden ausgelassen, da sich
    ihr HTML nicht sicher rekonstruieren laesst.
    """
    items = []
    parsed_slides = []
    for i, s in enumerate(slides_ergebnis["slides_2_bis_8"], start=2):
        parsed = parse_slide_body(s["body"])
        parsed_slides.append(parsed)
        if parsed["type"] == "trio":
            items.append((f"s{i}_headline", parsed["headline"]))
            for j, item in enumerate(parsed["items"]):
                items.append((f"s{i}_item{j}_titel", item["titel"]))
                items.append((f"s{i}_item{j}_text", item["text"]))
        elif parsed["type"] in ("card", "simple"):
            items.append((f"s{i}_headline", parsed["headline"]))
            items.append((f"s{i}_body", parsed["body"]))
    fazit_text = parse_fazit_body(slides_ergebnis["fazit_body"])
    items.append(("fazit", fazit_text))
    items.append(("caption", caption))
    return items, parsed_slides


def _proofread_items(items):
    """
    Schickt eine flache Liste von (id, text)-Paaren zum Proofreading an
    Claude (kaputte Umlaute/scharfes-S, Grammatik, fehlende Woerter) und
    gibt ein Dict id -> korrigierter Text zurueck (fuer JEDE eingereichte ID,
    auch unveraendert gebliebene).
    """
    eingabe = "\n\n".join(f'ID: {id_}\nText: "{text}"' for id_, text in items)
    user_msg = (
        "Pruefe folgende Textfelder eines Instagram-Posts auf drei "
        "Fehlerarten: (1) als ae/oe/ue/ss ausgeschriebene statt echter "
        "Umlaute/scharfes-S - ersetze IMMER durch das richtige Zeichen, "
        "z.B. 'Woerter' -> 'Wörter', 'Koerper' -> 'Körper', "
        "'Verhaeltnis' -> 'Verhältnis', 'duenner' -> 'dünner', "
        "'gepraegt' -> 'geprägt', 'Abkuerzungen' -> 'Abkürzungen', "
        "'ausser' -> 'außer' - auch wenn der Rest des Wortes korrekt "
        "erscheint; (2) Grammatikfehler; (3) fehlende Woerter oder "
        "abgebrochene Saetze. Aendere NICHTS am Inhalt, Ton oder an der "
        "Wortwahl - nur diese drei Fehlerarten beheben. Felder ohne Fehler "
        "unveraendert zurueckgeben. Reiche fuer JEDE ID einen Eintrag "
        "ein.\n\n" + eingabe
    )
    resp = _client().messages.create(
        model=MODEL,
        max_tokens=4096,
        system=_editorial_system_prompt(),
        tools=[PROOFREAD_TOOL],
        tool_choice={"type": "tool", "name": "korrekturen"},
        messages=[{"role": "user", "content": user_msg}],
    )
    return {k["id"]: k["text"] for k in _tool_input(resp)["korrekturen"]}


def proofread_cover_optionen(cover_optionen):
    """Prueft die 3 Cover-Frage-Vorschlaege (Slide 1, je teil1/teil2) auf
    kaputte Umlaute, Grammatikfehler und fehlende Woerter - Inhalt/Ton
    bleiben unveraendert."""
    items = []
    for i, o in enumerate(cover_optionen):
        items.append((f"cover{i}_teil1", o["teil1"]))
        items.append((f"cover{i}_teil2", o["teil2"]))
    korrekturen = _proofread_items(items)
    return [
        {
            "teil1": korrekturen.get(f"cover{i}_teil1", o["teil1"]),
            "teil2": korrekturen.get(f"cover{i}_teil2", o["teil2"]),
        }
        for i, o in enumerate(cover_optionen)
    ]


def proofread_slides_und_caption(slides_ergebnis, caption):
    """
    Laesst Claude alle Texte (Slide-Headlines/Bodies, Fazit, Caption) auf
    kaputte Umlaute, Grammatikfehler und fehlende Woerter pruefen und
    korrigieren - Inhalt/Ton bleiben unveraendert, nur Fehler werden
    behoben. Gibt ein korrigiertes slides_ergebnis-Dict (gleiche Form wie
    generate_slides_und_caption()) zurueck.
    """
    items, parsed_slides = _sammle_proofreading_items(slides_ergebnis, caption)
    korrekturen = _proofread_items(items)

    korrigierte_slides = []
    for i, (s, parsed) in enumerate(zip(slides_ergebnis["slides_2_bis_8"], parsed_slides), start=2):
        if parsed["type"] == "trio":
            parsed["headline"] = korrekturen.get(f"s{i}_headline", parsed["headline"])
            for j, item in enumerate(parsed["items"]):
                item["titel"] = korrekturen.get(f"s{i}_item{j}_titel", item["titel"])
                item["text"] = korrekturen.get(f"s{i}_item{j}_text", item["text"])
            neuer_body = build_slide_body(parsed)
        elif parsed["type"] in ("card", "simple"):
            parsed["headline"] = korrekturen.get(f"s{i}_headline", parsed["headline"])
            parsed["body"] = korrekturen.get(f"s{i}_body", parsed["body"])
            neuer_body = build_slide_body(parsed)
        else:
            neuer_body = s["body"]
        korrigierte_slides.append({"label": s["label"], "body": neuer_body})

    korrigiertes_fazit = build_fazit_body(
        korrekturen.get("fazit", parse_fazit_body(slides_ergebnis["fazit_body"]))
    )
    korrigierte_caption = korrekturen.get("caption", caption)

    return {
        "slides_2_bis_8": korrigierte_slides,
        "fazit_body": korrigiertes_fazit,
        "caption": korrigierte_caption,
    }


def assemble_slides(cover_frage, slides_2_bis_8, fazit_body, bild_b64=None):
    """Baut die vollstaendige 9er-Slide-Liste fuer render_carousel() zusammen."""
    slides = [build_cover_slide(cover_frage, bild_b64=bild_b64)]
    for i, s in enumerate(slides_2_bis_8, start=2):
        eyebrow = f"{i}/9"
        if s.get("label"):
            eyebrow += f" &mdash; {s['label']}"
        slides.append({"eyebrow": eyebrow, "body": s["body"], "footer": "@KopfnussPsychologie"})
    slides.append(build_cta_slide(fazit_body))
    return slides
