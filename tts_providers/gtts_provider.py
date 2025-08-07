
from gtts import gTTS

def generate_audio(text, output_path, lang='en'):
    """
    Generates an audio file using Google Text-to-Speech (gTTS).

    Args:
        text (str): The text to convert to speech.
        output_path (str): The full path to save the .mp3 file.
        lang (str): The language for the TTS engine.

    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        tts = gTTS(text=text, lang=lang)
        tts.save(output_path)
        return True
    except Exception as e:
        print(f"❌ gTTS Error for text '{text[:20]}...': {e}")
        return False