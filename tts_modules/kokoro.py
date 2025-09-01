import os
import shutil
import soundfile as sf
from pydub import AudioSegment
from kokoro.pipeline import KPipeline  # assuming you're using kokoro-tts

def generate_speech(lang_code, voice, text, chunk_dir, chunk_base="chunk"):
    """
    Generates MP3 chunks from input text using Kokoro TTS and saves them into chunk_dir.

    Args:
        lang_code (str): Language code for Kokoro TTS.
        voice (str): Voice name for Kokoro TTS.
        text (str): Input text to synthesize.
        chunk_dir (str): Directory to save individual MP3 chunks.
        chunk_base (str): Base name for each chunk file.
    """
    os.makedirs(chunk_dir, exist_ok=True)

    # Install espeak-ng (Linux systems)
    os.system("apt-get -qq -y install espeak-ng > /dev/null 2>&1")

    pipeline = KPipeline(lang_code=lang_code)

    generator = pipeline(
        text,
        voice=voice,
        speed=1,
        split_pattern=r'\n+'
    )

    for i, (gs, ps, audio) in enumerate(generator):
        # print(f"\n--- Chunk {i} ---")
        # print("Text:", gs)
        # print("Phonemes:", ps)

        wav_path = os.path.join(chunk_dir, f"{chunk_base}_{i}.wav")
        sf.write(wav_path, audio, 24000)

        mp3_path = os.path.join(chunk_dir, f"{chunk_base}_{i}.mp3")
        sound = AudioSegment.from_wav(wav_path)
        sound.export(mp3_path, format="mp3")
        # print(f"Saved MP3: {mp3_path}")

        os.remove(wav_path)

def merge_mp3_chunks(folder_path, output_path):
    """
    Merges all .mp3 chunks in a folder into a single mp3 file.

    Args:
        folder_path (str): Path to folder containing .mp3 chunks.
        output_path (str): Path for the final merged MP3 file.
    """
    files = sorted([
        f for f in os.listdir(folder_path)
        if f.lower().endswith(".mp3")
    ])

    if not files:
        print("No .mp3 files found in folder.")
        return

    merged = AudioSegment.empty()
    for f in files:
        mp3_path = os.path.join(folder_path, f)
        merged += AudioSegment.from_mp3(mp3_path)

    merged.export(output_path, format="mp3")
    print(f"Merged MP3 saved to: {output_path}")

def generate_and_merge_speech(lang_code, voice, text, chunk_dir, output_dir, output_name="output", chunk_base="chunk"):
    """
    Complete pipeline: generate MP3 chunks and merge into a final MP3 file.

    Args:
        lang_code (str): Language code.
        voice (str): Voice name.
        text (str): Input text.
        chunk_dir (str): Directory to store chunks.
        output_dir (str): Directory to store final merged MP3.
        output_name (str): Name of final MP3 (without extension).
        chunk_base (str): Base name for chunk files.
    """
    # print("[1/3] Generating speech chunks...")
    generate_speech(lang_code, voice, text, chunk_dir, chunk_base)

    os.makedirs(output_dir, exist_ok=True)
    final_output_path = os.path.join(output_dir, f"{output_name}.mp3")

    # print("[2/3] Merging chunks...")
    merge_mp3_chunks(chunk_dir, final_output_path)

    # print("[3/3] Cleaning up chunk directory...")
    shutil.rmtree(chunk_dir)
    # print(f"Deleted chunk directory: {chunk_dir}")
