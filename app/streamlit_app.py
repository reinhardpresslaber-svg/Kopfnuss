"""
Kopfnuss - einfache Streamlit-Oberflaeche (V1, erster Entwurf)
=================================================================
Verbindet die bereits fertigen Module zu einem klickbaren Ablauf:
Thema eingeben -> Cover-Frage waehlen -> Slides & Caption generieren
-> Vorschau ansehen.

Noch NICHT eingebaut: automatische Recherche-Anbindung, Bild-Modul,
PNG-Export (wkhtmltoimage fehlt noch) - kommt in spaeteren Schritten.
"""

import re

import streamlit as st

from post_historie import check_topic, append_post
from text_module import generate_cover_optionen, generate_slides_und_caption, assemble_slides
from render_module import render_carousel

st.set_page_config(page_title="Kopfnuss Post-Generator", page_icon="🥜", layout="centered")
st.title("🥜 Kopfnuss Post-Generator")


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


for key, default in [
    ("cover_optionen", None),
    ("cover_frage", ""),
    ("slides_ergebnis", None),
    ("render_ergebnis", None),
]:
    if key not in st.session_state:
        st.session_state[key] = default

st.header("1. Thema")
thema = st.text_input("Worum soll der Post gehen?", key="thema_input")
farbthema = st.radio("Farbthema", ["klassisch", "gruen"], horizontal=True)

if thema:
    treffer = check_topic(thema)
    if treffer:
        st.warning("Aehnliche Themen gibt es schon:")
        for t in treffer:
            st.write(f"- {t['thema']} ({t['cover_frage']})")

if st.button("Cover-Vorschlaege generieren", disabled=not thema):
    with st.spinner("Claude ueberlegt sich 3 Formulierungen..."):
        st.session_state.cover_optionen = generate_cover_optionen(thema)
    st.session_state.slides_ergebnis = None
    st.session_state.render_ergebnis = None

if st.session_state.cover_optionen:
    st.header("2. Cover-Frage auswaehlen")
    auswahl = st.radio(
        "Welche Formulierung gefaellt dir am besten?",
        st.session_state.cover_optionen,
        key="cover_auswahl",
    )
    cover_frage = st.text_input("Cover-Frage (kannst du hier noch anpassen):", value=auswahl)

    if st.button("Slides & Caption generieren"):
        with st.spinner("Claude schreibt die Slides 2-8, das Fazit und die Caption..."):
            ergebnis = generate_slides_und_caption(thema, cover_frage)
            slides = assemble_slides(cover_frage, ergebnis["slides_2_bis_8"], ergebnis["fazit_body"])
            slug = slugify(thema)
            render_ergebnis = render_carousel(
                slides=slides,
                topic_slug=slug,
                topic_title=thema,
                theme=farbthema,
                output_dir=f"_preview_{slug}",
            )
        st.session_state.cover_frage = cover_frage
        st.session_state.slides_ergebnis = ergebnis
        st.session_state.render_ergebnis = render_ergebnis

if st.session_state.render_ergebnis:
    st.header("3. Vorschau")
    with open(st.session_state.render_ergebnis["preview_html"], encoding="utf-8") as f:
        html = f.read()
    st.components.v1.html(html, height=800, scrolling=True)

    st.header("4. Caption")
    st.text_area("Caption (zum Kopieren)", st.session_state.slides_ergebnis["caption"], height=200)

    if st.button("Als fertigen Post in der Historie speichern"):
        append_post(
            slug=slugify(thema),
            thema=thema,
            cover_frage=st.session_state.cover_frage,
            farbthema=farbthema,
        )
        st.success("Gespeichert in post_historie.json")
