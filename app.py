# app.py — GlobeCast AI PRO (Commercial Grade)

import streamlit as st
import os, tempfile, random, gc
from gtts import gTTS
from moviepy.editor import (
    VideoFileClip, ImageClip, AudioFileClip,
    CompositeVideoClip, CompositeAudioClip,
    concatenate_videoclips, ColorClip
)
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import textwrap

# ===============================
# CONFIGURATION
# ===============================
st.set_page_config(page_title="GlobeCast AI PRO", layout="wide")
st.title("🎬 GlobeCast AI – Générateur Publicitaire PRO")

ASSETS_MUSIC = "assets/music"
ASSETS_FONT = "assets/fonts/DejaVuSans-Bold.ttf"

SUPPORTED_LANGS = {
    "Français": "fr",
    "Anglais": "en",
    "Espagnol": "es"
}

VIDEO_SIZE = (1080, 1920)  # TikTok / Reels / Shorts

# ===============================
# UTILITAIRES CRITIQUES
# ===============================

def ensure_music():
    files = [os.path.join(ASSETS_MUSIC, f) for f in os.listdir(ASSETS_MUSIC) if f.endswith(".mp3")]
    if not files:
        st.error("❌ Aucune musique trouvée dans assets/music/")
        st.stop()
    return random.choice(files)

def generate_voice(text, lang):
    path = tempfile.mktemp(suffix=".mp3")
    gTTS(text=text, lang=lang).save(path)
    return path

def loop_audio(audio, duration):
    clips = []
    t = 0
    while t < duration:
        clip = audio.subclip(0, min(audio.duration, duration - t))
        clips.append(clip)
        t += clip.duration
    return CompositeAudioClip(clips)

def animated_fallback(duration):
    return ColorClip(
        size=VIDEO_SIZE,
        color=(30, 30, 40),
        duration=duration
    )

def make_text_overlay(text, duration):
    img = Image.new("RGBA", VIDEO_SIZE, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(ASSETS_FONT, 60)

    wrapped = textwrap.fill(text, width=28)
    w, h = draw.multiline_textsize(wrapped, font=font)
    x = (VIDEO_SIZE[0] - w) // 2
    y = VIDEO_SIZE[1] - h - 120

    draw.multiline_text(
        (x, y),
        wrapped,
        font=font,
        fill="white",
        align="center",
        stroke_width=3,
        stroke_fill="black"
    )

    return ImageClip(np.array(img)).set_duration(duration)

def build_visual_track(duration):
    # 🔒 ZÉRO ÉCRAN NOIR GARANTI
    clips = []

    stock_videos = []
    if os.path.exists("cache/videos"):
        stock_videos = [
            os.path.join("cache/videos", f)
            for f in os.listdir("cache/videos")
            if f.endswith(".mp4")
        ]

    if stock_videos:
        t = 0
        while t < duration:
            path = random.choice(stock_videos)
            clip = VideoFileClip(path).resize(VIDEO_SIZE)
            clip = clip.subclip(0, min(clip.duration, duration - t))
            clips.append(clip)
            t += clip.duration
        return concatenate_videoclips(clips)

    # 🧯 Fallback ABSOLU
    return animated_fallback(duration)

# ===============================
# UI
# ===============================
subject = st.text_input("🎯 Sujet de la publicité", "Café éthique")
company = st.text_input("🏢 Marque / Entreprise", "M&G Consulting")
lang_name = st.selectbox("🌍 Langue", list(SUPPORTED_LANGS.keys()))

if st.button("🚀 Générer la vidéo publicitaire PRO"):

    try:
        with st.spinner("🎙️ Génération voix off..."):
            script = (
                f"Découvrez {subject}. "
                f"Avec {company}, choisissez la qualité, la confiance et l’innovation. "
                f"Une solution pensée pour aujourd’hui et pour demain."
            )

            voice_path = generate_voice(script, SUPPORTED_LANGS[lang_name])
            voice_clip = AudioFileClip(voice_path)
            duration = voice_clip.duration

        with st.spinner("🎵 Préparation musique..."):
            music_path = ensure_music()
            music_clip = AudioFileClip(music_path)
            music_looped = loop_audio(music_clip.volumex(0.18), duration)

        with st.spinner("🎬 Construction visuelle..."):
            visual = build_visual_track(duration)

        with st.spinner("🎨 Habillage texte..."):
            text_overlay = make_text_overlay(script, duration)

        final_audio = CompositeAudioClip([voice_clip, music_looped])
        final_video = CompositeVideoClip([visual, text_overlay]).set_audio(final_audio)

        out = tempfile.mktemp(suffix=".mp4")
        final_video.write_videofile(
            out,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            threads=2,
            verbose=False,
            logger=None
        )

        st.success("✅ Vidéo publicitaire générée avec succès")
        st.video(out)

        with open(out, "rb") as f:
            st.download_button("⬇️ Télécharger la vidéo", f, file_name="GlobeCast_AI_PRO.mp4")

    except Exception as e:
        st.error(f"❌ Erreur critique : {e}")

    finally:
        gc.collect()
