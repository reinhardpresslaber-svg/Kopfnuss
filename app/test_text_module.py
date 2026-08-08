"""
End-to-End-Testlauf: Post-Historie-Check -> Text-Modul -> Render-Modul,
mit einem Testthema, das noch nicht behandelt wurde.
"""

from post_historie import check_topic
from text_module import generate_cover_optionen, generate_slides_und_caption, assemble_slides
from render_module import render_carousel

THEMA = "Confirmation Bias (Bestaetigungsfehler)"

print(f"--- Historien-Check fuer '{THEMA}' ---")
treffer = check_topic(THEMA)
print("Treffer:" if treffer else "Keine Dopplung gefunden, weiter geht's.")
for t in treffer:
    print(" ->", t["thema"])
print()

print("--- Schritt a: Cover-Vorschlaege generieren ---")
vorschlaege = generate_cover_optionen(THEMA)
for i, v in enumerate(vorschlaege, 1):
    print(f"{i}. {v}")
print()

cover_frage = vorschlaege[0]
print(f"(Testlauf waehlt automatisch Vorschlag 1: \"{cover_frage}\")")
print()

print("--- Schritt b: Slides 2-8, Fazit, Caption generieren ---")
ergebnis = generate_slides_und_caption(THEMA, cover_frage)
print(f"Anzahl Slides 2-8: {len(ergebnis['slides_2_bis_8'])}")
print(f"Fazit-Body: {ergebnis['fazit_body'][:80]}...")
print(f"Caption (erste 150 Zeichen): {ergebnis['caption'][:150]}...")
print()

print("--- Rendern ---")
slides = assemble_slides(cover_frage, ergebnis["slides_2_bis_8"], ergebnis["fazit_body"])
result = render_carousel(
    slides=slides,
    topic_slug="confirmation-bias-test",
    topic_title=THEMA,
    theme="klassisch",
    output_dir="_test_output",
)
print("Vorschau-HTML:", result["preview_html"])
print("Export-Ordner:", result["export_dir"])
