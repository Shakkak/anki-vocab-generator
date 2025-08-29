import os
import subprocess
import soundfile as sf
from kokoro import KPipeline
from pydub import AudioSegment

def generate_speech(lang_code, voice, text, output_name="output"):
    # Install system dependency (in case you're running this in Colab)
    os.system("apt-get -qq -y install espeak-ng > /dev/null 2>&1")

    # Initialize Kokoro TTS pipeline
    pipeline = KPipeline(lang_code=lang_code)

    # Generate speech from text
    generator = pipeline(
        text,
        voice=voice,
        speed=1,
        split_pattern=r'\n+'
    )

    for i, (gs, ps, audio) in enumerate(generator):
        print(f"\n--- Chunk {i} ---")
        print("Text:", gs)
        print("Phonemes:", ps)

        # Temporary WAV path (intermediate)
        wav_path = f"{output_name}_{i}.wav"
        sf.write(wav_path, audio, 24000)

        # Export to MP3
        mp3_path = f"{output_name}_{i}.mp3"
        sound = AudioSegment.from_wav(wav_path)
        sound.export(mp3_path, format="mp3")
        print(f"Saved MP3: {mp3_path}")

        # Clean up intermediate WAV
        os.remove(wav_path)


def merge_mp3_chunks(folder_path, output_path="merged_output.mp3"):
    """
    Merges all .mp3 chunks in a folder into a single mp3 file.

    Args:
        folder_path (str): Path to the folder containing .mp3 chunks.
        output_path (str): Name/path for the final merged mp3 file.
    """
    # Sort files like chunk_0.mp3, chunk_1.mp3, ...
    files = sorted([
        f for f in os.listdir(folder_path)
        if f.lower().endswith(".mp3")
    ])

    if not files:
        print("No .mp3 files found in folder.")
        return

    # Load and concatenate audio segments
    merged = AudioSegment.empty()
    for f in files:
        chunk = AudioSegment.from_mp3(os.path.join(folder_path, f))
        merged += chunk

    # Export the final merged audio
    merged.export(output_path, format="mp3")
    print(f"Merged MP3 saved to: {output_path}")

def generate_and_merge_speech(lang_code, voice, text, output_name="output"):
    """
    Generate MP3 speech chunks from text and merge them into a single file.

    Args:
        lang_code (str): Language code for Kokoro (e.g., 'a')
        voice (str): Kokoro voice name (e.g., 'af_heart')
        text (str): Input text
        output_name (str): Base name for chunk files and final output
    """
    print("[1/2] Generating speech chunks...")
    generate_speech(lang_code, voice, text, output_name)

    print("\n[2/2] Merging chunks...")
    merge_mp3_chunks("audio_chunks", output_path=f"{output_name}_final.mp3")
