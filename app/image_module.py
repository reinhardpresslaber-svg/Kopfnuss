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
- Flaches Icon-Design: eine Mischung aus duennen Linien UND ausgefuellten/flaechigen Formen (nicht nur Umrisse) - wie ein modernes Icon-Set, nicht wie eine Bleistiftskizze
- Symbolisch/diagrammatisch statt narrativ: 2-4 kleine, klar erkennbare Einzelsymbole/Icons, die das Thema andeuten (z.B. ein Diagramm mit Achsen, ein Objekt-Icon, Zahnraeder, ein Kopf-Symbol, Verbindungslinien/gepunktete Linien zwischen Elementen) - KEINE erzaehlte Szene, KEINE Comic-Charaktere mit Gesicht/Mimik
- Reduziert, viel Leerraum zwischen den einzelnen Symbolen
- Kein Fotorealismus, keine 3D-Effekte, keine harten Schatten
- UNBEDINGT BEACHTEN: Das Bild darf UNTER KEINEN UMSTAENDEN Text enthalten - keine Buchstaben, Woerter, Beschriftungen, Labels oder Zahlen, auch nicht auf Schildern, Kaestchen oder Objekten im Bild. Zeichne ausschliesslich reine Formen/Symbole/Icons OHNE jede Schrift. Ein einzelnes Satzzeichen wie "?" ist die einzige Ausnahme.

Farbpalette (NUR diese Farben verwenden, dabei kraeftig/satt und praesent einsetzen - keine ausgeblassten/verwaschenen Toene, ruhig auch groessere ausgefuellte Flaechen in diesen Farben):
- Terrakotta: #C15A2E
- Salbeigruen: #8FBFA0
- Dunkelgruen: #2E4A3B
- Gold/Orange: #EDA23E

Hintergrund: WICHTIG - der komplette Hintergrund muss eine einzige, absolut gleichmaessige Flaeche in genau dieser Farbe sein: RGB(255, 0, 255) reines Magenta/Pink, ohne jede Textur, Farbverlauf oder Schatten (wird danach automatisch entfernt).

Komposition:
- Format 3:4 Hochformat (1080x1440px)
- WICHTIG: Der Schwerpunkt/die Hauptmasse der Symbole liegt klar in der RECHTEN Bildhaelfte. Im linken oberen Bereich (dort sitzt spaeter ein Logo, ca. bei 15-35% der Bildbreite/-hoehe) duerfen bestenfalls einzelne duenne Linien durchlaufen, aber keine dichten/dominanten Formen - dieser Bereich soll sichtbar leerer wirken als die rechte Seite.
- Weiter unten (dort wo die Ueberschrift als Text liegt) duerfen die Symbole ueber die ganze Breite verteilt sein, da die Linien duenn und blass genug sind, dass der Text trotzdem gut lesbar bleibt.
- Nur die direkten Bildraender (ca. 60px) bleiben komplett frei.
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


def _clear_left_zone(img, fraction=0.18):
    """
    Loescht (macht transparent) den linken Bildbereich hart, egal was
    dort generiert wurde - verlaesslicher als sich nur auf die
    Prompt-Anweisung "Schwerpunkt rechts" zu verlassen, da Gemini
    gelegentlich trotzdem einzelne Icons/Linien links platziert. Seit die
    Deckkraft des Motivs auf der Slide gesenkt wurde (siehe
    render_module.build_cover_slide), stoert Bildinhalt links nicht mehr
    so stark - daher weniger stark beschnitten als frueher (0.37 -> 0.18).
    """
    data = np.array(img)
    cut = round(img.width * fraction)
    data[:, :cut, 3] = 0
    return Image.fromarray(data, "RGBA")


def _trim_transparent(img, padding=30):
    """
    Schneidet ueberschuessigen transparenten Rand um das eigentliche
    Motiv herum ab, damit es beim Einpassen in die Zielgroesse (via
    _fit_to_canvas) moeglichst gross erscheint statt von unsichtbarem
    Leerraum umgeben zu sein.
    """
    bbox = img.getchannel("A").getbbox()
    if bbox is None:
        return img
    left, top, right, bottom = bbox
    left = max(0, left - padding)
    top = max(0, top - padding)
    right = min(img.width, right + padding)
    bottom = min(img.height, bottom + padding)
    return img.crop((left, top, right, bottom))


def _fit_to_canvas(img, width, height, x_bias=0.5):
    """
    Skaliert ein Bild so, dass es komplett hineinpasst (nichts wird
    abgeschnitten), und platziert es auf einer transparenten Leinwand
    der Zielgroesse (1080x1440, passend zur vollen Slide-Flaeche).
    x_bias verschiebt die horizontale Position leicht nach rechts
    (0.5 = mittig, 1.0 = ganz rechts), damit der Bildschwerpunkt zur
    rechtslastigen Komposition passt statt streng zentriert zu wirken.
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
    left = round((width - new_width) * x_bias)
    top = (height - new_height) // 2
    canvas.paste(img, (left, top), img)
    return canvas


def _clean_resize_haze(img):
    """
    Entfernt einen leichten Schleier, der beim Hochskalieren (LANCZOS)
    an transparenten Kanten entstehen kann - alles unterhalb eines
    Alpha-Schwellwerts wird komplett durchsichtig statt leicht sichtbar.
    """
    data = np.array(img)
    data[:, :, 3] = np.where(data[:, :, 3] < 25, 0, data[:, :, 3])
    return Image.fromarray(data, "RGBA")


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
            img = _trim_transparent(img)
            img = _fit_to_canvas(img, 1080, 1440)
            img = _clear_left_zone(img)
            img = _clean_resize_haze(img)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            return buf.getvalue()

    raise RuntimeError("Gemini hat kein Bild zurueckgegeben.")


PROMPT_TEMPLATE_FOTO = """Erstelle ein modernes, kunstvolles Foto im Stil eines zeitgenoessischen Editorial-/Fine-Art-Portraitshootings (z.B. wie ein aktuelles Magazin-Cover oder eine Galerie-Fotografie - KEIN generisches, beliebiges Corporate-/Lifestyle-Stockfoto) fuer die Titelseite eines Instagram-Posts zum Thema Psychologie/Coaching. Das Foto wird als fest umrissener Bildblock am oberen Rand der Seite verwendet (kein Freistellen noetig, kein Verlauf - darunter folgt eine harte Kante zu einer einfarbigen Flaeche mit Text).

WICHTIGSTE REGEL, UNBEDINGT EINHALTEN: Das Bild selbst ist ein reines, digitales Foto OHNE jeden Rahmen - KEIN weisser oder cremefarbener Rand, KEIN Passepartout, KEINE Bordüre, KEINE Vignette, KEIN sichtbarer Fotoabzug/Print-Look mit Papierrand um die Szene herum. Auch die "Editorial-/Fine-Art"-Anmutung bezieht sich NUR auf Licht und Bildsprache, NICHT auf einen physischen Print oder Rahmen als Bildelement. Die Aufnahme fuellt die gesamte Bildflaeche bis zum allerletzten Pixel an allen vier Kanten aus.

Zentrale Frage/Thema des Posts: "{cover_frage}"

Motiv:
- WICHTIGSTES ZIEL - Storytelling: Das Bild soll die Frage/das Thema oben ("{cover_frage}") konkret ERZAEHLEN, nicht nur allgemein illustrieren. Ueberlege dir eine nachvollziehbare, spezifische Alltagsszene, die genau diese Situation zeigt (passende Handlung, Requisiten, Umgebung, Interaktion zwischen den Personen - was tun sie gerade, warum, was ist der Ausloeser?). Wer das Bild sieht, soll auch ohne den Text zu lesen erahnen koennen, worum es im Post geht - keine austauschbare, allgemeine "nachdenkliche Person"-Pose ohne erkennbaren inhaltlichen Bezug zum Thema
- Entscheide bewusst zwischen EINER Person, einem DUO oder einer GRUPPE (3+ Personen), je nachdem was inhaltlich am besten passt - NICHT automatisch immer auf 1-2 Personen ausweichen. Geht es im Thema eher um ein inneres Erleben oder eine individuelle Gewohnheit EINER Person (z.B. Prokrastination, Selbstzweifel, eigene Denkmuster, eine persoenliche Entscheidung), zeige NUR EINE Person - das wirkt oft eindringlicher als ein Duo. Geht es um zwischenmenschliche Dynamik zwischen zwei Menschen (z.B. Streit, Missverstaendnis, ein Gespraech), passen 2 Personen. Geht es dagegen um Gruppendynamik, soziale Kategorisierung, Zugehoerigkeit/Ausgrenzung, "wir vs. die anderen", Gruppenverhalten oder aehnliches (z.B. Ingroup/Outgroup, Konformitaet, Gruppendruck, Vorurteile zwischen Gruppen), zeige eine echte GRUPPE von mindestens 3-6 Personen - bei Themen, die zwei Gruppen gegenueberstellen (z.B. "Gruppe A und Gruppe B"), koennen auch zwei sichtbar getrennte Grueppchen im selben Bild dargestellt werden. Die Person(en) sollen sympathisch, authentisch wirken (natuerliche Ausstrahlung, KEIN aufgesetztes Stock-Foto-Laecheln), Situation/Gesichtsausdruck faengt das Thema emotional ein
- Blickkontakt fuer mehr Scroll-Stopper-Wirkung: Mindestens eine der abgebildeten Personen schaut direkt in die Kamera/zum Betrachter (nicht alle Personen blicken aneinander vorbei oder aus dem Bild heraus)
- Falls du dich fuer 2 oder mehr Personen entscheidest: Variiere bewusst die Konstellation von Bild zu Bild - NICHT immer ein gemischtgeschlechtliches Mann-Frau-Duo, sondern abwechselnd auch mal zwei Frauen, zwei Maenner, unterschiedliche Altersgruppen/Erscheinungsbilder. Insgesamt divers und nicht immer denselben Personentyp zeigen
- Bewusste, kuenstlerische Bildkomposition statt beliebigem Alltagsschnappschuss - praezise Posen/Blickrichtung, klare Bildidee
- Halbnahe bis mittlere Einstellung (Kopf bis Oberkoerper/Hueften sichtbar) bei 1-2 Personen - KEIN extremer Close-up. Bei einer Gruppe darf die Einstellung entsprechend weiter/kleiner werden, damit alle Personen bequem ins Bild passen. Die Personen muessen VOLLSTAENDIG und mit spuerbarem Rand/Luft zu allen Bildkanten im Bild stehen - Koepfe/Gesichter/Koerper duerfen NICHT am Bildrand angeschnitten sein oder zu nah rangezoomt wirken. Grosszuegiger Rahmen, damit beim spaeteren Zuschneiden nichts Wichtiges verloren geht

Stil:
- Modernes, kunstvolles Editorial-/Fine-Art-Licht: kraeftiges, gerichtetes Licht mit klaren Kontrasten/Schatten (z.B. hartes Seitenlicht oder starkes Fensterlicht) statt diffusem, flachem "Lifestyle"-Licht
- Reduzierte, bewusst gewaehlte Farbpalette - gerne mit Anklaengen an Terrakotta (#C15A2E), Salbeigruen (#8FBFA0) oder Creme (#FBF6EF) in Kleidung/Umgebung, ruhig und hochwertig statt bunt/beliebig
- Fotorealistisch, KEINE Illustration, KEIN 3D-Render, KEIN Comic-/Cartoon-Stil
- UNBEDINGT BEACHTEN: Das Bild darf UNTER KEINEN UMSTAENDEN Text, Buchstaben, Woerter oder Logos enthalten
- UNBEDINGT BEACHTEN: Das Foto muss randlos/vollflaechig bis zum Bildrand gehen - KEIN weisser/cremefarbener Rahmen, KEIN Passepartout, KEIN Rand, KEINE Bordüre um das Foto herum, auch nicht als "Fine-Art-Print"-Stilmittel. Die Szene fuellt das gesamte Bild bis zu allen vier Kanten aus.

Format: Querformat-aehnlicher Bildausschnitt (wird oben auf der Seite als breiter Streifen genutzt, randlos/vollflaechig). Das Hauptmotiv mittig positionieren, mit ausreichend Luft zu allen vier Bildraendern innerhalb der Szene selbst (nichts wird angeschnitten) - aber OHNE einen umlaufenden Rahmen/Rand als eigenes Bildelement.
"""


def generate_cover_foto(cover_frage):
    """
    Generiert ein realistisches Foto-Motiv mit Menschen fuer Slide 1 -
    Alternative zur Icon-Illustration (generate_cover_bild()), fuer ein
    emotionaleres, ansprechenderes Cover. Wird als querformatiger Streifen
    (1080x620px, siehe render_module.build_cover_slide_foto()) am oberen
    Slide-Rand verwendet, daher hier im Breitformat "16:9" generiert statt
    im Hochformat wie beim Icon-Motiv - object-fit:cover schneidet sonst
    zu viel vom Hochformat-Bild weg. Kein Freistellen/Chroma-Key noetig,
    da das Foto opak verwendet wird. Gibt PNG-Bytes zurueck.
    """
    prompt = PROMPT_TEMPLATE_FOTO.format(cover_frage=cover_frage)
    client = _client()
    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(aspect_ratio="16:9"),
        ),
    )

    for part in response.candidates[0].content.parts:
        if part.inline_data:
            img = Image.open(io.BytesIO(part.inline_data.data)).convert("RGB")
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            return buf.getvalue()

    raise RuntimeError("Gemini hat kein Bild zurueckgegeben.")
