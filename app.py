# app.py - GlobeCast AI version finale
import streamlit as st
from gtts import gTTS
import os
import tempfile
import requests
from bs4 import BeautifulSoup
import gc
from moviepy.editor import (
    ImageClip,
    AudioFileClip,
    CompositeVideoClip,
    concatenate_videoclips,
    ColorClip,
    CompositeAudioClip
)
from PIL import Image, ImageDraw, ImageFont
import numpy as np

# -------------------------------
# Paramètres
# -------------------------------
st.set_page_config(page_title="GlobeCast AI – Qualité Pro", layout="wide")
st.title("🌍 GlobeCast AI – Version Qualité Pro")
st.markdown("""
**Créé par : Dauphin Gelase Michelot**  
**Label : M&G Consulting**  

Améliorations :  
- Voix off boostée (volume corrigé via ffmpeg)  
- Transitions crossfade entre images  
- Musique de fond  
- Texte overlay sans ImageMagick
""")

LANGUAGES = {
    "1. Anglais": "en",
    "2. Français": "fr",
    "3. Espagnol": "es",
    "4. Chinois Mandarin": "zh",
    "5. Hindi": "hi"
}

# -------------------------------
# Fonctions utilitaires
# -------------------------------

def get_content(subject):
    """Récupère un extrait de Wikipedia (en anglais)"""
    content = ""
    try:
        query = subject.replace(' ', '_')
        url = f"https://en.wikipedia.org/wiki/{query}"
        response = requests.get(url, timeout=6)
        soup = BeautifulSoup(response.text, 'html.parser')
        div = soup.find('div', {'class': 'mw-parser-output'})
        if div:
            paragraphs = div.find_all('p', limit=5)
            content = ' '.join(p.get_text().strip() for p in paragraphs)[:1000]
    except Exception:
        content = ""
    return content or "Découvrez les avantages uniques de ce sujet."

def get_images(subject, num=3):
    """Récupère des images depuis Unsplash"""
    images = []
    try:
        query = subject.replace(' ', '%20')
        url = f"https://unsplash.com/s/photos/{query}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=6)
        soup = BeautifulSoup(response.text, 'html.parser')
        img_tags = soup.find_all('img', {'srcset': True}, limit=num*3)
        
        for img in img_tags:
            srcset = img['srcset'].split(',')
            img_url = srcset[-1].strip().split(' ')[0]
            resp = requests.get(img_url, timeout=6, stream=True)
            if resp.status_code == 200:
                path = tempfile.mktemp(suffix=".jpg")
                with open(path, 'wb') as f:
                    for chunk in resp.iter_content(8192):
                        f.write(chunk)
                images.append(path)
                if len(images) >= num:
                    break
    except:
        pass
    return images

def generate_script(subject, company, content):
    """Génère un script publicitaire court"""
    return (
        f"Attention ! {subject} change tout ! Avec {company}, profitez du meilleur. "
        f"{content[:400]}... Chez {company}, qualité, innovation et confiance."
    )

def download_background_music():
    """Télécharge une musique libre de droits"""
    url = "https://files.freemusicarchive.org/storage-freemusicarchive-org/music/no_curator/Lite_Saturation/Upbeat_Corporate/Lite_Saturation_-_Medium2.mp3"
    path = tempfile.mktemp(suffix=".mp3")
    try:
        resp = requests.get(url, timeout=12, stream=True)
        resp.raise_for_status()
        with open(path, 'wb') as f:
            for chunk in resp.iter_content(8192):
                f.write(chunk)
        return path
    except:
        return None

def boost_audio_volume(input_path):
    """Augmente le volume avec ffmpeg"""
    try:
        boosted_path = tempfile.mktemp(suffix=".mp3")
        os.system(
            f'ffmpeg -y -i "{input_path}" -filter:a "volume=6dB" '
            f'-acodec libmp3lame "{boosted_path}" > NUL 2>&1'
        )
        if os.path.exists(boosted_path) and os.path.getsize(boosted_path) > 10000:
            os.replace(boosted_path, input_path)
        else:
            if os.path.exists(boosted_path):
                os.remove(boosted_path)
    except:
        pass

def make_text_clip(text, size, duration):
    """Crée un clip texte avec PIL (sans ImageMagick)"""
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 48)
    except:
        font = ImageFont.load_default()

    margin = 60
    max_width = size[0] - margin * 2
    words = text.split()
    lines, line = [], ""

    for word in words:
        test = f"{line} {word}".strip()
        if draw.textlength(test, font=font) <= max_width:
            line = test
        else:
            lines.append(line)
            line = word
    lines.append(line)

    y = size[1] - (len(lines) * 55) - 80
    for l in lines:
        w = draw.textlength(l, font=font)
        x = (size[0] - w) // 2
        draw.text((x, y), l, fill="white", font=font, stroke_width=2, stroke_fill="black")
        y += 55

    return ImageClip(np.array(img)).set_duration(duration)

# -------------------------------
# Inputs utilisateur
# -------------------------------
subject = st.text_input("Sujet", value="Café éthique")
company = st.text_input("Entreprise", value="M&G Consulting")
language_name = st.selectbox("Langue", list(LANGUAGES.keys()))
platform = st.selectbox("Plateforme", [
    "TikTok – Vertical 9:16",
    "YouTube – Horizontal 16:9",
    "Facebook – Carré 1:1"
])

if st.button("Générer Vidéo Pro"):

    progress = st.progress(0)
    status = st.empty()

    lang_code = LANGUAGES[language_name]
    voice_path = tempfile.mktemp(suffix=".mp3")
    music_path = None
    video_path = None
    images = []

    try:
        status.text("Récupération contenu Wikipedia...")
        content = get_content(subject)
        progress.progress(15)

        status.text("Génération script voix off...")
        script_text = generate_script(subject, company, content)
        st.write("**Script voix off :**", script_text)
        progress.progress(25)

        status.text("Synthèse vocale (gTTS)...")
        tts = gTTS(text=script_text[:1000], lang=lang_code, slow=False)
        tts.save(voice_path)
        boost_audio_volume(voice_path)
        progress.progress(40)

        status.text("Téléchargement musique de fond...")
        music_path = download_background_music()
        progress.progress(50)

        status.text("Téléchargement images Unsplash...")
        images = get_images(subject, num=3)
        progress.progress(60)

        status.text("Création vidéo...")
        voice_clip = AudioFileClip(voice_path)
        duration = min(voice_clip.duration, 60)

        if music_path:
            music_clip = AudioFileClip(music_path).subclip(0, duration).volumex(0.20)
            audio_final = CompositeAudioClip([voice_clip, music_clip])
        else:
            audio_final = voice_clip

        if platform.startswith("TikTok"):
            size = (1080, 1920)
        elif platform.startswith("YouTube"):
            size = (1920, 1080)
        else:
            size = (1080, 1080)

        if images:
            clip_duration = duration / max(1, len(images))
            img_clips = []
            for img_path in images:
                clip = (ImageClip(img_path)
                        .set_duration(clip_duration + 1.2)
                        .crossfadein(1.0)
                        .crossfadeout(1.0))
                img_clips.append(clip)
            base_video = concatenate_videoclips(img_clips, method="compose").resize(size)
        else:
            base_video = ColorClip(size=size, color=(20,20,40), duration=duration)

        txt_clip = make_text_clip(script_text[:180]+"...", size, duration)
        txt_clip = txt_clip.set_position(('center', 'bottom'))

        final_video = CompositeVideoClip([base_video, txt_clip]).set_audio(audio_final)
        video_path = tempfile.mktemp(suffix=".mp4")

        final_video.write_videofile(
            video_path,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            preset='medium',
            threads=2,
            verbose=False,
            logger=None
        )

        st.success("Vidéo générée !")
        st.video(video_path)

        with open(video_path, "rb") as f:
            st.download_button(
                "Télécharger la vidéo MP4",
                f,
                file_name=f"Pro_{company.replace(' ','_')}_{subject.replace(' ','_')}.mp4"
            )

        progress.progress(100)
        status.text("Terminé !")

    except Exception as e:
        st.error(f"Erreur lors de la génération vidéo : {str(e)}")

    finally:
        paths = [voice_path, music_path, video_path] + images
        for path in paths:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except:
                    pass
        gc.collect()
