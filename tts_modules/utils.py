import os
import json
import pandas as pd
from pathlib import Path
from tqdm import tqdm
from tts_modules.kokoro import generate_batched_speech
import shutil
from pathlib import Path

def copy_json_for_same_structure(first_json_path: Path, csv_filenames: list[str]):
    """
    Copies the first JSON config file to create configs for all other CSV files.

    Args:
        first_json_path (Path): Path to the first generated JSON file.
        csv_filenames (list[str]): List of CSV filenames (not Paths).
                                   Each will get a corresponding JSON copy.
    """
    for csv_file in csv_filenames[1:]:  # Skip first, already has JSON
        target_json = Path(first_json_path.parent) / Path(csv_file).with_suffix(".json")
        if not target_json.exists():
            shutil.copy(first_json_path, target_json)
            print(f"✅ Copied JSON config to {target_json}")
        else:
            print(f"⚠️ JSON already exists for {csv_file}, skipping.")



# ---------- CONFIG PARSING ----------
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


# ---------- TEXT HELPERS ----------
def sanitize_text(text):
    return str(text).replace("<br>", " ;- ").strip()


def split_text_by_delimiter(text, delimiter="#"):
    return [part.strip() for part in str(text).split(delimiter)]


# ---------- MAIN PROCESS ----------
import numpy as np
from pydub import AudioSegment

def process_dataframe(df, chapter_id, columns_for_audio, audio_folders, voice_params):
    """
    Processes the DataFrame and generates audio files for configured columns.
    Uses batched TTS for multiple text parts per cell.
    """
    for row_idx, row in enumerate(tqdm(df.iterrows(), total=len(df), desc=f"Chapter {chapter_id}"), start=1):
        row = row[1]
        for col_name in columns_for_audio:
            value = row[col_name]
            if pd.isna(value):
                continue

            # Split into parts (batched)
            text_parts = [sanitize_text(p) for p in str(value).split('#') if p.strip()]
            if not text_parts:
                continue

            # One TTS call for all parts
            results = generate_batched_speech(voice_params["voice"], text_parts)

            # Save each as MP3 with proper normalization
            for part_idx, (txt, seg) in enumerate(results, start=1):
                filename = f"ch{chapter_id}_r{row_idx}_c{col_name}_p{part_idx}.mp3"
                output_path = Path(audio_folders["base"]) / filename

                # Convert AudioSegment to numpy float32 array
                samples = np.array(seg.get_array_of_samples()).astype(np.float32)

                # Normalize
                max_val = np.max(np.abs(samples))
                if max_val > 0:
                    samples /= max_val

                # Convert back to int16 for pydub
                seg_clean = AudioSegment(
                    (samples * 32767).astype(np.int16).tobytes(),
                    frame_rate=seg.frame_rate,
                    sample_width=2,
                    channels=seg.channels
                )

                seg_clean.export(output_path, format="mp3")



def generate_all_audio_from_df(df, chapter_id, json_path, AUDIO_FOLDER):
    """
    Generates all required audio files based on the JSON config and a given DataFrame.
    """
    print("--- Starting Audio Generation ---")
    os.makedirs(AUDIO_FOLDER, exist_ok=True)

    columns_for_audio = get_columns_for_audio(json_path)
    if not columns_for_audio:
        print("⚠️ No audio columns configured. Exiting.")
        return
    print(f"✅ Columns to generate audio for: {', '.join(columns_for_audio)}")

    voice_params = {
        "lang_code": "a",       # Replace with actual language code
        "voice": "af_heart"     # Replace with actual voice
    }

    audio_folders = {"base": AUDIO_FOLDER}
    process_dataframe(df, chapter_id, columns_for_audio, audio_folders, voice_params)

    print("\n--- Audio Generation Complete ---")



# from tts_modules.kokoro import *
# from pathlib import Path
# import json
# import os
# import pandas as pd
# from tqdm import tqdm

# def get_audio_columns_from_config(json_path):
#     """
#     Parses the JSON config file to get a list of all column types
#     that have "audio": true.

#     Args:
#         json_path (str): The path to the JSON configuration file.

#     Returns:
#         set: A set of column names that require audio generation.
#              Returns an empty set if the file is not found or is invalid.
#     """
#     try:
#         with open(json_path, 'r') as f:
#             config_data = json.load(f)
        
#         audio_columns = set()
#         # Check both "front" and "back" sections of the config
#         for section in config_data.values():
#             for item in section:
#                 if item.get("audio") and "type" in item:
#                     audio_columns.add(item["type"])
        
#         return audio_columns
#     except FileNotFoundError:
#         print(f"❌ Error: Configuration file not found at '{json_path}'.")
#         return set()
#     except json.JSONDecodeError:
#         print(f"❌ Error: Could not parse the JSON file at '{json_path}'. Please check its format.")
#         return set()




# def get_columns_for_audio(json_path):
#     # Implement this based on your config structure
#     return get_audio_columns_from_config(json_path)

# def sanitize_text(text):
#     return text.replace("<br>", " ;- ").strip()

# def split_text_by_delimiter(text, delimiter="#"):
#     return [part.strip() for part in str(text).split(delimiter)]


# from tqdm import tqdm

# def process_dataframe(df, chapter_id, columns_for_audio, audio_folders, voice_params):
#     for row_idx, row in enumerate(tqdm(df.iterrows(), total=len(df), desc=f"Chapter {chapter_id}"), start=1):
#         row = row[1]  # iterrows() returns (index, Series)
#         for col_name in columns_for_audio:
#             value = row[col_name]
#             if pd.isna(value):
#                 continue
#             text_parts = str(value).split('#')
#             for part_idx, part in enumerate(text_parts, start=1):
#                 if part.strip():
#                     filename = f"ch{chapter_id}_r{row_idx}_c{col_name}_p{part_idx}.mp3"
#                     output_path = Path(audio_folders["base"]) / filename
#                     generate_and_merge_speech(
#                         lang_code=voice_params["lang_code"],
#                         voice=voice_params["voice"],
#                         text=sanitize_text(part),
#                         chunk_dir=os.path.join(audio_folders["base"], "chunks"),
#                         output_dir=audio_folders["base"],
#                         output_name=filename
#                     )



# def generate_all_audio_from_df(df, chapter_id, json_path, AUDIO_FOLDER):
#     """
#     Generates all required audio files based on the JSON config and a given DataFrame.

#     Parameters:
#         df (pd.DataFrame): The input data (e.g. merged CSV).
#         chapter_id (str): Identifier for the chapter, used in naming audio files.
#         json_path (str): Path to JSON config specifying which columns to process.
#         AUDIO_FOLDER (str): Root folder where audio files will be saved.
#     """
#     print("--- Starting Audio Generation ---")
#     os.makedirs(AUDIO_FOLDER, exist_ok=True)

#     columns_for_audio = get_columns_for_audio(json_path)
#     if not columns_for_audio:
#         print("⚠️  No columns configured for audio generation. Exiting.")
#         return
#     print(f"✅ Columns to generate audio for: {', '.join(columns_for_audio)}")

#     voice_params = {
#         "lang_code": "a",        # Replace with actual language code
#         "voice": "af_heart"      # Replace with actual voice
#     }

#     audio_folders = {
#         "base": AUDIO_FOLDER
#     }

#     # Directly process the DataFrame
#     process_dataframe(df, chapter_id, columns_for_audio, audio_folders, voice_params)

#     print("\n--- Audio Generation Complete ---")

