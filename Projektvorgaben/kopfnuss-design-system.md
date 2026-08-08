# Kopfnuss – Design System & Content Guidelines

Kanal: **@KopfnussPsychologie**
Claim (nur letzte Slide als CTA): **"KopfnussPsychologie | Wissenswertes aus Psychologie & Coaching"**
Betreiber: Diplom-Psychologe

Diese Datei ist die einzige Referenz, die für neue Karussell-Posts gebraucht wird.
Zusammen mit `build_carousel.py`, `style_with_icon.css` und dem Logo-PNG reicht das,
um jedes neue Thema im gleichen Format zu produzieren.

---

## 1. Struktur eines Karussells (immer 9 Slides)

| # | Inhalt |
|---|--------|
| 1 | **Cover** – catchy Frage, die den Leser direkt mit "du" anspricht (nie "man" oder unpersönlich) |
| 2 | **Beispiel** – konkrete Alltagssituation, so einfach formuliert, dass kein Vorwissen nötig ist. Kommt IMMER vor der Theorie. |
| 3 | **Kerngedanke / Definition** – wer hat das Konzept geprägt, Kernaussage |
| 4 | **Mechanismus Teil 1** – wie funktioniert es |
| 5 | **Mechanismus Teil 2** – Beispiele, Unterscheidung, oder Aufschlüsselung (z.B. als 3er-Trio oder Bulletpoints) |
| 6 | **Mechanismus Teil 3 / Vertiefung** | 
| 7 | **Kernaussage / Zuspitzung** – der "Aha"-Satz des Posts |
| 8 | **Warum das relevant ist** – Alltagsrelevanz, Transfer |
| 9 | **Fazit + CTA** – praktische Konsequenz, dann: Bookmark-Icon (Instagram-Speichern-Symbol) + "Speichern", darunter Teilen-Icon (Papierflieger) + "Teilen" sowie Repost-Icon (Doppelpfeil) + "Repost" nebeneinander, dann 👉 Folge @KopfnussPsychologie \| Wissenswertes aus Psychologie & Coaching (siehe Abschnitt 4) |

Die genaue Aufteilung von Slide 3-8 variiert je nach Thema – wichtig ist nur:
Beispiel vor Theorie, catchy Frage auf Slide 1, offizieller Claim auf Slide 9.

## 2. Redaktionelle Regeln

- **Sprache:** Einfach, klar, ohne unnötigen Fachjargon. Wenn ein Fachbegriff nötig ist, sofort in Alltagssprache übersetzen.
- **Ton:** Seriös (Diplom-Psychologe als Absender), aber zugänglich und "catchy" – kein trockener Lehrbuchstil.
- **Beispiele:** Immer so schreiben, dass sofort klar ist, was in jeder Vergleichsgruppe/Situation tatsächlich passiert – keine Formulierungen, die zu Missverständnissen führen (z.B. nicht "beide meditieren", wenn nur eine Gruppe meditiert).
- **Zitate/Studien:** Autor:innen und Jahr nennen, Kernbefund in eigenen, einfachen Worten wiedergeben.
- **Keine Übertreibung:** Bei unsicherer Evidenzlage (z.B. Aufstellungsarbeit) das explizit einordnen.

## 3. Caption-Regeln

- Aufbau: knackiger Opener-Satz → wissenschaftlicher Hintergrund (2-3 Absätze, einfach erklärt) → praktische Konsequenz
- **CTA nur:** 🔖 Speichern-Hinweis + 🔁 Teilen-/Repost-Hinweis (in der Caption als Emoji, auf den Slides als SVG-Icons, siehe Abschnitt 4) + 👉 Folge @KopfnussPsychologie | Wissenswertes aus Psychologie & Coaching
- **Nie:** Aufforderung zum direkten Kommentieren/"Schreib mir" persönlicher Situationen (kann bei sensiblen Themen ausufern)
- 5 Hashtags (Instagram-Karussell-Limit), thematisch passend, ohne Massenhashtags

## 4. Branding

- **Logo:** zweigeteiltes Gehirn-Icon (Terrakotta links / Salbeigrün rechts, orange/beige Balken, Terrakotta/Dunkelgrün-Schale mit weißem Lächeln)
- Auf Slide 1: Logo groß (Icon + Wortmarke "Kopfnuss"), darunter die Cover-Frage
- Auf Slide 2-9: Logo klein (nur Icon) oben rechts als wiederkehrendes Wasserzeichen
- Jede Slide: dünne Trennlinie + Handle `@KopfnussPsychologie` unten links als Footer
- **Speichern-Icon auf Slide 9:** kein Emoji, sondern das Instagram-typische Bookmark-Symbol (Lesezeichen-Umriss) als Inline-SVG. Liegt in `build_carousel.py` als wiederverwendbare Konstante `BOOKMARK_ICON_SVG` vor und wird in der CTA-Zeile vor "Speichern" eingesetzt. Erbt automatisch die Textfarbe (`stroke="currentColor"`).
- **Teilen-/Repost-Icons auf Slide 9:** direkt unter der Speichern-Zeile, nebeneinander in einer eigenen `.cta-row`:
  - **Teilen** – Papierflieger-Umriss (Send-Icon), Konstante `SHARE_ICON_SVG`, `stroke="currentColor"`, analog zum Bookmark-Icon.
  - **Repost** – zwei gegenläufige Pfeile (klassisches Retweet-/Repost-Symbol), Konstante `REPOST_ICON_SVG`, da im Original durchgehend gefüllt mit `fill="currentColor"` statt `stroke`.
  - Layout über `.cta-row` / `.cta-item` in `style_with_icon.css`: Flexbox mit Abstand zwischen den beiden Icon+Label-Paaren, kein manuelles `vertical-align`.

## 5. Visuelles Design

**Format:** 1080×1350 px (Instagram 4:5, Hochformat)

**Farbpalette (aus dem Logo abgeleitet):**
| Rolle | Hex |
|---|---|
| Hintergrund hell | `#FBF6EF` |
| Hintergrund alt. (jede 2. Slide) | `#F2E6D3` |
| Text (dunkel) | `#2C2420` |
| Text (soft/Fließtext) | `#6B5847` |
| Terrakotta (Akzent 1) | `#C15A2E` |
| Salbeigrün (Akzent 2) | `#8FBFA0` |
| Dunkelgrün (Akzent 3) | `#2E4A3B` |
| Gold/Orange (Akzent 4) | `#EDA23E` |
| Karten-Hintergrund | `#FFFDF9` |

Slides alternieren zwischen Hintergrund hell und Hintergrund alt. (ungerade = hell, gerade = alt.)

**Alternative Farbthemen:**
Die Standard-Akzentfarbe ist Terrakotta (`--rust`). Für Themen, bei denen ein
kräftigerer, dunklerer Grünton besser passt, gibt es ein optionales Grün-Theme.
Es überschreibt nur die Akzentfarben, Hintergrund/Text/Typografie bleiben gleich:

| Variable | Standard | Grün-Variante |
|---|---|---|
| `--rust` (Eyebrow, Footer-Linie, Trio-Rahmen, Blobs) | `#C15A2E` | `#235C3D` |
| `--gold` (Blobs) | `#EDA23E` | `#4C7A40` |
| `--moss` (Bullets, Blobs) | `#8FBFA0` | `#6FA283` |
| `.blob` Deckkraft | `0.16` | `0.34` (sonst wirkt Grün zu blass) |

Umsetzung: in `build_carousel.py` die Konstante `GREEN_THEME_OVERRIDE` (CSS-Variablen-
Override) in den `<style>`-Block der Vorschau- und Export-Templates einfügen. Das
Basis-CSS (`style_with_icon.css`) bleibt dabei unverändert – die Wahl des Farbthemas
ist eine bewusste Entscheidung pro Post, kein neuer Standard.

**Typografie:**
- Headlines: **Fraunces** (Serif, weight 900), 56-78px
- Fließtext: **Karla**, 34px, Zeilenhöhe 1.5
- Eyebrow-Label (oben links, "01/09 — Thema"): Karla Bold, 22px, Buchstabenabstand 2.5px, Terrakotta

**Wiederkehrende Layout-Elemente:**
- Organische, halbtransparente "Blob"-Kreise im Hintergrund (Terrakotta/Gold/Salbeigrün, wechselnde Position)
- Trio-Layout für 3 Vergleichspunkte (z.B. drei Attributionsstile): 3 Karten nebeneinander, je mit farbigem oberen Rand
- Karten (`.card`) für Beispiel-Slides: heller Kasten mit Schatten, hebt die Alltagssituation optisch ab
- Bulletpoints: farbiger runder Punkt statt Standard-Bullet

## 6. Technische Umsetzung

Alle Dateien liegen im Project-Knowledge:
- `build_carousel.py` – Python-Script, das aus einer Liste von 9 Slide-Inhalten sowohl eine interaktive HTML-Vorschau als auch 9 einzelne PNG-Export-HTMLs erzeugt. Enthält auch `BOOKMARK_ICON_SVG`, `SHARE_ICON_SVG` und `REPOST_ICON_SVG` für Slide 9 sowie optional `GREEN_THEME_OVERRIDE` für die grüne Farbvariante.
- `style_with_icon.css` – das komplette CSS inkl. Logo-Icon als eingebettetes Base64-Hintergrundbild
- `logo_full_transparent.png` / `logo_full_transparent_b64.txt` – große Logo-Version (Icon + Wortmarke) für Slide 1

**Workflow für einen neuen Post:**
1. Slide-Inhalte nach obigem 9-Slide-Schema texten (inkl. Caption). Für die Cover-Frage auf Slide 1 **immer 3 Formulierungsvorschläge** zur Auswahl anbieten, nicht nur eine fertige Formulierung.
2. **Textfreigabe zuerst:** Der komplette Text-Inhalt aller 9 Slides wird mit Ansgar abgestimmt und freigegeben, bevor irgendetwas gerendert wird. Erst nach Freigabe geht es weiter zu Schritt 3.
3. `build_carousel.py` mit den freigegebenen Texten befüllen (siehe Kommentare im Script)
4. Script ausführen → erzeugt `carousel_<thema>.html` (Vorschau) + `slides_export_<thema>/slide-1.html` bis `slide-9.html`
5. Jede `slide-N.html` mit `wkhtmltoimage --width 1080 --height 1350 --disable-smart-width slide-N.html slide-N.png` in ein PNG rendern
6. PNGs als Karussell hochladen, Caption separat kopieren
