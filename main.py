import warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

import os
import json
import pandas as pd
from pathlib import Path
import argparse
import sys

# --- LOCAL imports ---
from ankigen.ankigenclass import (
    merge_dataframe,
    get_csv_informations,
    create_initial_structure,
    get_csv_files_windows_sorted_stdlib
)
from tts_modules.utils import generate_all_audio_from_df

# === CLI ARGUMENTS ===
parser = argparse.ArgumentParser(description="Generate Anki decks with optional TTS audio.")

parser.add_argument(
    "--name",
    type=str,
    default="default_name",
    help="Provide a name string"
)

parser.add_argument(
    "--same_structure",
    action="store_true",
    help="Set if all CSVs have the same structure"
)

parser.add_argument(
    "--merge_duplicates",
    action="store_true",
    help="Merge rows with the same value in the specified key column."
)

parser.add_argument(
    "--key_column",
    type=str,
    help="Column name to use as the key when merging duplicates (e.g., 'Word')."
)

args = parser.parse_args()

# === SAFETY CHECK ===
if args.merge_duplicates and not args.key_column:
    print("❌ Error: You must specify --key_column if --merge_duplicates is set.")
    sys.exit(1)

# === PATHS ===
CSV_FOLDER = Path("./input")
AUDIO_FOLDER = Path("output/audio")
DECK_NAME_PREFIX = args.name
OUTPUT_FILENAME = Path(f"output/{DECK_NAME_PREFIX}.apkg")

# === STEP 1: FIND CSV FILES ===
try:
    sorted_csv_list_stdlib = get_csv_files_windows_sorted_stdlib(CSV_FOLDER)
    print(f"\nFiles found and sorted from '{CSV_FOLDER}':")
    for file_path in sorted_csv_list_stdlib:
        print(f"- {file_path.name}")
except FileNotFoundError as e:
    print(e)
    raise

if not sorted_csv_list_stdlib:
    raise ValueError("❌ No CSV found in input folder.")

multiple_csv_flag = len(sorted_csv_list_stdlib) > 1

# === STEP 2: PROCESS MULTIPLE CSVs ===
if multiple_csv_flag and args.same_structure and args.merge_duplicates:
    headers_list, dataframes_list, filenames_list = get_csv_informations(CSV_FOLDER)
    print("Found the following headers from your data source:")
    print(headers_list[0])

    for idx, (df, headers, filename) in enumerate(zip(dataframes_list, headers_list, filenames_list), start=1):
        print(f"\n--- Processing DataFrame {idx}: {filename} ---")

        # Merge duplicates if requested
        merged_df = merge_dataframe(df, args.merge_duplicates, args.key_column)

        # Prepare JSON configuration path
        configuration_path = Path(CSV_FOLDER, filename).with_suffix(".json")

        # Create initial card structure (writes JSON if missing)
        initial_card_structure = create_initial_structure(headers, configuration_path)
        print(json.dumps(initial_card_structure, indent=4))

        # Generate audio for this DataFrame
        chapter_id = idx
        generate_all_audio_from_df(merged_df, chapter_id, configuration_path, AUDIO_FOLDER)

elif multiple_csv_flag:
    print("⚠️ Multiple CSVs found, but conditions (--same_structure and --merge_duplicates) not satisfied.")
    print("No processing performed.")

else:
    print("✅ Single CSV mode not yet implemented in this script.")



# import warnings
# warnings.filterwarnings("ignore", category=UserWarning)
# warnings.filterwarnings("ignore", category=FutureWarning)


# # In main.py
# import os
# import re
# from typing import List
# import pandas as pd
# from pathlib import Path
# import argparse
# import json
# # --- lOCAL iMports ---
# from ankigen.ankigenclass import merge_dataframe, AnkiCardGenerator, get_csv_informations, create_initial_structure, edit_card_structure, get_csv_files_windows_sorted_stdlib
# from tts_modules.kokoro import *
# from tts_modules.utils import *
# # === CONFIGURATION ===



# parser = argparse.ArgumentParser(description="Process one or more CSV files with optional same-structure validation.")



# parser.add_argument(
#     "--name",
#     type=str,
#     default="default_name",
#     help="Provide a name string"
# )

# # Boolean flag for same structure
# parser.add_argument(
#     "--same_structure",
#     action="store_true",
#     help="Set if all CSVs have the same structure"
# )

# parser.add_argument(
#     "--merge_duplicates",
#     action="store_true",
#     help="Merge rows with the same value in the specified key column."
# )

# parser.add_argument(
#     "--key_column",
#     type=str,
#     default="Word",
#     help="The column name to use as the key for merging duplicates (e.g., 'Word')."
# )

# args = parser.parse_args()

# CSV_FOLDER = './input'
# AUDIO_FOLDER = 'output/audio'
# DECK_NAME_PREFIX = args.name 
# OUTPUT_FILENAME = f'output/{DECK_NAME_PREFIX}.apkg'

# try:
#     sorted_csv_list_stdlib = get_csv_files_windows_sorted_stdlib(CSV_FOLDER)
#     print(f"\nFiles found and sorted from '{CSV_FOLDER}':")
#     for file_path in sorted_csv_list_stdlib:
#         print(f"- {file_path.name}")

# except FileNotFoundError as e:
#     print(e)

# if len(sorted_csv_list_stdlib) == 0:
#     raise ValueError("No CSV found")
# elif len(sorted_csv_list_stdlib) == 1:
#     multiple_csv_flag = False
# else:
#     multiple_csv_flag = True    

# if not multiple_csv_flag:
#     pass

# elif multiple_csv_flag and args.same_structure and args.merge_duplicates:
#     # print('csv files:\n', sorted_csv_list_stdlib)
#     headers_list, dataframes_list, filenames_list = get_csv_informations('./input')
#     print("Found the following headers from your data source:")
#     print(headers_list[0])

#     for idx, (df, headers, filename) in enumerate(zip(dataframes_list, headers_list, filenames_list), start=1):
#         print(f"\n--- Processing DataFrame {idx}: {filename} ---")

#         # Merge duplicates if requested
#         merged_df = merge_dataframe(df, args.merge_duplicates, args.key_column)

#         # Prepare JSON configuration path
#         configuration_dir = os.path.join(CSV_FOLDER, filename)
#         configuration_dir = Path(configuration_dir).with_suffix('.json')

#         # Create initial card structure
#         initial_card_structure = create_initial_structure(headers, configuration_dir)
#         print(json.dumps(initial_card_structure, indent=4))

#         # Generate audio from the merged DataFrame
#         chapter_id = idx  # Or some other logic to assign chapter IDs
#         generate_all_audio_from_df(merged_df, chapter_id, configuration_dir, AUDIO_FOLDER)
    
# elif multiple_csv_flag and args.same_structure and args.merge_duplicates:
#     pass
