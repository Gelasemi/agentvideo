import streamlit as st
from gtts import gTTS
import os
import tempfile
import requests
from bs4 import BeautifulSoup
import gc
import shutil  # Pour trouver le bon binaire ImageMagick
from moviepy.config import change_settings
from moviepy.editor import (
    ImageClip, AudioFileClip, TextClip, CompositeVideoClip,
    concatenate_videoclips, ColorClip, CompositeAudioClip
)

# Configuration MoviePy / ImageMagick – chemin automatique et robuste
magick_bin = shutil.which("convert") or shutil.which("magick") or "convert"
change_settings({"IMAGEMAGICK_BINARY": magick_bin})
# Alternative si toujours problème : forcer "convert"
# change_settings({"IMAGEMAGICK_BINARY": "convert"})

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
        response = requests.get(url, timeout=6)
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
        response = requests.get(url, headers=headers, timeout=6)
        soup = BeautifulSoup(response.text, 'html.parser')
        img_tags = soup.find_all('img', {'srcset': True}, limit=num*2)
        for img in img_tags:
            if 'srcset' in img.attrs:
                srcset = img['srcset'].split(',')
                url = srcset[-1].strip().split(' ')[0]
                resp = requests.get(url, timeout=6, stream=True)
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
    """Boost volume simple avec ffmpeg (alternative pydub)"""
    try:
        boosted_path = tempfile.mktemp(suffix=".mp3")
        os.system(
            f'ffmpeg -y -i "{audio_path}" -filter:a "volume=6dB" '
            f'-acodec libmp3lame "{boosted_path}" > /dev/null 2>&1'
        )
        if os.path.exists(boosted_path) and os.path.getsize(boosted_path) > 10000:
            os.replace(boosted_path, audio_path)
        else:
            os.remove(boosted_path)
    except Exception as e:
        st.warning(f"Boost audio échoué : {e}")

st.set_page_config(page_title="GlobeCast AI – Qualité Pro", layout="wide")
st.title("🌍 GlobeCast AI – Version Qualité Pro (Voix + Transitions + Musique)")
st.markdown("""
**Créé par : Dauphin Gelase Michelot**  
**Label :** M&G Consulting  
**GitHub :** [gelasemi](https://github.com/gelasemi)

**Améliorations :** Voix boostée, transitions fluides, musique fond, robustesse erreurs
""")

subject = st.text_input("Sujet", value="Café éthique")
company = st.text_input("Entreprise", value="M&G Consulting")
language_name = st.selectbox("Langue", list(LANGUAGES.keys()))
platform = st.selectbox("Plateforme", [
    "TikTok – Vertical 9:16",
    "YouTube – Horizontal 16:9",
    "Facebook – Carré 1:1"
])

if st.button("Générer Vidéo Pro", type="primary"):
    progress = st.progress(0)
    status = st.empty()

    lang_code = LANGUAGES[language_name]

    # Variables temporaires déclarées tôt pour éviter NameError
    voice_path = tempfile.mktemp(suffix=".mp3")
    boosted_voice = None
    music_path = None
    video_path = None
    images = []

    try:
        status.text("Contenu Wikipedia...")
        content = get_content(subject)
        progress.progress(15)

        status.text("Script...")
        script_text = generate_script(subject, company, content)
        st.write("**Script voix off :**", script_text)
        progress.progress(25)

        status.text("Voix off...")
        tts = gTTS(text=script_text[:1000], lang=lang_code, slow=False)
        tts.save(voice_path)
        normalize_audio(voice_path)  # boost volume
        progress.progress(40)

        status.text("Musique de fond...")
        music_path = download_music()
        progress.progress(50)

        status.text("Images...")
        images = get_images(subject, num=3)
        progress.progress(60)

        status.text("Assemblage vidéo...")
        voice_clip = AudioFileClip(voice_path)
        duration = min(voice_clip.duration, 60)

        if music_path:
            music_clip = AudioFileClip(music_path).subclip(0, duration).volumex(0.25)
            audio_final = CompositeAudioClip([voice_clip, music_clip])
        else:
            audio_final = voice_clip

        # Taille selon plateforme
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
                        .set_duration(clip_duration + 1)
                        .crossfadein(1.0)
                        .crossfadeout(1.0))
                img_clips.append(clip)
            video = concatenate_videoclips(img_clips, method="compose").resize(size)
        else:
            video = ColorClip(size=size, color=(0,0,0), duration=duration)

        txt_clip = TextClip(
            script_text[:150] + "...",
            fontsize=45,
            color='white',
            stroke_color='black',
            stroke_width=1.5,
            font='Arial-Bold',
            method='label',  # ← Évite la plupart des problèmes ImageMagick
            align='center',
            size=(size[0]-120, None)
        ).set_position(('center', 'bottom')).set_duration(duration)

        final = CompositeVideoClip([video, txt_clip]).set_audio(audio_final)

        video_path = tempfile.mktemp(suffix=".mp4")
        final.write_videofile(
            video_path,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            preset='medium',
            threads=2,
            verbose=False,
            logger=None
        )

        st.success("Vidéo générée avec succès !")
        st.video(video_path)

        with open(video_path, "rb") as f:
            st.download_button("Télécharger Vidéo MP4", f, file_name=f"Pro_{company}_{subject}.mp4")

        progress.progress(100)
        status.text("Terminé !")

    except Exception as e:
        st.error(f"Erreur lors de la génération : {str(e)}")

    finally:
        # Nettoyage sécurisé
        paths = [voice_path, boosted_voice, music_path, video_path] + images
        for path in paths:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except:
                    pass
        gc.collect()
