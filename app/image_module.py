"""
Kopfnuss Bild-Modul
=====================
Generiert ein freigestelltes Icon-/Diagramm-Motiv fuer Slide 1 (Cover) per
Gemini-Bildgenerierung ("Nano Banana"), passend zur freigegebenen Cover-Frage
und dem duennen, blassen Linien-Illustrationsstil des Kopfnuss-Kanals.

Das Motiv wird auf einem Chroma-Key-Einfarbhintergrund generiert und danach
per Bildbearbeitung durchsichtig gemacht, damit es sich transparent ueber das
bestehende Slide-Design (Hintergrundfarbe + Blob-Deko) legen laesst.
"""

import io
import os

import numpy as np
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image

load_dotenv()

MODEL = "gemini-2.5-flash-image"

CHROMA_KEY = (255, 0, 255)  # reines Magenta, kommt in unserer Palette nicht vor

PROMPT_TEMPLATE = """Erstelle ein einzelnes, freigestelltes Icon-/Diagramm-Motiv (kein flaechendeckendes Hintergrundbild) fuer eine Instagram-Cover-Slide zum Thema Psychologie/Coaching. Das Motiv wird spaeter freigestellt auf einer bereits vorhandenen Seite platziert.

Zentrale Frage/Thema des Motivs: "{cover_frage}"

Stil (wichtig, genau einhalten):
- Sehr duenne, filigrane Linienzeichnung, wie eine wissenschaftliche/schematische Diagramm-Illustration - KEINE dicken, saettigten Flaechen
- Symbolisch/diagrammatisch statt narrativ: 2-4 kleine, klar erkennbare Einzelsymbole/Icons, die das Thema andeuten (z.B. ein Diagramm mit Achsen, ein Objekt-Icon, Zahnraeder, ein Kopf-Symbol, Verbindungslinien/gepunktete Linien zwischen Elementen) - KEINE erzaehlte Szene, KEINE Comic-Charaktere mit Gesicht/Mimik
- Sehr reduziert, viel Leerraum zwischen den einzelnen Symbolen
- Alles wirkt leicht, luftig, skizzenhaft, kein Fotorealismus, keine 3D-Effekte, keine harten Schatten
- KEINERLEI Buchstaben, Woerter oder Zahlen im Bild (ein einzelnes Satzzeichen wie "?" ist erlaubt, aber keine Woerter/Beschriftungen)

Farbpalette (NUR diese Farben verwenden, aber SEHR blass/gedaempft/halbtransparent wirkend - duenne Outlines, Flaechen nur wie mit 20-30% Deckkraft):
- Terrakotta: #C15A2E
- Salbeigruen: #8FBFA0
- Dunkelgruen: #2E4A3B
- Gold/Orange: #EDA23E

Hintergrund: WICHTIG - der komplette Hintergrund muss eine einzige, absolut gleichmaessige Flaeche in genau dieser Farbe sein: RGB(255, 0, 255) reines Magenta/Pink, ohne jede Textur, Farbverlauf oder Schatten (wird danach automatisch entfernt).

Komposition:
- Format 4:5 Hochformat (1080x1350px)
- Die Symbole duerfen grosszuegig ueber die Flaeche verteilt sein, auch dort wo spaeter Logo/Ueberschrift als Text darueber liegen werden - das ist gewollt (die Linien sind duenn und blass genug, dass der Text trotzdem gut lesbar bleibt). Nur die direkten Bildraender (ca. 60px) bleiben frei.
"""


def _client():
    return genai.Client(api_key=os.environ["GOOGLE_API_KEY"])


def _sample_corner_color(img, box_size=20):
    """
    Liest die tatsaechlich erzeugte Hintergrundfarbe aus der oberen linken
    Bildecke aus (statt eine feste Farbe zu erwarten) - Gemini haelt sich
    erfahrungsgemaess nicht immer exakt an die vorgegebene Chroma-Key-Farbe.
    """
    corner = np.array(img.crop((0, 0, box_size, box_size)))
    return tuple(corner.reshape(-1, 3).mean(axis=0))


def _remove_chroma_key(img, key_color=CHROMA_KEY, tolerance=60, feather=40):
    """
    Macht Pixel nahe der Chroma-Key-Farbe transparent (mit weichem
    Uebergang statt hartem Rand), damit vom generierten Bild nur das
    Motiv selbst uebrig bleibt.
    """
    img = img.convert("RGBA")
    data = np.array(img)
    diff = np.sqrt(((data[:, :, :3].astype(float) - np.array(key_color)) ** 2).sum(axis=2))
    alpha = np.clip((diff - tolerance) / feather, 0, 1) * 255
    data[:, :, 3] = np.minimum(data[:, :, 3], alpha.astype(np.uint8))

    # Aeusseren Rand (dort ist laut Prompt garantiert nur Hintergrund) hart
    # auf komplett durchsichtig setzen, damit keine Farbreste/Kompressions-
    # artefakte am Bildrand als sichtbarer "Rahmen" uebrig bleiben.
    border = 50
    data[:border, :, 3] = 0
    data[-border:, :, 3] = 0
    data[:, :border, 3] = 0
    data[:, -border:, 3] = 0

    return Image.fromarray(data, "RGBA")


def _fit_to_canvas(img, width, height):
    """
    Skaliert ein Bild so, dass es komplett hineinpasst (nichts wird
    abgeschnitten), und zentriert es auf einer transparenten Leinwand
    der Zielgroesse (1080x1350, passend zur vollen Slide-Flaeche).
    """
    img_ratio = img.width / img.height
    target_ratio = width / height
    if img_ratio > target_ratio:
        new_width = width
        new_height = round(width / img_ratio)
    else:
        new_height = height
        new_width = round(height * img_ratio)
    img = img.resize((new_width, new_height), Image.LANCZOS)
    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    left = (width - new_width) // 2
    top = (height - new_height) // 2
    canvas.paste(img, (left, top), img)
    return canvas


def generate_cover_bild(cover_frage):
    """
    Generiert ein freigestelltes, kompakt zugeschnittenes Cover-Motiv
    (transparentes PNG) fuer die gegebene Cover-Frage. Gibt die
    PNG-Bytes zurueck.
    """
    prompt = PROMPT_TEMPLATE.format(cover_frage=cover_frage)
    client = _client()
    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(aspect_ratio="3:4"),
        ),
    )

    for part in response.candidates[0].content.parts:
        if part.inline_data:
            img = Image.open(io.BytesIO(part.inline_data.data)).convert("RGB")
            key_color = _sample_corner_color(img)
            img = _remove_chroma_key(img, key_color=key_color)
            img = _fit_to_canvas(img, 1080, 1350)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            return buf.getvalue()

    raise RuntimeError("Gemini hat kein Bild zurueckgegeben.")
