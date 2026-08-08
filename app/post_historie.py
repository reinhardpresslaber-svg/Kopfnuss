"""
Kopfnuss Post-Historie
=======================
Fuehrt eine strukturierte Liste aller bisherigen Posts (Thema, Cover-Frage,
Slug, Quelle, Farbthema), damit neue Themen dagegen geprueft werden koennen
(Dopplungen vermeiden) und nach jedem neuen Post automatisch ein Eintrag
angehaengt wird.
"""

import json
import os

HISTORIE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "post_historie.json")


def load_historie():
    with open(HISTORIE_PATH, encoding="utf-8") as f:
        return json.load(f)


def save_historie(eintraege):
    with open(HISTORIE_PATH, "w", encoding="utf-8") as f:
        json.dump(eintraege, f, ensure_ascii=False, indent=2)


def append_post(slug, thema, cover_frage, datum=None, quelle=None, farbthema="klassisch"):
    """Haengt nach dem Rendern eines neuen Posts einen Eintrag an die Historie an."""
    historie = load_historie()
    historie.append({
        "slug": slug,
        "thema": thema,
        "cover_frage": cover_frage,
        "datum": datum,
        "quelle": quelle,
        "farbthema": farbthema,
    })
    save_historie(historie)
    return historie


def check_topic(neues_thema):
    """
    Einfacher Basis-Check: sucht Stichworte des neuen Themas in Thema/Cover-Frage
    bisheriger Posts (z.B. erkennt "Impostor" in "Impostor-Syndrom"). Erkennt noch
    KEINE inhaltliche Aehnlichkeit ueber Synonyme hinweg (z.B. "Hochstapler-Syndrom"
    vs. "Impostor-Syndrom") - das kommt mit dem Text-Modul (Claude-API) dazu, sobald
    der Anthropic-API-Key eingerichtet ist.
    """
    stichworte = [w.lower().strip(".,?!–—") for w in neues_thema.split() if len(w) > 3]
    treffer = []
    for eintrag in load_historie():
        text = f"{eintrag['thema']} {eintrag['cover_frage']}".lower()
        if any(stichwort in text for stichwort in stichworte):
            treffer.append(eintrag)
    return treffer
