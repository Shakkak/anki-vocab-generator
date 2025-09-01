import warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)


# In main.py
import os
import re
from typing import List
import pandas as pd
from pathlib import Path
import argparse
import json
# --- lOCAL iMports ---
from ankigen.ankigenclass import process_dataframe, AnkiCardGenerator, get_csv_informations, create_initial_structure, edit_card_structure, get_csv_files_windows_sorted_stdlib
from tts_modules.kokoro import *
from tts_modules.utils import *
# === CONFIGURATION ===



parser = argparse.ArgumentParser(description="Process one or more CSV files with optional same-structure validation.")



parser.add_argument(
    "--name",
    type=str,
    default="default_name",
    help="Provide a name string"
)

# Boolean flag for same structure
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
    default="Word",
    help="The column name to use as the key for merging duplicates (e.g., 'Word')."
)

args = parser.parse_args()

CSV_FOLDER = './input'
AUDIO_FOLDER = 'output/audio'
DECK_NAME_PREFIX = args.name 
OUTPUT_FILENAME = f'output/{DECK_NAME_PREFIX}.apkg'

try:
    sorted_csv_list_stdlib = get_csv_files_windows_sorted_stdlib(CSV_FOLDER)
    print(f"\nFiles found and sorted from '{CSV_FOLDER}':")
    for file_path in sorted_csv_list_stdlib:
        print(f"- {file_path.name}")

except FileNotFoundError as e:
    print(e)

if len(sorted_csv_list_stdlib) == 0:
    raise ValueError("No CSV found")
elif len(sorted_csv_list_stdlib) == 1:
    multiple_csv_flag = False
else:
    multiple_csv_flag = True    

if not multiple_csv_flag:
    pass

elif multiple_csv_flag and args.same_structure and args.merge_duplicates:
    # print('csv files:\n', sorted_csv_list_stdlib)
    headers_list, dataframes_list, filenames_list = get_csv_informations('./input')
    print("Found the following headers from your data source:")
    print(headers_list[0])
    merged_df = process_dataframe(dataframes_list[0], args.merge_duplicates, args.key_column)
    
    configuration_dir = os.path.join(CSV_FOLDER, filenames_list[0])
    configuration_dir = Path(configuration_dir).with_suffix('.json')
    
    initial_card_structure = create_initial_structure(headers_list[0], configuration_dir)
    # print(f"Configuration saved at {configuration_dir}.")
    print(json.dumps(initial_card_structure, indent=4))
    generate_all_audio_files(configuration_dir, CSV_FOLDER, AUDIO_FOLDER)
    
elif multiple_csv_flag and args.same_structure and args.merge_duplicates:
    pass

    # 2. Call the new function to build the initial structure.
    #    The script will now enter the interactive setup menu.
#     
#     

#     # use a pretty printer or a helper function to display it

#     
    
# elif multiple_csv_flag and not args.same_structure:
#     pass







# json_path = './input/Ch1.json'
# print('sounds:\n',get_audio_columns_from_config(json_path))
# AUDIO_FOLDER = './output/audio'



# generate_all_audio_files()
