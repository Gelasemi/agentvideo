import streamlit as st
from gtts import gTTS
from moviepy.editor import ImageClip, AudioFileClip, TextClip, CompositeVideoClip, concatenate_videoclips
import os
import tempfile
import requests
from bs4 import BeautifulSoup
import threading  # For potential async scraping if needed
import gc  # For garbage collection to free memory

# Supported languages (top 10 most spoken – gTTS codes)
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
    """Scrape content from Wikipedia for documentary/advertising info. Optimized with timeout and limited parse."""
    query = subject.replace(' ', '_')
    url = f"https://en.wikipedia.org/wiki/{query}"
    try:
        response = requests.get(url, timeout=5)  # Reduced timeout for speed
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        content_div = soup.find('div', {'class': 'mw-parser-output'})
        if content_div:
            paragraphs = content_div.find_all('p', limit=5)  # Limit to first 5 paragraphs for speed
            content = ' '.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])[:1000]  # Reduced limit
        else:
            content = "Aucune information trouvée sur Wikipedia. Utilisez des faits généraux."
    except Exception as e:
        content = f"Erreur lors du scraping : {str(e)}. Utilisez des faits généraux."
    return content

def get_images(subject, num=3):  # Reduced max images to 3 for faster processing
    """Scrape images from Unsplash matching the subject. Optimized with fewer requests."""
    query = subject.replace(' ', '%20')
    url = f"https://unsplash.com/s/photos/{query}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    images = []
    try:
        response = requests.get(url, headers=headers, timeout=5)  # Reduced timeout
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        img_tags = soup.find_all('img', {'srcset': True}, limit=num+2)  # Limit tags parsed
        image_urls = [img['src'] for img in img_tags if 'src' in img.attrs and 'unsplash.com/photos' in img['src']]
        unique_urls = list(dict.fromkeys(image_urls))[:num]
        for u in unique_urls:
            resp = requests.get(u, timeout=5, stream=True)  # Stream for memory efficiency
            if resp.status_code == 200:
                path = tempfile.mktemp(suffix=".jpg")
                with open(path, 'wb') as f:
                    for chunk in resp.iter_content(chunk_size=8192):  # Chunked write for low memory
                        f.write(chunk)
                images.append(path)
    except Exception as e:
        st.warning(f"Erreur lors de la récupération des images : {str(e)}. Utilisation d'avatar par défaut.")
    return images

def generate_script(subject, company, content, lang_code):
    """Generate a 1-minute advertising/documentary script using scraped content (AIDA structure)."""
    # Aim for ~120-150 words for 1 min, reduced computation
    script = (
        f"Attention ! Découvrez {subject} avec {company}. "
        f"{content[:400]}... "  # Shorter include for faster string ops
        f"Intéressant ? {company} offre les meilleurs avantages. "
        f"Désir : Choisissez {company} pour {subject}. "
        f"Action : Abonnez-vous maintenant !"
    )
    if len(script) < 600:
        script += f" Plus d'infos : {content[400:600]}."
    return script

st.set_page_config(page_title="GlobeCast AI Amélioré", layout="wide")
st.title("🌍 GlobeCast AI – Agent Vidéo Puissant (Version Optimisée CPU)")
st.markdown("""
**Créé par : Dauphin Gelase Michelot**  
**Label :** M&G Consulting  
**GitHub :** [gelasemi](https://github.com/gelasemi)  
**Niveau :** Starter Amélioré  
**Date :** Février 2026  
**Améliorations :** Scraping optimisé, moins d'images, vidéo allégée pour CPU/laptop rapide (FPS bas, résol. réduite, cleanup mémoire).
""")

st.info("Version CPU-optimisée – Exécution plus rapide sur laptop/CPU : scraping limité, vidéo légère (~30s max), garbage collection.")

# User inputs
subject = st.text_input("Sujet de la vidéo (documentaire ou pub)", placeholder="Exemple : Café éthique à Madagascar", value="Café éthique")
company = st.text_input("Nom de l'entreprise pour la pub", placeholder="Exemple : M&G Consulting", value="M&G Consulting")
language_name = st.selectbox("Langue de la vidéo", list(LANGUAGES.keys()))
platform = st.selectbox("Format / Plateforme cible", [
    "TikTok – Vertical 9:16 (1080×1920)",
    "YouTube – Horizontal 16:9 (1920×1080)",
    "Facebook/Instagram – Carré 1:1 (1080×1080)"
])

if st.button("🎥 Générer Vidéo Publicitaire Auto (1 min)", type="primary"):
    if not subject.strip() or not company.strip():
        st.error("Veuillez entrer un sujet et un nom d'entreprise valides.")
    else:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.text("Scraping contenu...")
        content = get_content(subject)
        st.subheader("Contenu scraped (aperçu)")
        st.write(content[:300] + "...")
        progress_bar.progress(0.2)
        
        status_text.text("Génération script...")
        script_text = generate_script(subject, company, content, language_name)  # Fix: lang_code not used in generate_script
        st.subheader("Script généré (~1 min)")
        st.write(script_text)
        progress_bar.progress(0.4)
        
        lang_code = LANGUAGES[language_name]
        
        status_text.text("Synthèse vocale...")
        try:
            tts = gTTS(text=script_text[:1000], lang=lang_code, slow=False) # Limit text for faster TTS
            audio_path = tempfile.mktemp(suffix=".mp3")
            tts.save(audio_path)
        except Exception as e:
            st.error(f"Erreur TTS : {e}")
            st.stop()
        progress_bar.progress(0.5)
        
        status_text.text("Récupération images...")
        images = get_images(subject, num=3) # Reduced to 3
        if not images:
            st.warning("Aucune image. Avatar par défaut.")
            avatar_filename = f"avatar_{lang_code}.png"
            avatar_path = os.path.join("avatars", avatar_filename)
            if os.path.exists(avatar_path):
                images = [avatar_path] * 3 # Reuse for speed
            else:
                st.error("Avatar manquant !")
                os.remove(audio_path)
                st.stop()
        progress_bar.progress(0.6)
        
        status_text.text("Création vidéo optimisée...")
        try:
            audio_clip = AudioFileClip(audio_path)
            duration = min(audio_clip.duration, 60) # Cap to 60s max for speed
            clip_duration = duration / max(1, len(images))
           
            # Optimized clips: no crossfade if many, low FPS
            img_clips = []
            for img in images:
                clip = ImageClip(img).set_duration(clip_duration) # No fade for speed
                img_clips.append(clip)
           
            video = concatenate_videoclips(img_clips, method="compose")
           
            # Lower res for processing, then resize
            if platform.startswith("TikTok"):
                size = (1080, 1920)
            elif platform.startswith("YouTube"):
                size = (1920, 1080)
            else:
                size = (1080, 1080)
            process_size = (size[0] // 2, size[1] // 2) # Half res temp
            video = video.resize(process_size)
            video = video.resize(size)
           
            subtitle = script_text[:150] + "..." # Shorter subtitle
            txt_clip = TextClip(
                subtitle,
                fontsize=40, # Smaller font for faster render
                color='white',
                stroke_color='black',
                stroke_width=1,
                font='Arial',
                method='label', # Faster method
                align='center'
            ).set_position(('center', 'bottom')).set_duration(duration)
           
            final_video = CompositeVideoClip([video, txt_clip]).set_audio(audio_clip)
           
            video_path = tempfile.mktemp(suffix=".mp4")
            final_video.write_videofile(
                video_path,
                fps=15, # Lower FPS for faster export
                codec="libx264",
                audio_codec="aac",
                preset='ultrafast', # Fastest preset
                threads=2, # Limited threads for laptop CPU
                verbose=False,
                logger=None
            )
           
            st.success("Vidéo générée rapidement ! (~1 min, optimisée CPU)")
            st.video(video_path)
           
            with open(video_path, "rb") as f:
                st.download_button(
                    label="Télécharger Vidéo MP4",
                    data=f,
                    file_name=f"Pub_{company}_{subject.replace(' ', '_')}.mp4",
                    mime="video/mp4"
                )
           
            # Cleanup
            os.remove(audio_path)
            os.remove(video_path)
            for img in images:
                if 'avatars' not in img:
                    os.remove(img)
            gc.collect() # Force memory cleanup
           
            progress_bar.progress(1.0)
            status_text.text("Terminé !")
           
        except Exception as e:
            st.error(f"Erreur vidéo : {str(e)}")
            if os.path.exists(audio_path):
                os.remove(audio_path)
            gc.collect()

st.markdown("---")
st.caption("Optimisations CPU : FPS réduit (15), preset ultrafast, moins d'images/fades, cleanup mémoire, timeouts courts. Prochaines : Async scraping, cloud offload. Contact GitHub ! 🚀")
