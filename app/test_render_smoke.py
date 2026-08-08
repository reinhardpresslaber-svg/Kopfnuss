"""
Testlauf fuer render_module.py mit den bekannten TSST-VR-Texten
(gleicher Inhalt wie Projektvorgaben/build_carousel.py), um zu pruefen,
dass die Funktion die gleichen Ergebnisse liefert wie das Original-Skript.
"""

from render_module import render_carousel, build_cover_slide, build_cta_slide

# render_module.py hat kein eigenes "slide()"-Hilfsfunktion, daher hier lokal nachgebaut
def slide(eyebrow, body_html, footer="@KopfnussPsychologie"):
    return {"eyebrow": eyebrow, "body": body_html, "footer": footer}


slides = [
    build_cover_slide("Kannst du dich in einer virtuellen Welt genauso stressen wie im echten Leben?"),
    slide("02 / 09 &mdash; Beispiel", '''
<div class="content-mid">
  <div class="headline">Stell dir vor:</div>
  <div class="card">
    <p class="body-text" style="margin-top:0;">Du sitzt mit einer VR-Brille im Labor. Deine Aufgabe: Halte spontan eine &Uuml;berzeugungsrede vor einer Jury &ndash; die Jury sitzt nicht im Raum, sie existiert nur in deinem Headset.</p>
  </div>
</div>
'''),
    slide("03 / 09", '''
<div class="content-mid">
  <div class="headline">Der Klassiker unter Stresstests</div>
  <p class="body-text">Der Trier Social Stress Test (TSST) gilt seit den 1990ern als Goldstandard, um im Labor echten Stress auszul&ouml;sen: freie Rede und Kopfrechnen vor einer kritischen Jury. Katrin Linnig und Kolleg:innen (2024) haben nun eine frei verf&uuml;gbare VR-Version entwickelt und getestet &ndash; den Open TSST-VR.</p>
</div>
'''),
    slide("04 / 09", '''
<div class="content-mid">
  <div class="headline">Warum &uuml;berhaupt VR?</div>
  <p class="body-text">Die klassische Version ist aufwendig: Sie braucht echte Pr&uuml;fer:innen und reagiert empfindlich auf kleinste Unterschiede in deren Verhalten. Das erschwert es, Studien weltweit zu vergleichen.</p>
</div>
'''),
    slide("05 / 09", '''
<div class="content-mid">
  <div class="headline">So lief die Studie</div>
  <p class="body-text">50 M&auml;nner wurden zuf&auml;llig entweder der TSST-VR-Gruppe oder einer neutralen VR-Kontrollbedingung zugeteilt. Gemessen wurden Herzrate, Speichelcortisol und subjektives Stressempfinden &ndash; vor und nach der Aufgabe.</p>
</div>
'''),
    slide("06 / 09", '''
<div class="content-mid">
  <div class="headline">Und, hat's funktioniert?</div>
  <p class="body-text">Ja: Die Stressgruppe zeigte einen deutlich st&auml;rkeren Anstieg von subjektivem Stress <strong>und</strong> Cortisol als die Kontrollgruppe. Der K&ouml;rper reagierte also wirklich biologisch &ndash; nicht nur gef&uuml;hlt.</p>
</div>
'''),
    slide("07 / 09", '''
<div class="content-mid">
  <div class="headline">Dein K&ouml;rper macht keinen Unterschied</div>
  <p class="body-text">Eine virtuelle Jury kann eine genauso echte Stressreaktion ausl&ouml;sen wie eine echte. F&uuml;r dein Nervensystem z&auml;hlt offenbar vor allem: Werde ich gerade bewertet?</p>
</div>
'''),
    slide("08 / 09", '''
<div class="content-mid">
  <div class="headline">Warum dich das interessieren sollte</div>
  <p class="body-text">Ein g&uuml;nstigerer, besser standardisierbarer Stresstest hilft der Forschung zu Burnout, Angstst&ouml;rungen und Therapieans&auml;tzen &ndash; weltweit vergleichbar, ohne Jury-Kosten.</p>
</div>
'''),
    build_cta_slide('<p class="body-text">Selbst virtuelle Bewertung geht &bdquo;unter die Haut&ldquo; &ndash; dein K&ouml;rper reagiert, als w&auml;re sie echt.</p>'),
]

result = render_carousel(
    slides=slides,
    topic_slug="tsst-vr-test",
    topic_title="Open TSST-VR (Testlauf)",
    theme="gruen",
    output_dir="_test_output",
)

print("Vorschau-HTML:", result["preview_html"])
print("Export-Ordner:", result["export_dir"])
print("Anzahl Slide-HTMLs:", len(result["slide_htmls"]))
