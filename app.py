import streamlit as st
from gtts import gTTS
import os
from moviepy.config import change_settings
# Force MoviePy to use the correct ImageMagick binary name on modern systems
change_settings({"IMAGEMAGICK_BINARY": "/usr/bin/magick"})
from moviepy.editor import (
    ImageClip,
    AudioFileClip,
    TextClip,
    CompositeVideoClip,
    concatenate_videoclips,
    ColorClip,
    CompositeAudioClip
)
import os
import tempfile
import requests
from bs4 import BeautifulSoup
from pydub import AudioSegment
import gc

# Supported languages
LANGUAGES = {
    "1. Anglais": "en",
    "2. Chinois Mandarin": "zh",
    "3. Hindi": "hi",
    "4. Espagnol": "es",
    "5. Français": "fr",
    "6. Arabe": "ar",
    "7. Bengali": "bn",
    "8. Russe": "ru",
    "9. Portugais": "pt",
    "10. Ourdou": "ur"
}

def get_content(subject):
    content = ""
    try:
        query = subject.replace(' ', '_')
        url = f"https://en.wikipedia.org/wiki/{query}"
        response = requests.get(url, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        div = soup.find('div', {'class': 'mw-parser-output'})
        if div:
            paragraphs = div.find_all('p', limit=5)
            content = ' '.join(p.get_text().strip() for p in paragraphs)[:1000]
    except Exception as e:
        st.warning(f"Erreur Wikipedia : {e}")
    return content or "Découvrez les avantages uniques de ce sujet."

def get_images(subject, num=3):
    images = []
    try:
        query = subject.replace(' ', '%20')
        url = f"https://unsplash.com/s/photos/{query}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        img_tags = soup.find_all('img', {'srcset': True}, limit=num*2)
        for img in img_tags:
            if 'srcset' in img.attrs:
                srcset = img['srcset'].split(',')
                url = srcset[-1].strip().split(' ')[0]  # Plus haute résolution
                resp = requests.get(url, timeout=5, stream=True)
                if resp.status_code == 200:
                    path = tempfile.mktemp(suffix=".jpg")
                    with open(path, 'wb') as f:
                        for chunk in resp.iter_content(8192):
                            f.write(chunk)
                    images.append(path)
                    if len(images) >= num:
                        break
    except Exception as e:
        st.warning(f"Erreur images Unsplash : {e}")
    return images

def generate_script(subject, company, content):
    script = (
        f"Attention ! {subject} change tout ! Avec {company}, profitez du meilleur. "
        f"{content[:400]}... "
        f"Chez {company}, qualité, innovation et confiance. "
        f"Rejoignez-nous dès aujourd'hui : abonnez-vous, contactez-nous !"
    )
    return script

def download_music():
    # Musique libre de droits (exemple FMA - Upbeat Corporate - CC BY-ND)
    url = "https://files.freemusicarchive.org/storage-freemusicarchive-org/music/no_curator/Lite_Saturation/Upbeat_Corporate/Lite_Saturation_-_Medium2.mp3"
    path = tempfile.mktemp(suffix=".mp3")
    try:
        resp = requests.get(url, timeout=10, stream=True)
        resp.raise_for_status()
        with open(path, 'wb') as f:
            for chunk in resp.iter_content(8192):
                f.write(chunk)
        return path
    except:
        return None

def normalize_audio(audio_path):
    """Améliore la qualité audio avec pydub : normalisation + léger boost"""
    try:
        sound = AudioSegment.from_mp3(audio_path)
        # Normalisation + compression dynamique
        normalized = sound.normalize()
        # Boost subtil si trop bas
        if normalized.dBFS < -20:
            normalized = normalized + 6  # +6 dB max
        normalized.export(audio_path, format="mp3")
    except Exception as e:
        st.warning(f"Normalisation audio échouée : {e}")

st.set_page_config(page_title="GlobeCast AI – Qualité Pro", layout="wide")

st.title("🌍 GlobeCast AI – Version Qualité Pro (Voix + Transitions + Musique)")
st.markdown("""
**Créé par : Dauphin Gelase Michelot**  
**Label :** M&G Consulting  
**GitHub :** [gelasemi](https://github.com/gelasemi)  
**Améliorations :**  
- Voix off normalisée (plus claire et puissante)  
- Transitions fluides entre images (crossfade)  
- Musique de fond libre de droits (volume équilibré)  
- Robustesse totale aux erreurs de scraping
""")

subject = st.text_input("Sujet", value="Café éthique")
company = st.text_input("Entreprise", value="M&G Consulting")
language_name = st.selectbox("Langue", list(LANGUAGES.keys()))
platform = st.selectbox("Plateforme", [
    "TikTok – Vertical 9:16",
    "YouTube – Horizontal 16:9",
    "Facebook – Carré 1:1"
])

if st.button("Générer Vidéo Pro (Qualité Audio + Transitions)", type="primary"):
    progress = st.progress(0)
    status = st.empty()

    lang_code = LANGUAGES[language_name]

    status.text("Contenu...")
    content = get_content(subject)
    progress.progress(15)

    status.text("Script...")
    script_text = generate_script(subject, company, content)
    st.write("**Script voix off :**", script_text)
    progress.progress(25)

    status.text("Voix off (qualité améliorée)...")
    try:
        tts = gTTS(text=script_text[:1000], lang=lang_code, slow=False)
        voice_path = tempfile.mktemp(suffix=".mp3")
        tts.save(voice_path)
        normalize_audio(voice_path)  # ← Amélioration qualité
    except Exception as e:
        st.error(f"TTS erreur : {e}")
        st.stop()
    progress.progress(40)

    status.text("Musique de fond...")
    music_path = download_music()
    progress.progress(50)

    status.text("Images en ligne...")
    images = get_images(subject, num=3)
    progress.progress(60)

    status.text("Vidéo avec transitions fluides...")
    try:
        voice_clip = AudioFileClip(voice_path)
        duration = min(voice_clip.duration, 60)

        if music_path:
            music_clip = AudioFileClip(music_path).subclip(0, duration).volumex(0.25)  # Volume fond bas
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
            clip_duration = duration / len(images)
            img_clips = []
            for img in images:
                clip = (ImageClip(img)
                        .set_duration(clip_duration + 1)  # +1s pour transition
                        .crossfadein(1.0)
                        .crossfadeout(1.0))
                img_clips.append(clip)
            video = concatenate_videoclips(img_clips, method="compose", padding=-1).resize(size)
        else:
            video = ColorClip(size=size, color=(0,0,0), duration=duration)

        txt_clip = TextClip(
    script_text[:150] + "...",
    fontsize=45,
    color='white',
    stroke_color='black',
    stroke_width=2,
    font='DejaVu-Sans',          # almost always available
    method='label',              # ← very important: avoids most ImageMagick calls
    size=(size[0]-120, None),
    align='center'
).set_position(('center', 'bottom')).set_duration(duration)

        final = CompositeVideoClip([video, txt_clip]).set_audio(audio_final)

        video_path = tempfile.mktemp(suffix=".mp4")
        final.write_videofile(
            video_path,
            fps=24,                # 24 fps pour fluidité acceptable
            codec="libx264",
            audio_codec="aac",
            preset='medium',       # Meilleur équilibre qualité/vitesse
            threads=2,
            verbose=False,
            logger=None
        )

        st.success("Vidéo PRO générée : voix claire + transitions fluides + musique fond !")
        st.video(video_path)

        with open(video_path, "rb") as f:
            st.download_button("Télécharger Vidéo MP4", f, file_name=f"Pro_{company}_{subject}.mp4")

        # Cleanup
        os.remove(voice_path)
        if music_path and os.path.exists(music_path):
            os.remove(music_path)
        os.remove(video_path)
        for img in images:
            if os.path.exists(img):
                os.remove(img)
        gc.collect()

        progress.progress(100)
        status.text("Terminé !")

    except Exception as e:
        st.error(f"Erreur finale : {str(e)}")
        if os.path.exists(voice_path):
            os.remove(voice_path)
        if music_path and os.path.exists(music_path):
            os.remove(music_path)
        gc.collect()



