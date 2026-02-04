# app.py - GlobeCast AI version ultime
import streamlit as st
from gtts import gTTS
import os
import tempfile
import requests
from bs4 import BeautifulSoup
import gc
from moviepy.editor import (
    ImageClip,
    VideoFileClip,
    AudioFileClip,
    CompositeVideoClip,
    concatenate_videoclips,
    ColorClip,
    CompositeAudioClip
)
from PIL import Image, ImageDraw, ImageFont
import numpy as np

# -------------------------------
# Paramètres Streamlit
# -------------------------------
st.set_page_config(page_title="GlobeCast AI – Vidéo Dynamique", layout="wide")
st.title("🌍 GlobeCast AI – Vidéo Dynamique Ultime")
st.markdown("""
**Créé par : Dauphin Gelase Michelot**  
**Label : M&G Consulting**  

Améliorations :  
- Voix off boostée  
- Musique de fond en boucle  
- Texte overlay sans ImageMagick  
- Images et clips vidéos libres de droits en boucle  
- Scraping automatique de vidéos YouTube Creative Commons
""")

LANGUAGES = {
    "1. Anglais": "en",
    "2. Français": "fr",
    "3. Espagnol": "es",
    "4. Chinois Mandarin": "zh",
    "5. Hindi": "hi"
}

PEXELS_API_KEY = "YOUR_PEXELS_API_KEY"  # Remplace par ta clé Pexels
PEXELS_VIDEO_ENDPOINT = "https://api.pexels.com/videos/search"

# -------------------------------
# Fonctions utilitaires
# -------------------------------

def get_content(subject):
    """Récupère un extrait de Wikipedia"""
    try:
        query = subject.replace(' ', '_')
        url = f"https://en.wikipedia.org/wiki/{query}"
        response = requests.get(url, timeout=6)
        soup = BeautifulSoup(response.text, 'html.parser')
        div = soup.find('div', {'class': 'mw-parser-output'})
        if div:
            paragraphs = div.find_all('p', limit=5)
            return ' '.join(p.get_text().strip() for p in paragraphs)[:1000]
    except:
        pass
    return "Découvrez les avantages uniques de ce sujet."

def get_images(subject, num=3):
    """Télécharge des images libres de droits depuis Unsplash"""
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
            r = requests.get(img_url, stream=True, timeout=6)
            if r.status_code == 200:
                path = tempfile.mktemp(suffix=".jpg")
                with open(path, 'wb') as f:
                    for chunk in r.iter_content(8192):
                        f.write(chunk)
                images.append(path)
                if len(images) >= num:
                    break
    except:
        pass
    return images

def get_pexels_videos(subject, num=2):
    """Télécharge des clips vidéo depuis Pexels"""
    clips = []
    try:
        headers = {"Authorization": PEXELS_API_KEY}
        params = {"query": subject, "per_page": num}
        resp = requests.get(PEXELS_VIDEO_ENDPOINT, headers=headers, params=params, timeout=6)
        data = resp.json()
        for video in data.get("videos", []):
            video_url = video["video_files"][0]["link"]
            path = tempfile.mktemp(suffix=".mp4")
            r = requests.get(video_url, stream=True, timeout=12)
            if r.status_code == 200:
                with open(path, 'wb') as f:
                    for chunk in r.iter_content(8192):
                        f.write(chunk)
                clips.append(path)
    except:
        pass
    return clips

def get_youtube_cc_videos(subject, num=2):
    """Récupération automatique de vidéos YouTube Creative Commons (libres)"""
    # Note: nécessite package `yt_dlp` installé (`pip install yt-dlp`)
    import yt_dlp
    clips = []
    try:
        ydl_opts = {
            "format": "mp4",
            "noplaylist": True,
            "max_downloads": num,
            "quiet": True,
            "ignoreerrors": True,
            "outtmpl": tempfile.gettempdir() + "/%(id)s.%(ext)s",
            "postprocessors": [{"key": "FFmpegVideoConvertor", "preferedformat": "mp4"}],
            "match_filter": yt_dlp.utils.match_filter_func("is_cc")  # CC only
        }
        query = f"{subject} Creative Commons"
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch{num}:{query}", download=True)
            if info and "entries" in info:
                for e in info["entries"]:
                    if e and e.get("filepath") and os.path.exists(e["filepath"]):
                        clips.append(e["filepath"])
    except Exception as e:
        st.warning(f"Erreur récupération YouTube CC: {e}")
    return clips

def generate_script(subject, company, content):
    return (
        f"Attention ! {subject} change tout ! Avec {company}, profitez du meilleur. "
        f"{content[:400]}... Chez {company}, qualité, innovation et confiance."
    )

def download_background_music():
    """Télécharge musique libre et la met en boucle"""
    url = "https://files.freemusicarchive.org/storage-freemusicarchive-org/music/no_curator/Lite_Saturation/Upbeat_Corporate/Lite_Saturation_-_Medium2.mp3"
    path = tempfile.mktemp(suffix=".mp3")
    try:
        r = requests.get(url, timeout=12, stream=True)
        r.raise_for_status()
        with open(path, 'wb') as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
        return path
    except:
        return None

def boost_audio_volume(input_path):
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
    img = Image.new("RGBA", size, (0,0,0,0))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 48)
    except:
        font = ImageFont.load_default()

    margin = 60
    max_width = size[0] - margin*2
    words, lines, line = text.split(), [], ""
    for word in words:
        test = f"{line} {word}".strip()
        if draw.textlength(test, font=font) <= max_width:
            line = test
        else:
            lines.append(line)
            line = word
    lines.append(line)

    y = size[1] - (len(lines)*55) - 80
    for l in lines:
        w = draw.textlength(l, font=font)
        x = (size[0]-w)//2
        draw.text((x,y), l, fill="white", font=font, stroke_width=2, stroke_fill="black")
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

# -------------------------------
# Génération vidéo
# -------------------------------
if st.button("Générer Vidéo Dynamique"):

    progress = st.progress(0)
    status = st.empty()

    lang_code = LANGUAGES[language_name]
    voice_path = tempfile.mktemp(suffix=".mp3")
    music_path = None
    video_path = None
    media_paths = []

    try:
        status.text("Récupération contenu Wikipedia...")
        content = get_content(subject)
        progress.progress(10)

        status.text("Génération script voix off...")
        script_text = generate_script(subject, company, content)
        st.write("**Script voix off :**", script_text)
        progress.progress(20)

        status.text("Synthèse vocale (gTTS)...")
        tts = gTTS(text=script_text[:1000], lang=lang_code, slow=False)
        tts.save(voice_path)
        boost_audio_volume(voice_path)
        progress.progress(35)

        status.text("Téléchargement musique de fond...")
        music_path = download_background_music()
        progress.progress(45)

        status.text("Récupération médias libres de droits...")
        images = get_images(subject, num=3)
        pexels_videos = get_pexels_videos(subject, num=2)
        youtube_videos = get_youtube_cc_videos(subject, num=2)
        media_paths = images + pexels_videos + youtube_videos
        progress.progress(65)

        status.text("Création clips vidéo...")
        voice_clip = AudioFileClip(voice_path)
        duration = voice_clip.duration

        # Musique en boucle
        if music_path:
            music_clip = AudioFileClip(music_path)
            loops = int(duration/music_clip.duration)+1
            music_clip = concatenate_videoclips([music_clip]*loops).subclip(0,duration).volumex(0.2)
            audio_final = CompositeAudioClip([voice_clip, music_clip])
        else:
            audio_final = voice_clip

        # Dimensions
        if platform.startswith("TikTok"):
            size = (1080,1920)
        elif platform.startswith("YouTube"):
            size = (1920,1080)
        else:
            size = (1080,1080)

        # Création du fond dynamique avec répétition si nécessaire
        clips, clip_duration = [], duration / max(1,len(media_paths))
        for path in media_paths:
            if path.endswith(".mp4"):
                clip = VideoFileClip(path).set_duration(clip_duration).resize(size).crossfadein(1).crossfadeout(1)
            else:
                clip = ImageClip(path).set_duration(clip_duration).resize(size).crossfadein(1).crossfadeout(1)
            # Repetition pour couvrir toute la durée
            loops = int(duration/clip.duration)+1
            clip = concatenate_videoclips([clip]*loops).subclip(0,duration)
            clips.append(clip)

        if clips:
            base_video = concatenate_videoclips(clips, method="compose")
        else:
            base_video = ColorClip(size=size, color=(20,20,40), duration=duration)

        # Texte overlay
        txt_clip = make_text_clip(script_text[:200]+"...", size, duration)
        txt_clip = txt_clip.set_position(('center','bottom'))

        # Montage final
        final_video = CompositeVideoClip([base_video, txt_clip]).set_audio(audio_final)
        video_path = tempfile.mktemp(suffix=".mp4")
        final_video.write_videofile(video_path, fps=24, codec="libx264", audio_codec="aac", preset='medium', threads=2, verbose=False, logger=None)

        st.success("🎬 Vidéo dynamique générée !")
        st.video(video_path)
        with open(video_path,"rb") as f:
            st.download_button("Télécharger la vidéo MP4", f, file_name=f"Dynamic_{company.replace(' ','_')}_{subject.replace(' ','_')}.mp4")

        progress.progress(100)
        status.text("Terminé !")

    except Exception as e:
        st.error(f"Erreur lors de la génération vidéo : {str(e)}")

    finally:
        paths = [voice_path, music_path, video_path] + media_paths
        for p in paths:
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except:
                    pass
        gc.collect()


