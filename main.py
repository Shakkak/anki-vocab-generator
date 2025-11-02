import warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=SyntaxWarning)

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
    edit_card_structure,
    get_csv_files_windows_sorted_stdlib
)
from ankigen.anki_deck_generator import *
from tts_modules.utils import generate_all_audio_from_df, copy_json_for_same_structure



CARD_CSS = '''
        .card {
            font-family: Arial, sans-serif;
            font-size: 22px;
            text-align: center;
            color: #f0f0f0;
            background-color: #2c2c2c;
        }
        .card-front .word {
            font-size: 52px;
            font-weight: bold;
            margin-bottom: 20px;
            color: #FFFFFF;
        }
        .card-back .front-word {
            font-size: 36px;
            font-weight: bold;
            margin-bottom: 10px;
            color: #FFFFFF;
        }
        hr {
            border-color: #555;
        }
        .section {
            margin: 15px auto;
            max-width: 90%;
            text-align: left;
        }
        .label {
            font-weight: bold;
            color: #ccc;
            font-size: 18px;
            margin-bottom: 5px;
        }
        .content, .examples {
            line-height: 1.5;
            text-align: left;
        }
        .examples {
            white-space: pre-wrap;
            color: #89cff0;
        }
    '''

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

    # === Handle JSON for same structure ===
    # Always create JSON for the first CSV
    first_df, first_headers, first_filename = dataframes_list[0], headers_list[0], filenames_list[0]
    first_config_path = Path(CSV_FOLDER, first_filename).with_suffix(".json")

    # initial_card_structure = create_initial_structure(first_headers, first_config_path)
    # print(json.dumps(initial_card_structure, indent=4))

    # edited_version = edit_card_structure(headers_list[0], first_config_path)
    # If same_structure: copy that JSON for the rest
    if args.same_structure:
        copy_json_for_same_structure(first_config_path, filenames_list)

    # === Loop over all DataFrames ===
    for idx, (df, headers, filename) in enumerate(zip(dataframes_list, headers_list, filenames_list), start=1):
        print(f"\n--- Processing DataFrame {idx}: {filename} ---")

        merged_df = merge_dataframe(df, args.merge_duplicates, args.key_column, delimiter=" # ", output_dir= "./input/merged/", filename_prefix=filename[:-4])
        config_path = Path(CSV_FOLDER, filename).with_suffix(".json")

        # Generate audio for this DataFrame
        chapter_id = idx
        # generate_all_audio_from_df(merged_df, chapter_id, config_path, AUDIO_FOLDER)


    generator = AnkiDeckGenerator(
        json_structure_path=first_config_path,
        key_column=args.key_column,
        css=CARD_CSS
    )
    generator.generate_deck(
        csv_folder='./input/merged/',
        audio_folder=AUDIO_FOLDER,
        output_filename=OUTPUT_FILENAME,
        deck_name_prefix=DECK_NAME_PREFIX
    )

elif multiple_csv_flag:
    print("⚠️ Multiple CSVs found, but conditions (--same_structure and --merge_duplicates) not satisfied.")
    print("No processing performed.")

else:
    headers_list, dataframes_list, filenames_list = get_csv_informations(CSV_FOLDER)
    print("Found the following headers from your data source:")
    print(headers_list[0])

    # === Handle JSON for same structure ===
    # Always create JSON for the first CSV
    first_df, first_headers, first_filename = dataframes_list[0], headers_list[0], filenames_list[0]
    first_config_path = Path(CSV_FOLDER, first_filename).with_suffix(".json")

    # initial_card_structure = create_initial_structure(first_headers, first_config_path)
    # print(json.dumps(initial_card_structure, indent=4))

    # edited_version = edit_card_structure(headers_list[0], first_config_path)
    # If same_structure: copy that JSON for the rest
    if args.same_structure:
        copy_json_for_same_structure(first_config_path, filenames_list)

    for idx, (df, headers, filename) in enumerate(zip(dataframes_list, headers_list, filenames_list), start=1):
        print(f"\n--- Processing DataFrame {idx}: {filename} ---")

        # merged_df = merge_dataframe(df, args.merge_duplicates, args.key_column, delimiter=" # ", output_dir= "./input/merged/", filename_prefix=filename[:-4])
        config_path = Path(CSV_FOLDER, filename).with_suffix(".json")

        # Generate audio for this DataFrame
        chapter_id = idx
        # generate_all_audio_from_df(merged_df, chapter_id, config_path, AUDIO_FOLDER)


    generator = AnkiDeckGenerator(
        json_structure_path=first_config_path,
        #key_column=args.key_column,
        css=CARD_CSS
    )
    generator.generate_deck(
        csv_folder='./input/merged/',
        audio_folder=AUDIO_FOLDER,
        output_filename=OUTPUT_FILENAME,
        deck_name_prefix=DECK_NAME_PREFIX
    )
    
    # print("✅ Single CSV mode not yet implemented in this script.")



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
