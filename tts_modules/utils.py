from tts_modules.kokoro import *
from pathlib import Path
import json
import os
import pandas as pd

def get_audio_columns_from_config(json_path):
    """
    Parses the JSON config file to get a list of all column types
    that have "audio": true.

    Args:
        json_path (str): The path to the JSON configuration file.

    Returns:
        set: A set of column names that require audio generation.
             Returns an empty set if the file is not found or is invalid.
    """
    try:
        with open(json_path, 'r') as f:
            config_data = json.load(f)
        
        audio_columns = set()
        # Check both "front" and "back" sections of the config
        for section in config_data.values():
            for item in section:
                if item.get("audio") and "type" in item:
                    audio_columns.add(item["type"])
        
        return audio_columns
    except FileNotFoundError:
        print(f"❌ Error: Configuration file not found at '{json_path}'.")
        return set()
    except json.JSONDecodeError:
        print(f"❌ Error: Could not parse the JSON file at '{json_path}'. Please check its format.")
        return set()




def get_columns_for_audio(json_path):
    # Implement this based on your config structure
    return get_audio_columns_from_config(json_path)

def sanitize_text(text):
    return text.replace("<br>", " ;- ").strip()

def split_text_by_delimiter(text, delimiter="#"):
    return [part.strip() for part in str(text).split(delimiter)]

# def generate_audio_for_row(chapter_num, row_idx, col_name, text, output_base, voice_params, audio_folders):
#     """
#     Generate audio for each part of the split text (by #).
#     """
#     split_parts = split_text_by_delimiter(text)
    
#     for part_idx, part in enumerate(split_parts):
#         if not part:
#             continue  # Skip empty segments

#         output_name = f"{output_base}_{part_idx}"

#         generate_and_merge_speech(
#             lang_code=voice_params["lang_code"],
#             voice=voice_params["voice"],
#             text=sanitize_text(part),
#             chunk_dir=os.path.join(audio_folders["base"], "chunks"),
#             output_dir=audio_folders["base"],
#             output_name=output_name
#         )

#         print(f"  -> Generated: {output_name}.mp3")

# def process_csv_file(csv_file_path, columns_for_audio, audio_folders, voice_params):
#     """
#     Process a single CSV file and generate audio for each flagged column.
#     """
#     chapter_num = int(csv_file_path.stem.replace('Ch', ''))
#     print(f"\nProcessing Audio for: {csv_file_path.name}")

#     df = pd.read_csv(csv_file_path)

#     for row_idx, row in df.iterrows():
#         for col_name in columns_for_audio:
#             if col_name in row and pd.notna(row[col_name]):
#                 output_base = f"ch{chapter_num}_{row_idx}_{col_name.replace(' ', '_')}"
#                 generate_audio_for_row(
#                     chapter_num=chapter_num,
#                     row_idx=row_idx,
#                     col_name=col_name,
#                     text=row[col_name],
#                     output_base=output_base,
#                     voice_params=voice_params,
#                     audio_folders=audio_folders
#                 )

def process_dataframe(df, chapter_id, columns_for_audio, audio_folders, voice_params):
    """
    Processes a DataFrame row by row to generate audio for specified columns.

    Parameters:
        df (pd.DataFrame): The input data.
        chapter_id (str): Used in naming the audio files.
        columns_for_audio (List[str]): Which columns to generate audio for.
        audio_folders (dict): Folder structure for audio output.
        voice_params (dict): Language and voice settings.
    """
    for row_idx, row in df.iterrows():
        for col_name in columns_for_audio:
            if pd.isna(row[col_name]):
                continue
            text_parts = str(row[col_name]).split('#')  # Split by delimiter
            for part_idx, part in enumerate(text_parts):
                if part.strip():
                    filename = f"ch{chapter_id}_r{row_idx+1}_c{col_name}_p{part_idx+1}.mp3"
                    output_path = Path(audio_folders["base"]) / filename
                    generate_and_merge_speech(
                        lang_code=voice_params["lang_code"],
                        voice=voice_params["voice"],
                        text=sanitize_text(part),
                        chunk_dir=os.path.join(audio_folders["base"], "chunks"),
                        output_dir=audio_folders["base"],
                        output_name=filename
                    )


def generate_all_audio_from_df(df, chapter_id, json_path, AUDIO_FOLDER):
    """
    Generates all required audio files based on the JSON config and a given DataFrame.

    Parameters:
        df (pd.DataFrame): The input data (e.g. merged CSV).
        chapter_id (str): Identifier for the chapter, used in naming audio files.
        json_path (str): Path to JSON config specifying which columns to process.
        AUDIO_FOLDER (str): Root folder where audio files will be saved.
    """
    print("--- Starting Audio Generation ---")
    os.makedirs(AUDIO_FOLDER, exist_ok=True)

    columns_for_audio = get_columns_for_audio(json_path)
    if not columns_for_audio:
        print("⚠️  No columns configured for audio generation. Exiting.")
        return
    print(f"✅ Columns to generate audio for: {', '.join(columns_for_audio)}")

    voice_params = {
        "lang_code": "a",        # Replace with actual language code
        "voice": "af_heart"      # Replace with actual voice
    }

    audio_folders = {
        "base": AUDIO_FOLDER
    }

    # Directly process the DataFrame
    process_dataframe(df, chapter_id, columns_for_audio, audio_folders, voice_params)

    print("\n--- Audio Generation Complete ---")



# def generate_all_audio_files(json_path, CSV_FOLDER, AUDIO_FOLDER):
#     """
#     Orchestrates the generation of all required audio files based on the JSON config.
#     """
#     print("--- Starting Audio Generation ---")
#     os.makedirs(AUDIO_FOLDER, exist_ok=True)

#     # 1. Get the list of columns that need audio from the JSON file
#     columns_for_audio = get_audio_columns_from_config(json_path)
    
#     if not columns_for_audio:
#         print("⚠️  No columns configured for audio generation. Exiting.")
#         return
        
#     print(f"✅ Columns to generate audio for: {', '.join(columns_for_audio)}")

#     # 2. Find all chapter CSV files
#     try:
#         csv_files = sorted(Path(CSV_FOLDER).glob('Ch*.csv'))
#         if not csv_files:
#             print(f"⚠️  No CSV files starting with 'Ch' found in '{CSV_FOLDER}'.")
#             return
#     except FileNotFoundError:
#         print(f"❌ Error: The directory '{CSV_FOLDER}' was not found.")
#         return

#     # 3. Process each CSV file
#     for csv_file_path in csv_files:
#         try:
#             # Extract chapter number from filename like 'Ch1.csv' or 'Ch12.csv'
#             chapter_num = int(csv_file_path.stem.replace('Ch', ''))
#         except (ValueError, IndexError):
#             print(f"⚠️  Skipping file with unexpected name format: {csv_file_path.name}")
#             continue

#         print(f"\nProcessing Audio for: {csv_file_path.name}")
#         df = pd.read_csv(csv_file_path)

#         # 4. Iterate through each row and the designated columns
#         for index, row in df.iterrows():
#             for col_name in columns_for_audio:
#                 if col_name in row and pd.notna(row[col_name]):
                    
#                     text_to_speak = str(row[col_name])
#                     text_to_speak = text_to_speak.replace("<br>", " ;- ")
#                     # Define the output filename structure
#                     output_base_name = f"ch{chapter_num}_{index}_{col_name.replace(' ', '_')}"

#                     # # 5. Generate audio only if it doesn't already exist
#                     # if not os.path.exists(output_path_with_ext):
#                     #     print(f"  -> Generating: {output_base_name}.mp3")
                        
#                         # Call your specific TTS function
#                     generate_and_merge_speech(
#                         lang_code="a",
#                         voice ="af_heart",
#                         text = text_to_speak,
#                         chunk_dir = os.path.join(AUDIO_FOLDER, "chunks"),
#                         output_dir = AUDIO_FOLDER,
#                         output_name = output_base_name
#                     )

#                     # else:
#                     #     print(f"  -- Skipping, exists: {output_base_name}.mp3")

#     print("\n--- Audio Generation Complete ---")