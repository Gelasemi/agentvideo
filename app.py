import streamlit as st
from gtts import gTTS
from moviepy.editor import ImageClip, AudioFileClip, TextClip, CompositeVideoClip
import os
import tempfile

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

def generate_simple_script(subject, lang_code):
    """
    Very basic AIDA-style script template.
    In future versions we can improve this significantly.
    """
    # We keep it in English structure – gTTS will pronounce according to lang_code
    script = (
        f"Attention ! {subject} est en train de changer le monde. "
        f"Intéressant, non ? Beaucoup de gens en parlent déjà. "
        f"Vous aussi, vous pouvez en profiter. "
        f"Action : likez, commentez et abonnez-vous pour plus de contenu !"
    )
    return script

st.set_page_config(page_title="GlobeCast AI MVP", layout="wide")

st.title("🌍 GlobeCast AI – Agent Vidéo Nouvelle Génération (MVP Zéro Budget)")
st.markdown("""
**Créé par : Dauphin Gelase Michelot**  
**Label :** M&G Consulting  
**GitHub :** [gelasemi](https://github.com/gelasemi)  
**Niveau :** Starter  
**Date :** Février 2026  
""")

st.info("Version MVP – Avatar statique + voix synthétique + sous-titres simples. Pas d'animation faciale (CPU only).")

# User inputs
subject = st.text_input("Sujet de la vidéo", placeholder="Exemple : Café éthique à Madagascar", value="Café éthique")
language_name = st.selectbox("Langue de la vidéo", list(LANGUAGES.keys()))
platform = st.selectbox("Format / Plateforme cible", [
    "TikTok – Vertical 9:16 (1080×1920)",
    "YouTube – Horizontal 16:9 (1920×1080)",
    "Facebook/Instagram – Carré 1:1 (1080×1080)"
])

if st.button("🎥 Générer la Vidéo Maintenant", type="primary"):
    if not subject.strip():
        st.error("Veuillez entrer un sujet valide.")
    else:
        with st.spinner("Génération en cours... (10–40 secondes selon la longueur)"):
            lang_code = LANGUAGES[language_name]

            # 1. Generate script
            script_text = generate_simple_script(subject, lang_code)

            # Show script preview
            st.subheader("Script généré (aperçu)")
            st.write(script_text)

            # 2. Text-to-Speech
            try:
                tts = gTTS(text=script_text, lang=lang_code, slow=False)
                audio_path = tempfile.mktemp(suffix=".mp3")
                tts.save(audio_path)
            except Exception as e:
                st.error(f"Erreur lors de la synthèse vocale : {e}")
                st.stop()

            # 3. Check avatar exists
            avatar_filename = f"avatar_{lang_code}.png"
            avatar_path = os.path.join("avatars", avatar_filename)

            if not os.path.exists(avatar_path):
                st.error(f"""
                Avatar manquant pour {language_name} !  
                → Ajoutez le fichier : **avatars/{avatar_filename}** dans votre dépôt GitHub  
                → Téléchargez une image libre de droits (Unsplash/Pexels) et renommez-la correctement.
                """)
                if os.path.exists(audio_path):
                    os.remove(audio_path)
                st.stop()

            # 4. Create video
            try:
                audio_clip = AudioFileClip(audio_path)
                duration = audio_clip.duration

                # Load and resize image
                img_clip = ImageClip(avatar_path).set_duration(duration)

                if platform.startswith("TikTok"):
                    size = (1080, 1920)
                elif platform.startswith("YouTube"):
                    size = (1920, 1080)
                else:
                    size = (1080, 1080)

                img_clip = img_clip.resize(size)

                # Simple subtitle (shows beginning of script)
                subtitle = script_text[:80] + "..." if len(script_text) > 80 else script_text
                txt_clip = TextClip(
                    subtitle,
                    fontsize=70,
                    color='white',
                    stroke_color='black',
                    stroke_width=2,
                    font='Arial-Bold',
                    method='caption',
                    align='center',
                    size=(size[0]-80, None)
                ).set_position(('center', 'bottom')).set_duration(duration).margin(bottom=40, opacity=0)

                # Compose final video
                final_video = CompositeVideoClip([img_clip, txt_clip]).set_audio(audio_clip)

                # Export
                video_path = tempfile.mktemp(suffix=".mp4")
                final_video.write_videofile(
                    video_path,
                    fps=24,
                    codec="libx264",
                    audio_codec="aac",
                    verbose=False,
                    logger=None
                )

                # Success!
                st.success("Vidéo générée avec succès !")
                st.video(video_path)

                # Download button
                with open(video_path, "rb") as video_file:
                    st.download_button(
                        label="Télécharger la vidéo (MP4)",
                        data=video_file,
                        file_name=f"GlobeCast_{subject.replace(' ', '_')}_{lang_code}.mp4",
                        mime="video/mp4"
                    )

                # Cleanup
                os.remove(audio_path)
                os.remove(video_path)

            except Exception as e:
                st.error(f"Erreur lors de la création de la vidéo : {str(e)}")
                # Cleanup on error
                for path in [audio_path, video_path]:
                    if 'path' in locals() and os.path.exists(path):
                        os.remove(path)

st.markdown("---")

st.caption("Prochaines étapes possibles : meilleure génération de script, musique de fond gratuite, avatars IA simples via PIL, publication directe... Contactez-moi sur GitHub ! 🚀")

