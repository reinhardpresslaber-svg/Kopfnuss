# Kopfnuss Post-Generator – Bauplan für Claude Code

Ziel: eine lokale Web-App, die den bestehenden Karussell-Workflow
(Recherche → Text → Cover-Bild → Rendering) KI-gestützt orchestriert,
aber alle bewährten Freigabe-Schritte beibehält. **Instagram-Publishing
ist bewusst nicht Teil von V1** – die Architektur soll das aber später
ohne Umbau ermöglichen.

---

## 0. Scope-Entscheidungen (Stand jetzt)

| Frage | Entscheidung |
|---|---|
| Bedienung | Web-Oberfläche, erst lokal, später ggf. auf einem Server (mobiler Zugriff) |
| Instagram-Publishing | **weggelassen** – Output bleibt vorerst 9 PNGs + Caption zum manuellen Hochladen |
| Automatisches Posten | **weggelassen** |
| Modularität | Recherche / Text / Bild / Rendering als eigenständige, austauschbare Module – Publishing kann später als zusätzliches Modul angedockt werden, ohne die anderen anzufassen |
| Folien-Vorlage | Zwei bestehende Vorlagen liegen schon vor (klassisch Terrakotta/Gold & Grün) – Auswahl pro Post in der Oberfläche, keine neue Vorlage nötig |
| Podcast/Video | Nicht Teil von V1, nur als spätere Erweiterung vorgemerkt (siehe Abschnitt 5) |
| Post-Historie | Liste aller bisherigen Posts wird geführt und bei jedem neuen Thema automatisch gegengecheckt (Dopplungen vermeiden) |
| Speicherort/Zugriff | Projektordner kann in OneDrive liegen – gut für Zugriff auf fertige PNGs/Historie vom Handy aus, ersetzt aber NICHT das Ausführen der App selbst (dafür weiterhin Server-Deployment nötig, siehe Abschnitt 4, Schritt 10) |
| Versionierung | Lokales Git-Repo für Code/Konfiguration von Anfang an, zusätzlich privates GitHub-Repo als Online-Backup. Fertige PNGs bleiben in OneDrive statt in Git (siehe Abschnitt 2) |

---

## 1. Architektur-Überblick

```
[Thema eingeben]  ODER  [Button: "Thema vorschlagen"]
        │
        ▼
 ⓪ Themen-Check gegen Post-Historie (Warnung bei möglicher Dopplung)
        │
        ▼
 ① Recherche-Modul  (Studie finden/einlesen, strukturiert zusammenfassen)
        │
        ▼
 ② Text-Modul (Claude API)
    a) 3 Cover-Frage-Vorschläge  →  Freigabe durch Ansgar
    b) restliche 8 Slide-Texte + Caption  →  Freigabe durch Ansgar
        │
        ▼
 ③ Bild-Modul (Nano Banana / Gemini API)
    Cover-Frage → Prompt-Template → Bild  →  Freigabe/Regenerieren
        │
        ▼
 ④ Render-Modul (bestehende build_carousel.py-Logik)
    Texte + Bild → HTML → wkhtmltoimage → 9 PNGs
        │
        ├──▶ Post-Historie wird um den neuen Eintrag ergänzt
        ▼
   [Output: 9 PNGs + Caption, bereit zum manuellen Upload]

   (später optional: ⑤ Publish-Modul → Instagram Graph API)
```

Jedes Modul ist eine eigene Python-Funktion/eigenes Skript mit klar
definiertem Ein-/Ausgabeformat (JSON), damit die Web-Oberfläche sie
nacheinander aufrufen kann und du an jedem Freigabepunkt eingreifen
kannst.

---

## 2. Tech-Stack-Empfehlung

- **Backend/Logik:** Python (baut direkt auf `build_carousel.py`,
  `style_with_icon.css`, Logo-Assets auf – nichts davon wird ersetzt,
  nur automatisiert angesteuert)
- **Web-Oberfläche:** Streamlit – schnell in Claude Code baubar, läuft
  lokal mit einem Befehl (`streamlit run app.py`), lässt sich später
  1:1 auf einen kleinen Server/VPS oder Streamlit Community Cloud
  deployen, ohne dass du das UI neu bauen musst. Für unterwegs reicht
  dann ein Browser-Tab.
- **Text-Generierung:** Anthropic API (Claude), System-Prompt mit dem
  kompletten Inhalt von `kopfnuss-design-system.md` als feste Regel
- **Bild-Generierung:** Google Gemini API, Modell `gemini-2.5-flash-image`
  ("Nano Banana", ~0,039 $/Bild). Bei Bedarf später Wechsel auf
  `gemini-3.1-flash-image` ("Nano Banana 2") für höhere Auflösung –
  eigener API-Key bei Google AI Studio nötig, unabhängig vom
  Anthropic-Key.
- **Recherche:** Semantic Scholar API / Europe PMC / CrossRef für
  echte Studien statt allgemeiner Websuche – passt besser zum
  Anspruch, Methodik/Limitationen sauber einzuordnen.
- **Secrets:** `.env`-Datei (Anthropic-Key, Gemini-Key), nie ins Repo
  committen.
- **Post-Historie:** einfache CSV- oder JSON-Datei im Projektordner,
  kein Datenbank-Overhead nötig für diese Größenordnung.
- **Versionierung:** lokales Git-Repo für Code, Konfiguration, Design-
  System und Vorlagen, zusätzlich ein privates GitHub-Repo als
  Online-Backup. Die generierten PNG-Ordner (bisherige + neue Posts)
  werden bewusst NICHT in Git versioniert – Bilddateien lassen sich
  dort nicht sinnvoll vergleichen und würden das Repo unnötig
  aufblähen. Klare Aufteilung: Git = Code-Absicherung, OneDrive =
  Zugriff auf fertige Bilder/Historie. Ein `.gitignore` schließt u. a.
  `.env`, generierte Export-Ordner und Python-Umgebungsdateien aus.

**Projekt-Ordner:** Ihr habt bereits einen lokalen Ordner (C:-Laufwerk) mit
den zwei bestehenden Folien-Vorlagen (klassisch & grün). Wichtig für den
Start mit Claude Code: Dieser Chat hier läuft in einer isolierten
Sandbox-Umgebung ohne Zugriff auf deine lokale Festplatte – der Ordner
kann also nicht in dieser Konversation eingebunden werden. Claude Code
läuft dagegen direkt auf deinem Rechner und hat echten Dateizugriff.
Praktisch heißt das: Du startest Claude Code im (oder mit Zeiger auf den)
bestehenden Ordner, und ich sichte dort zu Beginn die beiden Vorlagen
1:1, bevor das Render-Modul gebaut wird – genau wie ich hier jedes Mal
`kopfnuss-design-system.md` und `build_carousel.py` vor einem neuen
Post lese.

---

## 3. Module im Detail

### ⓪ Themen-Vorschlag & Post-Historie
- **Themen-Vorschlag (neu):** Button "Thema vorschlagen" – Claude
  schlägt 2–3 Kandidaten vor, mit je einer Zeile Begründung, warum das
  Thema breit interessant ist. Kriterien im Prompt: alltagsnahes,
  wiedererkennbares psychologisches Phänomen, gut erforscht/seriöse
  Evidenzlage (kein reines Hype-Thema), passt zum Kopfnuss-Ton. Gefällt
  keiner der Vorschläge, einfach neue anfordern.
- Führt eine einfache, strukturierte Liste aller bisherigen Posts
  (z. B. `posts_historie.csv` oder `.json` im Projektordner): Datum,
  Thema/Titel, finale Cover-Frage, Slug, ggf. Studie/Quelle,
  Farbthema.
- Egal ob Thema selbst eingetippt oder von Claude vorgeschlagen: bevor
  die Recherche losläuft, wird es gegen diese Liste geprüft (per
  Claude: nicht nur exakte Übereinstimmung, sondern auch inhaltlich
  ähnliche Themen erkennen, z. B. "Impostor Syndrom" vs.
  "Hochstapler-Syndrom"). Die Themen-Vorschlag-Funktion nutzt dieselbe
  Prüfung intern schon beim Generieren, damit möglichst keine bereits
  behandelten Themen vorgeschlagen werden. Bei Treffer trotzdem:
  Hinweis mit Datum/Titel des bisherigen Posts, du entscheidest, ob du
  weitermachst (z. B. neue Studie zum selben Thema) oder abbrichst.
- Nach dem Rendern eines neuen Posts wird automatisch ein Eintrag
  angehängt – die Liste wächst mit jedem Post mit, ohne dass du sie
  manuell pflegen musst.
- Liegt der Projektordner in OneDrive, ist diese Liste (und die
  fertigen PNGs) bequem vom Handy aus einsehbar, auch ohne dass die
  App selbst dort läuft.

### ① Recherche-Modul
- Input: entweder ein Thema (String) oder eine vorgegebene Studie
  (Text/PDF/Link).
- Bei Thema, zweistufig: **zuerst** wissenschaftliche APIs (Semantic
  Scholar / Europe PMC / CrossRef); liefern die keine ausreichend
  passenden Treffer, **Fallback** auf allgemeine Websuche. Ergebnisse
  aus dem Fallback werden in der Oberfläche als "nicht aus
  wissenschaftlicher Datenbank" markiert, damit beim Texten klar
  bleibt, ob die übliche Evidenzlage-Einordnung (Design-System,
  Abschnitt 2, "keine Übertreibung bei unsicherer Evidenzlage")
  besonders wichtig ist.
- Output (JSON): Autor:innen, Jahr, Kernbefund in einfachen Worten,
  Methodik, Limitationen/Kritikpunkte – exakt die Bausteine, die
  Abschnitt 2 des Design-Systems verlangt ("Zitate/Studien: Autor:innen
  und Jahr nennen, Kernbefund in eigenen Worten wiedergeben").

### ② Text-Modul
- System-Prompt enthält das komplette Design-System 1:1 (Struktur,
  Sprache, Ton, redaktionelle Regeln).
- Schritt a: 3 Cover-Fragen-Vorschläge generieren, dabei **nur Text**ausgeben, kein Layout-Vorschlag.
- Schritt b: nach deiner Auswahl (inkl. optionaler Korrektur) die
  Slides 2–9 + Caption generieren.
- Beide Schritte stoppen und warten auf deine Freigabe in der
  Oberfläche, bevor es weitergeht – identisch zur bisherigen Regel
  "Textfreigabe zuerst".

### ③ Bild-Modul
- Nimmt die freigegebene Cover-Frage, setzt sie ins bestehende
  deutsche Prompt-Template (`[SLIDE-1-FRAGE HIER EINFÜGEN]`).
- Ruft Nano Banana auf, zeigt Ergebnis in der Oberfläche, Buttons für
  "Übernehmen" oder "Neu generieren".
- **Layout-Entscheidung (steht fest):** Bild als **Hintergrund** von
  Slide 1, Logo + Headline liegen darüber. Details wie Text-Kontrast
  (z. B. dezentes Overlay/Scrim, damit die Headline über
  unterschiedlichsten Bildmotiven lesbar bleibt), Bildausschnitt und
  Zusammenspiel mit den bestehenden Blob-Deko-Elementen klären wir,
  sobald das erste generierte Bild vorliegt – wie gewohnt als
  PNG-Vorschau zur Freigabe, bevor es Standard in `build_carousel.py`
  wird.

### ④ Render-Modul
- Die bestehende Logik aus `build_carousel.py` (SLIDES-Struktur,
  `make_slide_div`, Export-Template, `GREEN_THEME_OVERRIDE` etc.)
  wird als Funktion `render_carousel(slides, topic_slug, theme)`
  wiederverwendet statt als Skript mit manuell editierten Konstanten.
- `theme` ist ein einfacher Parameter ("klassisch" / "grün"), den du in
  der Oberfläche vor dem Rendern auswählst – die Weiche existiert im
  Prinzip schon (`GREEN_THEME_OVERRIDE`). Falls die beiden Vorlagen im
  lokalen Ordner weiter auseinanderlaufen als nur die Akzentfarben,
  sichte ich das bei Projektstart und baue die Weiche entsprechend
  breiter (z. B. zwei komplette CSS-Dateien statt eines Overrides).
- Danach automatisierter `wkhtmltoimage`-Batch-Aufruf über
  `subprocess` für alle 9 Slides.
- Output: gleiche Dateistruktur wie heute
  (`slides_export_<thema>/slide-1.png` … `slide-9.png`).

---

## 4. Schritt-für-Schritt-Bauplan (für Claude Code)

1. **Vorbereitung:** Anthropic-API-Key und Google-AI-Studio-Key
   besorgen, in `.env` ablegen.
2. **Projektgerüst:** Neuer Ordner, bestehende Assets
   (`style_with_icon.css`, `logo_full_transparent_b64.txt`,
   `build_carousel.py`) hineinkopieren als Ausgangsbasis. Direkt dabei:
   lokales Git-Repo einrichten, `.gitignore` anlegen (u. a. `.env`,
   generierte Export-Ordner, Python-Umgebung), ersten Commit machen.
   Danach optional ein privates GitHub-Repo als Online-Backup
   verbinden.
3. **Render-Modul zuerst bauen:** `build_carousel.py` in eine
   aufrufbare Funktion umbauen (gleiche Logik, nur parametrisiert
   statt hartkodierter SLIDES) – das ist die Grundlage für alles
   Weitere und lässt sich isoliert testen (mit den bereits bekannten
   TSST-VR-Texten als Testdaten).
4. **Post-Historie & Themen-Vorschlag:** Datenformat festlegen
   (CSV/JSON), Funktionen zum Anhängen neuer Einträge, zum
   Gegenchecken eines Themas gegen die Liste, und für den
   "Thema vorschlagen"-Button (Claude-Call mit Kriterien für breite
   Alltagsrelevanz + Dopplungs-Check gegen dieselbe Liste). Historie
   mit den bisherigen Themen aus diesem Chat (Prospect Theory,
   Impostor Syndrom, Zimbardo, Vier-Seiten-Modell, ReSource-Projekt,
   TSST-VR) als Startdaten befüllen.
5. **Text-Modul:** Claude-API-Anbindung, System-Prompt aus
   `kopfnuss-design-system.md` generieren, Funktionen für
   Cover-Vorschläge und Rest-Slides, mit Zwischenspeicherung des
   Freigabestatus.
6. **Recherche-Modul:** Anbindung an eine wissenschaftliche API plus
   Websuche-Fallback, danach Testlauf mit einem bekannten Thema.
7. **Bild-Modul:** Gemini-API-Anbindung, Prompt-Template einbauen,
   neues Slide-1-Hintergrundbild-Layout im Design-System ergänzen und
   einmal freigeben lassen.
8. **Streamlit-Oberfläche:** alle Module hintereinanderschalten, mit
   Buttons/Freigabe-Schritten zwischen jeder Station (Thema eingeben
   ODER "Thema vorschlagen"-Button → Historien-Check → Vorlage wählen
   [klassisch/grün] → Cover wählen → Texte freigeben → Bild freigeben
   → Rendern-Button → Download der 9 PNGs + Caption).
9. **End-to-End-Test:** kompletten Durchlauf an einem bereits
   bekannten Thema (z. B. TSST-VR erneut) testen, um die Ergebnisse
   mit dem manuell erstellten Post zu vergleichen.
10. **(Optional, später) Server-Deployment:** Streamlit-App auf einem
    kleinen VPS oder Streamlit Community Cloud hosten, Secrets über
    Umgebungsvariablen statt lokaler `.env`.
11. **(Optional, später) Publish-Modul:** Instagram-Business-Account +
    Meta-Entwickler-App einrichten, Bild-Hosting-Lösung für öffentlich
    erreichbare URLs, Graph-API-Container-Flow (oder ein fertiger
    MCP-Server dafür) als eigenständiges Modul andocken – ohne die
    anderen Module anzufassen.

---

## 5. Spätere Erweiterung: Podcast & kurze Videos

Reine Einschätzung für später, nichts davon jetzt bauen.

**ElevenLabs Pro jetzt schon abonnieren? Eher nicht.**
Seit Mai 2026 hat ElevenLabs API-Nutzung von den UI-Abos entkoppelt –
man kann die API pay-as-you-go nutzen, ohne ein monatliches Abo zu
brauchen. Der Pro-Tarif (99 $/Monat, ~500–600k Credits) lohnt sich erst
bei regelmäßiger, hoher Produktion. Für den Einstieg reicht entweder
der kostenlose Tarif zum Testen oder der Starter-Tarif (~5–6 $/Monat:
kommerzielle Rechte, API-Zugang, Voice Cloning) – das deckt einen
ersten Podcast-Prototyp locker ab. Meine Empfehlung: Thema zurückstellen,
bis das Podcast-Modul tatsächlich gebaut wird, und dann mit
Free/Starter + API-Pay-as-you-go anfangen statt vorab ein Abo zu binden.

**Für kurze Video-Teaser:** Da ihr für Nano Banana ohnehin einen Google
AI Studio-Key habt, liegt es nahe, für Video im selben Ökosystem zu
bleiben. Zwei Kandidaten:
- **Gemini Omni Flash** (Google, seit Mai 2026): bis zu 10 Sekunden,
  Ton nativ dabei, für Social-Media-Formate wie Instagram-Teaser
  konzipiert und deutlich günstiger als Veo – aktuell bester
  Preis-Leistungs-Kandidat für kurze IG-Clips, sofern der Entwickler-API-Zugang
  (Stand jetzt: Rollout läuft) zum Zeitpunkt der Umsetzung verfügbar ist.
- **Veo 3.1** (Google, über Gemini API/Vertex AI): höhere Qualität
  (bis 4K, Szenen-Verlängerung), aber mit ca. 0,75 $/Sekunde deutlich
  teurer – eher relevant, falls die Bildqualität später wichtiger wird
  als die Kosten pro Clip.

Beides würde denselben Google-Key nutzen wie Nano Banana, es kommt also
kein zusätzlicher Anbieter dazu, nur ein weiteres Modell auf derselben
Plattform.

---

## 6. Offene Punkte für später

- Ob Nano Banana oder Nano Banana 2 das bessere Preis-Qualitäts-
  Verhältnis fürs Cover-Bild liefert – am besten an 2–3 echten Themen
  vergleichen, bevor man sich festlegt.
- Genaue Text-Overlay-Lösung fürs Hintergrundbild auf Slide 1 (wie
  stark abgedunkelt/geweicht, damit Headline + Logo bei jedem
  generierten Motiv lesbar bleiben) – klären wir am ersten echten
  Beispielbild.
- Ob der Fallback auf allgemeine Websuche automatisch greifen soll,
  wenn die wissenschaftlichen APIs nichts Passendes liefern, oder ob
  du das jedes Mal manuell bestätigen möchtest.
- Ob bereits ein GitHub-Account vorhanden ist oder für das private
  Backup-Repo neu angelegt werden muss (kostenlos, falls nötig:
  https://github.com/join).
- Server-Wahl fürs spätere Deployment (VPS vs. Streamlit Community
  Cloud vs. etwas anderes) – hat u. a. Auswirkungen auf Kosten und wie
  die Secrets verwaltet werden.
