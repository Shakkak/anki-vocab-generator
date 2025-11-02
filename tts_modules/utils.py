import os
import json
import shutil
import pandas as pd
from pathlib import Path
from tqdm import tqdm
from tts_modules.kokoro import generate_batched_speech
from pydub import AudioSegment

# ------------------------
# JSON helper for same_structure
# ------------------------
def copy_json_for_same_structure(first_json_path: Path, csv_filenames: list[str]):
    """
    Copies the first JSON config file to create configs for all other CSVs.
    """
    for csv_file in csv_filenames[1:]:
        target_json = Path(first_json_path.parent) / Path(csv_file).with_suffix(".json")
        if not target_json.exists():
            shutil.copy(first_json_path, target_json)
            print(f"✅ Copied JSON config to {target_json}")
        else:
            print(f"⚠️ JSON already exists for {csv_file}, skipping.")

# ------------------------
# Config parsing
# ------------------------
def get_audio_columns_from_config(json_path):
    try:
        with open(json_path, 'r') as f:
            config_data = json.load(f)
        audio_columns = set()
        for section in config_data.values():
            for item in section:
                if item.get("audio") and "type" in item:
                    audio_columns.add(item["type"])
        return audio_columns
    except FileNotFoundError:
        print(f"❌ Error: Configuration file not found at '{json_path}'.")
        return set()
    except json.JSONDecodeError:
        print(f"❌ Error: Invalid JSON at '{json_path}'.")
        return set()

def get_columns_for_audio(json_path):
    return get_audio_columns_from_config(json_path)

# ------------------------
# Text helpers
# ------------------------
def sanitize_text(text):
    return str(text).replace("<br>", " ;- ").strip()

def split_text_by_delimiter(text, delimiter="#"):
    return [part.strip() for part in str(text).split(delimiter)]

# ------------------------
# Main dataframe processing
# ------------------------
def process_dataframe(df, chapter_id, columns_for_audio, audio_folders, voice_params):
    """
    Process DataFrame and generate audio for each cell using batched TTS.
    """
    for row_idx, row in enumerate(tqdm(df.iterrows(), total=len(df), desc=f"CSV {chapter_id}"), start=1):
        row = row[1]  # unpack iterrows()
        for col_name in columns_for_audio:
            value = row[col_name]
            if pd.isna(value):
                continue

            # Split text into parts
            text_parts = [sanitize_text(p) for p in str(value).split('#') if p.strip()]
            if not text_parts:
                continue

            # Generate batched audio
            results = generate_batched_speech(
                voice=voice_params["voice"],
                texts=text_parts,
                lang_code=voice_params.get("lang_code", "a")
            )

            # Export each part to MP3
            for part_idx, (txt, seg) in enumerate(results, start=1):
                filename = f"ch{chapter_id}_r{row_idx}_c{col_name}_p{part_idx}.mp3"
                output_path = Path(audio_folders["base"]) / filename
                seg.export(output_path, format="mp3")

# ------------------------
# Full audio generation
# ------------------------
def generate_all_audio_from_df(df, chapter_id, json_path, AUDIO_FOLDER):
    """
    Generate all required audio files for a DataFrame based on JSON config.
    """
    print("--- Starting Audio Generation ---")
    os.makedirs(AUDIO_FOLDER, exist_ok=True)

    columns_for_audio = get_columns_for_audio(json_path)
    if not columns_for_audio:
        print("⚠️ No audio columns configured. Exiting.")
        return
    print(f"✅ Columns to generate audio for: {', '.join(columns_for_audio)}")

    voice_params = {
        "lang_code": "a",       # replace with your language code
        "voice": "af_heart"     # replace with your voice
    }

    audio_folders = {"base": AUDIO_FOLDER}
    process_dataframe(df, chapter_id, columns_for_audio, audio_folders, voice_params)

    print("\n--- Audio Generation Complete ---")
