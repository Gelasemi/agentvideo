import streamlit as st
from gtts import gTTS
import os
import tempfile
import requests
from bs4 import BeautifulSoup
import gc
import shutil
from moviepy.config import change_settings
from moviepy.editor import (
    ImageClip,
    AudioFileClip,
    TextClip,
    CompositeVideoClip,
    concatenate_videoclips,
    ColorClip,
    CompositeAudioClip
)

# Configuration MoviePy / ImageMagick – chemin automatique
magick_bin = shutil.which("convert") or shutil.which("magick") or "convert"
change_settings({"IMAGEMAGICK_BINARY": magick_bin})

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
    """Récupère un extrait de Wikipedia"""
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
            if 'srcset' in img.attrs:
                srcset = img['srcset'].split(',')
                url = srcset[-1].strip().split(' ')[0]
                try:
                    resp = requests.get(url, timeout=6, stream=True)
                    if resp.status_code == 200:
                        path = tempfile.mktemp(suffix=".jpg")
                        with open(path, 'wb') as f:
                            for chunk in resp.iter_content(8192):
                                f.write(chunk)
                        images.append(path)
                        if len(images) >= num:
                            break
                except:
                    continue
    except Exception as e:
        st.warning(f"Erreur images Unsplash : {e}")
    return images

def generate_script(subject, company, content):
    """Génère un script publicitaire court"""
    return (
        f"Attention ! {subject} change tout ! Avec {company}, profitez du meilleur. "
        f"{content[:400]}... "
        f"Chez {company}, qualité, innovation et confiance. "
        f"Rejoignez-nous dès aujourd'hui : abonnez-vous, contactez-nous !"
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
            f'-acodec libmp3lame "{boosted_path}" > /dev/null 2>&1'
        )
        if os.path.exists(boosted_path) and os.path.getsize(boosted_path) > 10000:
            os.replace(boosted_path, input_path)
        else:
            if os.path.exists(boosted_path):
                os.remove(boosted_path)
    except:
        pass  # silencieux en cas d'échec

st.set_page_config(page_title="GlobeCast AI – Qualité Pro", layout="wide")

st.title("🌍 GlobeCast AI – Version Qualité Pro")
st.markdown("""
**Créé par : Dauphin Gelase Michelot**  
**Label :** M&G Consulting  
**GitHub :** [gelasemi/agentvideo](https://github.com/gelasemi/agentvideo)  

**Améliorations :**  
- Voix off boostée (volume corrigé via ffmpeg)  
- Transitions crossfade entre images  
- Musique de fond à volume réduit  
- Texte affiché sans dépendance lourde à ImageMagick
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

    # Déclarer toutes les variables temporaires dès le début
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
        boost_audio_volume(voice_path)  # boost volume
        progress.progress(40)

        status.text("Ajout musique de fond...")
        music_path = download_background_music()
        progress.progress(50)

        status.text("Téléchargement images Unsplash...")
        images = get_images(subject, num=3)
        progress.progress(60)

        status.text("Assemblage vidéo avec transitions...")
        voice_clip = AudioFileClip(voice_path)
        duration = min(voice_clip.duration, 60)

        if music_path:
            music_clip = AudioFileClip(music_path).subclip(0, duration).volumex(0.20)
            audio_final = CompositeAudioClip([voice_clip, music_clip])
        else:
            audio_final = voice_clip

        # Format selon plateforme
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

        # Texte overlay sans dépendance lourde à ImageMagick
        txt_clip = TextClip(
            script_text[:150] + "...",
            fontsize=50,
            color='white',
            stroke_color='black',
            stroke_width=2,
            font='DejaVu-Sans',
            method='label',              # ← Solution clé pour éviter les erreurs policy
            align='center',
            size=(size[0]-140, None)
        ).set_position(('center', 'bottom')).set_duration(duration)

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

        st.success("Vidéo professionnelle générée ! Voix boostée + transitions + musique")
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
        # Nettoyage sécurisé
        paths = [voice_path, music_path, video_path] + images
        for path in paths:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except:
                    pass
        gc.collect()
