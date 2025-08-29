# In main.py
import os
import pandas as pd
from pathlib import Path
import argparse
import json
# --- lOCAL iMports ---
from ankigen.ankigenclass import AnkiCardGenerator,get_csv_headers, create_initial_structure, edit_card_structure 
from tts_providers.kokoro import *
# === CONFIGURATION ===


parser = argparse.ArgumentParser(description="Process one or more CSV files with optional same-structure validation.")



parser.add_argument(
    "--name",
    type=str,
    default="default_name",
    help="Provide a name string"
)

# Boolean flag for multiple CSVs
parser.add_argument(
    "--multiple",
    action="store_true",
    help="Set if multiple CSV files are provided"
)

# Boolean flag for same structure
parser.add_argument(
    "--same_structure",
    action="store_true",
    help="Set if all CSVs have the same structure"
)

args = parser.parse_args()

CSV_FOLDER = 'input'
AUDIO_FOLDER = 'output/audio'
DECK_NAME_PREFIX = args.name 
OUTPUT_FILENAME = f'output/{DECK_NAME_PREFIX}.apkg'
if not args.multiple:
    args.same_structure = False
    
csv_headers, csv_path = get_csv_headers('./input')

print("Found the following headers from your data source:")
print(csv_headers)

# # 2. Call the new function to build the initial structure.
# #    The script will now enter the interactive setup menu.
# initial_card_structure = create_initial_structure(csv_headers, csv_path)
# print(f"Configuration saved to '{csv_path.with_suffix('.json')}'")

# # use a pretty printer or a helper function to display it

# print(json.dumps(initial_card_structure, indent=4))


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

json_path = './input/Ch1.json'
print('sounds:\n',get_audio_columns_from_config(json_path))
AUDIO_FOLDER = 'your_audio_folder'

def generate_all_audio_files():
    """
    Orchestrates the generation of all required audio files based on the JSON config.
    """
    print("--- Starting Audio Generation ---")
    os.makedirs(AUDIO_FOLDER, exist_ok=True)

    # 1. Get the list of columns that need audio from the JSON file
    columns_for_audio = get_audio_columns_from_config(json_path)
    
    if not columns_for_audio:
        print("⚠️  No columns configured for audio generation. Exiting.")
        return
        
    print(f"✅ Columns to generate audio for: {', '.join(columns_for_audio)}")

    # 2. Find all chapter CSV files
    try:
        csv_files = sorted(Path(CSV_FOLDER).glob('Ch*.csv'))
        if not csv_files:
            print(f"⚠️  No CSV files starting with 'Ch' found in '{CSV_FOLDER}'.")
            return
    except FileNotFoundError:
        print(f"❌ Error: The directory '{CSV_FOLDER}' was not found.")
        return

    # 3. Process each CSV file
    for csv_file_path in csv_files:
        try:
            # Extract chapter number from filename like 'Ch1.csv' or 'Ch12.csv'
            chapter_num = int(csv_file_path.stem.replace('Ch', ''))
        except (ValueError, IndexError):
            print(f"⚠️  Skipping file with unexpected name format: {csv_file_path.name}")
            continue

        print(f"\nProcessing Audio for: {csv_file_path.name}")
        df = pd.read_csv(csv_file_path)

        # 4. Iterate through each row and the designated columns
        for index, row in df.iterrows():
            for col_name in columns_for_audio:
                if col_name in row and pd.notna(row[col_name]):
                    text_to_speak = str(row[col_name])
                    
                    # Define the output filename structure
                    output_base_name = f"ch{chapter_num}_{index}_{col_name.replace(' ', '_')}"
                    output_path_with_ext = os.path.join(AUDIO_FOLDER, f"{output_base_name}.mp3")

                    # 5. Generate audio only if it doesn't already exist
                    if not os.path.exists(output_path_with_ext):
                        print(f"  -> Generating: {output_base_name}.mp3")
                        
                        # Call your specific TTS function
                        generate_and_merge_speech(
                            lang_code="a",         # Placeholder value as requested
                            voice="af_heart",      # Placeholder value as requested
                            text=text_to_speak,
                            output_name=output_base_name # Pass the name without extension
                        )
                    else:
                        print(f"  -- Skipping, exists: {output_base_name}.mp3")

    print("\n--- Audio Generation Complete ---")

generate_all_audio_files()
# --- To run the script ---
# if __name__ == '__main__':
    # Before running:
    # 1. Create a folder named 'your_csv_folder' and place your 'Ch1.csv', 'Ch2.csv', etc. inside.
    # 2. Create a folder named 'your_audio_folder'.
    # 3. Save your JSON content into a file named 'audio_config.json' in the same directory as this script.
    
    # generate_all_audio_files()
# # 3. Initialize the generator with your CSS
# generator = AnkiCardGenerator(css=default_css)

# # 3. Visualize the template with your structure in the shell
# generator.visualize(initial_card_structure)

# # 4. You can still generate the Anki template as before
# anki_template = generator.make_template(initial_card_structure)

# # Print the generated template to see the data structure
# # import json
# # print("\n\nGenerated Anki Template Data:\n")
# # print(json.dumps(anki_template, indent=4))


# edited_structure = edit_card_structure(initial_card_structure, csv_path)
# print("\n--- Structure after further edits ---")
# print(json.dumps(edited_structure, indent=4))
# print(f"Configuration saved to '{csv_path.with_suffix('.json')}'")


# print("\nFinal, updated structure:")
# _print_structure(edited_structure) # Using the helper to print the final result
# print(f"Configuration saved to '{csv_path.with_suffix('.json')}'")


# sample_text = """
# The sky above the port was the color of television, tuned to a dead channel.

# [Kokoro](/kˈOkəɹO/) is an open-weight TTS model.
# """

# generate_and_merge_speech(
#     lang_code="a",
#     voice="af_heart",
#     text=sample_text,
#     output_name="kokoro_demo"
# )




# # === MAIN EXECUTION ===
# if __name__ == "__main__":
#     # In Colab/scripts, ensure necessary directories exist before running
#     os.makedirs(CSV_FOLDER, exist_ok=True)
#     os.makedirs(os.path.dirname(OUTPUT_FILENAME), exist_ok=True)

#     # Step 1: Generate all necessary audio files.
#     print("\n--- Audio Generation Complete ---")

#     # Step 2: Create the Anki deck using the generated files.
#     print("\n--- Starting Anki Deck Creation ---")
#     create_anki_deck(CSV_FOLDER, AUDIO_FOLDER, OUTPUT_FILENAME, DECK_NAME_PREFIX)
#     print("\n--- All tasks complete. ---")