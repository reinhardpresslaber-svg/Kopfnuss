"""
Kopfnuss Recherche-Modul
=========================
Sucht zu einem Thema eine passende Quelle/Studie:
1. Zuerst in der wissenschaftlichen Datenbank Semantic Scholar.
2. Nur wenn dort nichts Passendes zu finden ist: Fallback auf eine normale
   Websuche (ueber Claudes eingebautes Web-Search-Werkzeug), klar markiert
   als "nicht aus wissenschaftlicher Datenbank" (Design-System Abschnitt 2).

Output: Autor:innen, Jahr, Kernbefund in einfachen Worten, Methodik,
Limitationen/Kritikpunkte - die Bausteine, die das Design-System fuer
Zitate/Studien verlangt.
"""

import os
import re

import anthropic
import requests
from dotenv import load_dotenv

load_dotenv()

MODEL = "claude-sonnet-5"
SEMANTIC_SCHOLAR_URL = "https://api.semanticscholar.org/graph/v1/paper/search"


def _client():
    return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


RESEARCH_TOOL = {
    "name": "recherche_ergebnis",
    "description": "Reicht die strukturierte Zusammenfassung einer Studie/Quelle ein.",
    "strict": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "titel": {"type": "string"},
            "autoren": {"type": "string"},
            "jahr": {"type": "string"},
            "kernbefund": {
                "type": "string",
                "description": "Der zentrale Befund in einfachen, laienverstaendlichen Worten",
            },
            "methodik": {"type": "string"},
            "limitationen": {
                "type": "string",
                "description": "Limitationen/Kritikpunkte, insbesondere bei unsicherer Evidenzlage",
            },
            "quelle_typ": {
                "type": "string",
                "enum": ["wissenschaftliche_datenbank", "websuche"],
            },
        },
        "required": ["titel", "autoren", "jahr", "kernbefund", "methodik", "limitationen", "quelle_typ"],
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


def search_semantic_scholar(thema, limit=5):
    """
    Sucht Kandidaten in der wissenschaftlichen Datenbank Semantic Scholar.
    Gibt bei Fehlern (z.B. Rate-Limit ohne API-Key) eine leere Liste zurueck,
    statt abzubrechen - research_thema() weicht dann auf die Websuche aus.
    """
    try:
        resp = requests.get(
            SEMANTIC_SCHOLAR_URL,
            params={"query": thema, "limit": limit, "fields": "title,abstract,year,authors,externalIds"},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json().get("data", [])
    except requests.exceptions.RequestException:
        return []


def _research_via_semantic_scholar(thema, papers):
    kandidaten = "\n\n".join(
        f"Titel: {p.get('title')}\n"
        f"Jahr: {p.get('year')}\n"
        f"Autor:innen: {', '.join(a['name'] for a in p.get('authors', []))}\n"
        f"Abstract: {p.get('abstract') or 'kein Abstract verfuegbar'}"
        for p in papers[:3]
    )
    resp = _client().messages.create(
        model=MODEL,
        max_tokens=2048,
        tools=[RESEARCH_TOOL],
        tool_choice={"type": "tool", "name": "recherche_ergebnis"},
        messages=[{
            "role": "user",
            "content": (
                f"Thema: {thema}\n\nKandidaten aus Semantic Scholar (wissenschaftliche Datenbank):\n"
                f"{kandidaten}\n\nWaehle die am besten passende Studie aus und fasse sie strukturiert "
                "zusammen. Kernbefund in einfachen, laienverstaendlichen Worten (siehe Design-System: "
                "Autor:innen und Jahr nennen, Kernbefund in eigenen Worten wiedergeben). quelle_typ ist "
                "'wissenschaftliche_datenbank'."
            ),
        }],
    )
    return _tool_input(resp)


def _research_via_websearch(thema):
    such_resp = _client().messages.create(
        model=MODEL,
        max_tokens=8000,
        tools=[{"type": "web_search_20260209", "name": "web_search", "max_uses": 3}],
        messages=[{
            "role": "user",
            "content": (
                f"Suche nach einer moeglichst seriösen Quelle/Studie zum Thema '{thema}' und fasse "
                "zusammen: Autor:innen, Jahr, Kernbefund in einfachen Worten, Methodik, "
                "Limitationen/Kritikpunkte. Suche hoechstens 2-3 Mal - nutze die ersten brauchbaren "
                "Treffer, anstatt endlos weiterzusuchen. Schreibe danach IMMER eine Zusammenfassung in "
                "Textform, auch wenn nicht jedes Detail bestaetigt werden konnte. Wenn du gar nichts "
                "Passendes findest, sag das explizit in der Zusammenfassung."
            ),
        }],
    )
    summary_text = "".join(b.text for b in such_resp.content if b.type == "text")
    if not summary_text.strip():
        summary_text = "(Keine Zusammenfassung erhalten - Recherche wurde vermutlich abgebrochen.)"

    struct_resp = _client().messages.create(
        model=MODEL,
        max_tokens=2048,
        tools=[RESEARCH_TOOL],
        tool_choice={"type": "tool", "name": "recherche_ergebnis"},
        messages=[{
            "role": "user",
            "content": (
                f"Bringe folgende Rechercheergebnisse in die strukturierte Form:\n\n{summary_text}\n\n"
                "quelle_typ ist 'websuche', da keine wissenschaftliche Datenbank verfuegbar war."
            ),
        }],
    )
    return _tool_input(struct_resp)


def research_thema(thema):
    """
    Recherchiert ein Thema: zuerst Semantic Scholar (wissenschaftliche Datenbank),
    bei keinem Treffer Fallback auf Websuche (im Ergebnis als quelle_typ markiert).
    """
    papers = search_semantic_scholar(thema)
    if papers:
        return _research_via_semantic_scholar(thema, papers)
    return _research_via_websearch(thema)
