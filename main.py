# In main.py

import os
import pandas as pd
from pathlib import Path

# --- Local Imports ---
from anki_deck_generator import create_anki_deck
# ★★★ This is where you choose your TTS engine! ★★★
# To switch, you would change this import, e.g., from tts_providers.aws_polly_provider import generate_audio
from tts_providers.gtts_provider import generate_audio as tts_provider

# === CONFIGURATION ===
CSV_FOLDER = 'input'
AUDIO_FOLDER = 'output/audio'
DECK_NAME_PREFIX = 'English Vocabulary Learning'
OUTPUT_FILENAME = 'output/English_Vocabulary_Deck.apkg'

# Columns from which to generate audio
COLUMNS_FOR_AUDIO = ["Word", "Meaning Definition", "Related Words Notes"]

def generate_all_audio_files():
    """
    Orchestrates the generation of all required audio files.
    """
    print("--- Starting Audio Generation ---")
    os.makedirs(AUDIO_FOLDER, exist_ok=True)

    try:
        csv_files = sorted(Path(CSV_FOLDER).glob('ch*.csv'))
        if not csv_files:
            print(f"⚠️  No CSV files found in '{CSV_FOLDER}'.")
            return
    except FileNotFoundError:
        print(f"❌ Error: The directory '{CSV_FOLDER}' was not found.")
        return

    for csv_file_path in csv_files:
        chapter_num = int(csv_file_path.stem.replace('ch', ''))
        print(f"\nProcessing Audio for: {csv_file_path.name}")

        df = pd.read_csv(csv_file_path)
        for index, row in df.iterrows():
            for col_name in COLUMNS_FOR_AUDIO:
                if col_name in row and pd.notna(row[col_name]):
                    text_to_speak = str(row[col_name])
                    audio_filename = f"ch{chapter_num}_{index}_{col_name.replace(' ', '_')}.mp3"
                    output_path = os.path.join(AUDIO_FOLDER, audio_filename)

                    # Only generate audio if it doesn't already exist
                    if not os.path.exists(output_path):
                        print(f"  -> Generating: {audio_filename}")
                        # Call the chosen TTS provider
                        tts_provider(text=text_to_speak, output_path=output_path)
                    else:
                        print(f"  -- Skipping, exists: {audio_filename}")

# === MAIN EXECUTION ===
if __name__ == "__main__":
    # In Colab/scripts, ensure necessary directories exist before running
    os.makedirs(CSV_FOLDER, exist_ok=True)
    os.makedirs(os.path.dirname(OUTPUT_FILENAME), exist_ok=True)

    # Step 1: Generate all necessary audio files.
    generate_all_audio_files()
    print("\n--- Audio Generation Complete ---")

    # Step 2: Create the Anki deck using the generated files.
    print("\n--- Starting Anki Deck Creation ---")
    create_anki_deck(CSV_FOLDER, AUDIO_FOLDER, OUTPUT_FILENAME, DECK_NAME_PREFIX)
    print("\n--- All tasks complete. ---")