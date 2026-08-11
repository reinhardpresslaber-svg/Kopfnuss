"""
Kopfnuss - einfache Streamlit-Oberflaeche (V1, erster Entwurf)
=================================================================
Verbindet die bereits fertigen Module zu einem klickbaren Ablauf:
Thema eingeben -> Cover-Frage waehlen -> Slides & Caption generieren
-> Vorschau ansehen.

"""

import base64
import html as html_lib
import io
import os
import re
import shutil
import zipfile

import streamlit as st

from post_historie import check_topic, append_post
from research_module import schlage_studien_vor
from text_module import (
    generate_cover_optionen,
    generate_slides_und_caption,
    generate_gemini_video_prompt,
    proofread_slides_und_caption,
    proofread_cover_optionen,
    assemble_slides,
)
from render_module import (
    render_carousel,
    export_pngs,
    export_reel_cover,
    render_cover_preview_html,
    parse_slide_body,
    build_slide_body,
    parse_fazit_body,
    build_fazit_body,
)
from image_module import generate_cover_bild

st.set_page_config(page_title="Kopfnuss Post-Generator", page_icon="🥜", layout="centered")
st.title("🥜 Kopfnuss Post-Generator")

APP_PASSWORT = os.environ.get("APP_PASSWORT")
if APP_PASSWORT and not st.session_state.get("eingeloggt"):
    pw = st.text_input("Passwort", type="password", key="login_passwort")
    if pw:
        if pw == APP_PASSWORT:
            st.session_state.eingeloggt = True
            st.rerun()
        else:
            st.error("Falsches Passwort.")
    st.stop()

POSTS_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Posts")


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def recherche_als_kontext(r):
    return (
        f"Titel: {r['titel']}\nAutor:innen: {r['autoren']} ({r['jahr']})\n"
        f"Kernbefund: {r['kernbefund']}\nMethodik: {r['methodik']}\n"
        f"Limitationen: {r['limitationen']}"
    )


def copy_button_widget(text, label="Text kopieren", height=230, box_height=160):
    """
    Zeigt ein Textfeld mit einem 'Kopieren'-Button, der auch auf dem iPhone
    funktioniert. Nutzt document.execCommand('copy') statt der modernen
    Async-Clipboard-API, weil Safari Letztere nur ueber https/localhost
    erlaubt (die App wird oft ueber die Netzwerk-IP per http aufgerufen).
    """
    text_escaped = html_lib.escape(text)
    component_html = f"""
    <div style="font-family:'Source Sans Pro', sans-serif;">
      <textarea id="capbox" readonly style="width:100%; box-sizing:border-box; height:{box_height}px;
        padding:8px; border-radius:6px; border:1px solid #ccc; font-family:inherit;
        font-size:14px; resize:vertical;">{text_escaped}</textarea>
      <button id="copybtn" style="margin-top:8px; padding:8px 16px; border-radius:6px;
        border:none; background:#C15A2E; color:white; font-size:14px; cursor:pointer;">
        {label}
      </button>
      <span id="copystatus" style="margin-left:10px; font-size:14px; color:#2E4A3B;"></span>
    </div>
    <script>
      const box = document.getElementById('capbox');
      const btn = document.getElementById('copybtn');
      const status = document.getElementById('copystatus');
      btn.addEventListener('click', function() {{
        box.focus();
        box.select();
        box.setSelectionRange(0, box.value.length);
        let ok = false;
        try {{ ok = document.execCommand('copy'); }} catch (e) {{ ok = false; }}
        if (ok) {{
          status.textContent = 'Kopiert!';
        }} else if (navigator.clipboard && navigator.clipboard.writeText) {{
          navigator.clipboard.writeText(box.value).then(function() {{
            status.textContent = 'Kopiert!';
          }}).catch(function() {{
            status.textContent = 'Kopieren fehlgeschlagen - bitte Text manuell markieren.';
          }});
        }} else {{
          status.textContent = 'Kopieren fehlgeschlagen - bitte Text manuell markieren.';
        }}
        setTimeout(function() {{ status.textContent = ''; }}, 2500);
      }});
    </script>
    """
    st.components.v1.html(component_html, height=height)


for key, default in [
    ("recherche", None),
    ("cover_optionen", None),
    ("cover_frage", ""),
    ("slides_ergebnis", None),
    ("render_ergebnis", None),
    ("png_paths", None),
    ("cover_bild_bytes", None),
    ("video_prompt", None),
    ("studien_vorschlaege", None),
    ("reel_cover_path", None),
]:
    if key not in st.session_state:
        st.session_state[key] = default

st.header("1. Thema")
with st.container(horizontal=True, vertical_alignment="bottom"):
    thema = st.text_input("Worum soll der Post gehen?", key="thema_input")
    st.button("Bestaetigen", icon=":material/keyboard_return:", help="Eingabe bestaetigen")
farbthema = st.radio("Farbthema", ["klassisch", "gruen"], horizontal=True)

if thema:
    treffer = check_topic(thema)
    if treffer:
        st.warning("Aehnliche Themen gibt es schon:")
        for t in treffer:
            st.write(f"- {t['thema']} ({t['cover_frage']})")

st.header("2. Quelle recherchieren")
if st.button("Quelle recherchieren", disabled=not thema):
    with st.spinner("Claude nennt 3 passende Studien..."):
        st.session_state.studien_vorschlaege = schlage_studien_vor(thema)
    st.session_state.recherche = None

if st.session_state.studien_vorschlaege:
    studien = st.session_state.studien_vorschlaege
    optionen = [f"{s['titel']} - {s['autoren']} ({s['jahr']})" for s in studien]
    auswahl_idx = st.radio(
        "Welche Studie passt am besten?",
        range(len(optionen)),
        format_func=lambda i: optionen[i],
        key="studie_auswahl",
    )
    st.session_state.recherche = studien[auswahl_idx]
    st.caption(
        "Von Claude aus dem eigenen Wissen vorgeschlagen, nicht live recherchiert - "
        "bei Bedarf selbst gegenchecken."
    )

if st.session_state.recherche:
    r = st.session_state.recherche
    with st.expander("Details (Kernbefund, Methodik, Limitationen)"):
        st.write("**Kernbefund:**", r["kernbefund"])
        st.write("**Methodik:**", r["methodik"])
        st.write("**Limitationen:**", r["limitationen"])

kontext = recherche_als_kontext(st.session_state.recherche) if st.session_state.recherche else ""

if st.button("Cover-Vorschlaege generieren", disabled=not thema):
    with st.spinner("Claude ueberlegt sich 3 Formulierungen..."):
        vorschlaege = generate_cover_optionen(thema, kontext=kontext)
        st.session_state.cover_optionen = proofread_cover_optionen(vorschlaege)
    st.session_state.slides_ergebnis = None
    st.session_state.render_ergebnis = None
    st.session_state.cover_bild_bytes = None

if st.session_state.cover_optionen:
    st.header("3. Cover-Frage auswaehlen")
    auswahl = st.radio(
        "Welche Formulierung gefaellt dir am besten?",
        st.session_state.cover_optionen,
        format_func=lambda o: f"{o['teil1']} {o['teil2']}",
        key="cover_auswahl",
    )
    cover_teil1 = st.text_input("Cover-Frage - Teil 1 (kannst du hier noch anpassen):", value=auswahl["teil1"])
    cover_teil2 = st.text_input(
        "Cover-Frage - Teil 2 (wird in Terrakotta hervorgehoben):", value=auswahl["teil2"]
    )
    cover_frage = f"{cover_teil1} {cover_teil2}".strip()
    cover_frage_html = f'{cover_teil1} <span style="color:var(--rust);">{cover_teil2}</span>'

    st.header("4. Cover-Bild")
    bild_button_label = "Neu generieren" if st.session_state.cover_bild_bytes else "Cover-Bild generieren"
    if st.button(bild_button_label):
        with st.spinner("Gemini erzeugt ein passendes Motiv..."):
            st.session_state.cover_bild_bytes = generate_cover_bild(cover_frage)

    if st.session_state.cover_bild_bytes:
        bild_b64_preview = base64.b64encode(st.session_state.cover_bild_bytes).decode("ascii")
        preview_html = render_cover_preview_html(cover_frage_html, bild_b64=bild_b64_preview, theme=farbthema)
        st.components.v1.html(preview_html, height=460)

    if st.button("Slides & Caption generieren"):
        with st.spinner("Claude schreibt die Slides 2-8, das Fazit und die Caption..."):
            ergebnis = generate_slides_und_caption(thema, cover_frage, kontext=kontext)
        with st.spinner("Claude prueft Umlaute, Grammatik und fehlende Woerter..."):
            korrigiert = proofread_slides_und_caption(ergebnis, ergebnis["caption"])
        st.session_state.slides_ergebnis = korrigiert
        st.session_state.cover_frage = cover_frage
        st.session_state.render_ergebnis = None
        st.session_state.png_paths = None
        for i in range(2, 9):
            st.session_state.pop(f"label_{i}", None)
            st.session_state.pop(f"headline_{i}", None)
            st.session_state.pop(f"bodytext_{i}", None)
            st.session_state.pop(f"body_{i}", None)
            for j in range(3):
                st.session_state.pop(f"trio_titel_{i}_{j}", None)
                st.session_state.pop(f"trio_text_{i}_{j}", None)
        st.session_state.pop("fazit_body_edit", None)
        st.session_state.pop("caption_edit", None)
        st.session_state.video_prompt = None
        st.session_state.pop("video_prompt_edit", None)

    if st.session_state.slides_ergebnis:
        st.header("5. Texte bearbeiten (optional)")
        ergebnis = st.session_state.slides_ergebnis
        for i, s in enumerate(ergebnis["slides_2_bis_8"], start=2):
            titel = f"Slide {i}" + (f" – {s['label']}" if s.get("label") else "")
            with st.expander(titel):
                st.text_input("Label", value=s["label"], key=f"label_{i}")
                parsed = parse_slide_body(s["body"])
                if parsed["type"] == "trio":
                    st.text_input("Überschrift", value=parsed["headline"], key=f"headline_{i}")
                    for j, item in enumerate(parsed["items"]):
                        col1, col2 = st.columns([1, 2])
                        col1.text_input(f"Punkt {j + 1} – Titel", value=item["titel"], key=f"trio_titel_{i}_{j}")
                        col2.text_input(f"Punkt {j + 1} – Text", value=item["text"], key=f"trio_text_{i}_{j}")
                elif parsed["type"] in ("card", "simple"):
                    st.text_input("Überschrift", value=parsed["headline"], key=f"headline_{i}")
                    st.text_area("Text", value=parsed["body"], height=100, key=f"bodytext_{i}")
                else:
                    st.caption("Unbekanntes Format - hier bleibt der HTML-Code sichtbar.")
                    st.text_area("HTML-Body", value=parsed["html"], height=180, key=f"body_{i}")
        fazit_text = parse_fazit_body(ergebnis["fazit_body"])
        st.text_area("Fazit-Text (Slide 9)", value=fazit_text, height=100, key="fazit_body_edit")

        if st.button("Vorschau rendern"):
            with st.spinner("Baue die Vorschau..."):
                slides_2_bis_8 = []
                for i, s in enumerate(ergebnis["slides_2_bis_8"], start=2):
                    parsed = parse_slide_body(s["body"])
                    if parsed["type"] == "trio":
                        parsed["headline"] = st.session_state[f"headline_{i}"]
                        parsed["items"] = [
                            {
                                "titel": st.session_state[f"trio_titel_{i}_{j}"],
                                "text": st.session_state[f"trio_text_{i}_{j}"],
                            }
                            for j in range(3)
                        ]
                    elif parsed["type"] in ("card", "simple"):
                        parsed["headline"] = st.session_state[f"headline_{i}"]
                        parsed["body"] = st.session_state[f"bodytext_{i}"]
                    else:
                        parsed["html"] = st.session_state[f"body_{i}"]
                    slides_2_bis_8.append(
                        {"label": st.session_state[f"label_{i}"], "body": build_slide_body(parsed)}
                    )
                fazit_body = build_fazit_body(st.session_state["fazit_body_edit"])
                bild_b64 = (
                    base64.b64encode(st.session_state.cover_bild_bytes).decode("ascii")
                    if st.session_state.cover_bild_bytes
                    else None
                )
                slides = assemble_slides(cover_frage_html, slides_2_bis_8, fazit_body, bild_b64=bild_b64)
                slug = slugify(thema)
                render_ergebnis = render_carousel(
                    slides=slides,
                    topic_slug=slug,
                    topic_title=thema,
                    theme=farbthema,
                    output_dir=f"_preview_{slug}",
                )
            st.session_state.render_ergebnis = render_ergebnis
            st.session_state.png_paths = None

if st.session_state.render_ergebnis:
    st.header("6. Vorschau")
    with open(st.session_state.render_ergebnis["preview_html"], encoding="utf-8") as f:
        html = f.read()
    st.components.v1.html(html, height=800, scrolling=True)

    st.header("7. PNGs erzeugen")
    if st.button("9 PNGs erzeugen"):
        with st.spinner("Erzeuge Screenshots der 9 Slides..."):
            st.session_state.png_paths = export_pngs(st.session_state.render_ergebnis["slide_htmls"])
        with st.spinner("Erzeuge Reel-Hintergrund (9:16)..."):
            bild_b64_reel = (
                base64.b64encode(st.session_state.cover_bild_bytes).decode("ascii")
                if st.session_state.cover_bild_bytes
                else None
            )
            st.session_state.reel_cover_path = export_reel_cover(
                bild_b64_reel, output_dir=f"_preview_{slugify(thema)}", theme=farbthema
            )

    if st.session_state.png_paths:
        st.success(f"{len(st.session_state.png_paths)} PNGs erzeugt (jeweils 1080x1350px).")

        aktuelle_caption = st.session_state.get("caption_edit", st.session_state.slides_ergebnis["caption"])
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            for png_path in st.session_state.png_paths:
                zf.write(png_path, arcname=os.path.basename(png_path))
            zf.writestr("caption.txt", aktuelle_caption)
            if st.session_state.reel_cover_path:
                zf.write(st.session_state.reel_cover_path, arcname="reel_hintergrund_9x16.png")
        st.download_button(
            "Alle 9 PNGs + Caption + Reel-Hintergrund als ZIP herunterladen",
            data=zip_buffer.getvalue(),
            file_name=f"kopfnuss_{slugify(thema)}.zip",
            mime="application/zip",
        )

        if st.session_state.reel_cover_path:
            st.image(st.session_state.reel_cover_path, caption="Reel-Hintergrund (9:16)", width=200)

        with st.expander("Direkt aufs iPhone speichern (ohne ZIP)"):
            st.caption(
                "Auf dem iPhone: Bild antippen und gedrueckt halten, dann "
                "'Zu Fotos hinzufuegen' waehlen - jedes Bild kommt in voller "
                "Aufloesung (1080x1350px) in deine Fotomediathek. Die Reihenfolge "
                "hier ist absichtlich umgekehrt (Slide 9 zuerst, Slide 1 zuletzt), "
                "damit die neueste (= zuerst in Fotos angezeigte) Aufnahme Slide 1 "
                "ist - so landen sie beim Hochladen in Instagram richtig sortiert."
            )
            nummerierte_pfade = list(enumerate(st.session_state.png_paths, start=1))
            for i, png_path in reversed(nummerierte_pfade):
                st.image(png_path, caption=f"Slide {i}/9", width="stretch")
            if st.session_state.reel_cover_path:
                st.image(
                    st.session_state.reel_cover_path,
                    caption="Reel-Hintergrund (9:16) - separat speichern, nicht Teil des Karussells",
                    width="stretch",
                )

    st.header("8. Caption")
    st.text_area(
        "Caption (zum Bearbeiten)", st.session_state.slides_ergebnis["caption"], height=200, key="caption_edit"
    )
    st.caption("Kopieren fuer Instagram:")
    copy_button_widget(st.session_state["caption_edit"], label="Caption kopieren")

    st.header("9. Video-Prompt fuer Gemini Video (ca. 10 Sekunden)")
    if st.button("Video-Prompt erzeugen"):
        with st.spinner("Claude schreibt den Gemini-Video-Prompt..."):
            st.session_state.video_prompt = generate_gemini_video_prompt(
                thema, cover_frage, st.session_state["caption_edit"], kontext=kontext
            )

    if st.session_state.video_prompt:
        st.text_area(
            "Video-Prompt (zum Bearbeiten)",
            st.session_state.video_prompt,
            height=220,
            key="video_prompt_edit",
        )
        st.caption("Kopieren fuer Gemini Video:")
        copy_button_widget(
            st.session_state.get("video_prompt_edit", st.session_state.video_prompt),
            label="Video-Prompt kopieren",
            height=270,
            box_height=200,
        )

    if not st.session_state.png_paths:
        st.caption("Erst die 9 PNGs erzeugen (Schritt 7), dann laesst sich der Post speichern.")
    if st.button("Als fertigen Post in der Historie speichern", disabled=not st.session_state.png_paths):
        r = st.session_state.recherche
        quelle = f"{r['autoren']} ({r['jahr']})" if r else None
        append_post(
            slug=slugify(thema),
            thema=thema,
            cover_frage=st.session_state.cover_frage,
            quelle=quelle,
            farbthema=farbthema,
        )

        post_dir = os.path.join(POSTS_ROOT, slugify(thema))
        os.makedirs(post_dir, exist_ok=True)
        for png_path in st.session_state.png_paths:
            shutil.copy2(png_path, os.path.join(post_dir, os.path.basename(png_path)))
        aktuelle_caption = st.session_state.get("caption_edit", st.session_state.slides_ergebnis["caption"])
        with open(os.path.join(post_dir, "caption.txt"), "w", encoding="utf-8") as f:
            f.write(aktuelle_caption)
        if st.session_state.video_prompt:
            aktueller_video_prompt = st.session_state.get("video_prompt_edit", st.session_state.video_prompt)
            with open(os.path.join(post_dir, "video_prompt.txt"), "w", encoding="utf-8") as f:
                f.write(aktueller_video_prompt)

        st.success(f"Gespeichert in post_historie.json und in {post_dir}")
