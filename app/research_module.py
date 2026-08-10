"""
Kopfnuss Recherche-Modul
=========================
Laesst Claude schnell (aus eigenem Wissen, ohne Websuche oder externe
Datenbank-Abfrage) 3 passende Studien zu einem Thema vorschlagen - der
Nutzer waehlt danach eine davon als Quelle fuer den Post aus.

Output je Studie: Autor:innen, Jahr, Kernbefund in einfachen Worten,
Methodik, Limitationen/Kritikpunkte - die Bausteine, die das
Design-System fuer Zitate/Studien verlangt.
"""

import os
import re

import anthropic
from dotenv import load_dotenv

load_dotenv()

MODEL = "claude-sonnet-5"


def _client():
    return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


RESEARCH_TOOL = {
    "name": "studien_vorschlaege",
    "description": "Reicht 3 passende Studien-Vorschlaege zum Thema ein.",
    "strict": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "studien": {
                "type": "array",
                "description": "Genau 3 Studien-Vorschlaege.",
                "items": {
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
                    },
                    "required": ["titel", "autoren", "jahr", "kernbefund", "methodik", "limitationen"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["studien"],
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


def schlage_studien_vor(thema):
    """
    Laesst Claude 3 bekannte, passende Studien zum Thema nennen - direkt aus
    dem eigenen Wissen, ohne Websuche oder Datenbank-Abfrage (daher schnell,
    aber nicht live verifiziert - die Angaben sollten stichprobenartig
    geprueft werden, bevor sie im Post landen).
    """
    resp = _client().messages.create(
        model=MODEL,
        max_tokens=2048,
        tools=[RESEARCH_TOOL],
        tool_choice={"type": "tool", "name": "studien_vorschlaege"},
        messages=[{
            "role": "user",
            "content": (
                f"Nenne 3 bekannte, seriöse Studien zum Thema '{thema}', die du direkt aus "
                "deinem Wissen kennst (keine Websuche - nur Studien, die dir sofort einfallen). "
                "Fuer jede: Titel, Autor:innen, Jahr, Kernbefund in einfachen, "
                "laienverstaendlichen Worten (siehe Design-System: Kernbefund in eigenen Worten "
                "wiedergeben), Methodik, Limitationen/Kritikpunkte."
            ),
        }],
    )
    return _tool_input(resp)["studien"]
