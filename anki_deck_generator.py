# In anki_deck_generator.py

import os
import csv
import genanki
from pathlib import Path
import random


# The ANKI_MODEL definition remains exactly the same as before.
# (I'm omitting it here for brevity, but you would copy the full model definition from the previous answer)
ANKI_MODEL = genanki.Model(
        random.randrange(1 << 63),  # New unique ID for the updated model
        'TOEFL Vocabulary Model - Styled',
        fields=[
            {'name': 'Word'},
            {'name': 'Word_Audio'},
            {'name': 'Part_of_Speech'},
            {'name': 'Meaning_Definition'},
            {'name': 'Meaning_Definition_Audio'},
            {'name': 'Antonyms'},
            {'name': 'Examples'},
            {'name': 'Related_Words_Notes'},
            {'name': 'Related_Words_Notes_Audio'},
        ],
        templates=[
            {
                'name': 'Card 1',
                'qfmt': '''
                    <div class="card-front">
                        <div class="word">{{Word}}</div>
                        <div class="audio">{{Word_Audio}}</div>
                    </div>
                ''',
                # --- CHANGE IS HERE: Added "meaning-label" class ---
                'afmt': '''
                    <div class="card-back">
                        <div class="front-word">{{Word}} {{Word_Audio}}</div>
                        <hr>
                        <div class="section">
                            <div class="label meaning-label">Meaning / Definition:</div>
                            <div class="content">{{Meaning_Definition}} {{Meaning_Definition_Audio}}</div>
                        </div>

                        {{#Antonyms}}
                        <div class="section">
                            <div class="label">Antonym(s):</div>
                            <div class="content antonym">{{Antonyms}}</div>
                        </div>
                        {{/Antonyms}}

                        {{#Related_Words_Notes}}
                        <div class="section">
                            <div class="label">Related Words / Notes:</div>
                            <div class="content">{{Related_Words_Notes}} {{Related_Words_Notes_Audio}}</div>
                        </div>
                        {{/Related_Words_Notes}}

                        <div class="section">
                            <div class="label">Examples:</div>
                            <div class="examples">{{Examples}}</div>
                        </div>
                    </div>
                ''',
            },
        ],
        # --- ALL CSS STYLING CHANGES ARE HERE ---
        css='''
            .card {
                font-family: Arial, sans-serif;
                font-size: 22px;
                text-align: center; /* Center all content by default */
                color: #f0f0f0; /* Light grey default text for dark background */
                background-color: #2c2c2c; /* Dark background color */
            }
            .card-front .word {
                font-size: 52px;
                font-weight: bold;
                margin-bottom: 20px;
                color: #FFFFFF; /* White word color */
            }
            .card-back .front-word {
                font-size: 36px;
                font-weight: bold;
                margin-bottom: 10px;
                color: #FFFFFF; /* White word color */
            }
            hr {
                border-color: #555;
            }
            .section {
                margin-bottom: 20px;
            }
            .label {
                font-weight: bold;
                color: #ccc; /* Light grey for labels */
                font-size: 18px;
                margin-bottom: 5px;
            }
            .content, .examples {
                line-height: 1.5;
            }
            .examples {
                white-space: pre-wrap;
                color: #89cff0; /* A nice light blue for examples */
            }
            .synonym {
                color: #28a745; /* Green for synonyms */
                font-weight: 500;
            }
            .antonym {
                color: #dc3545; /* Red for antonyms */
                font-weight: 500;
            }
            .meaning-label {
                color: #88d8b0; /* Light Green for "Meaning / Definition" label */
            }
        '''
    )

def create_anki_deck(csv_folder, audio_folder, output_filename, deck_name_prefix):
    """
    Creates an Anki deck from CSV files and their corresponding audio.
    """
    package = genanki.Package([])
    media_files = []

    csv_files = sorted(Path(csv_folder).glob('Ch*.csv'))
    if not csv_files:
        print("No CSV files found to build the deck.")
        return

    for csv_file in csv_files:
        chapter_num = int(csv_file.stem.replace('Ch', ''))
        subdeck_name = f"{deck_name_prefix}::Chapter {chapter_num}"
        # Using a hash of the name for a more robust unique ID
        subdeck_id = abs(hash(subdeck_name)) % (10**10)
        subdeck = genanki.Deck(deck_id=subdeck_id, name=subdeck_name)

        with open(csv_file, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader):
                if not row.get('Word'):
                    continue

                # Prepare fields for the Anki note
                fields = {
                    'Word': str(row.get('Word', '')).strip(),
                    'Part_of_Speech': str(row.get('Part of Speech', '')).strip(),
                    'Meaning_Definition': str(row.get('Meaning Definition', '')).strip(),
                    'Antonyms': str(row.get('Antonym', '')).strip(),
                    'Examples': str(row.get('Examples', '')).strip().replace('\n', '<br>'),
                    'Related_Words_Notes': str(row.get('Related Words Notes', '')).strip(),
                }

                # Map audio files to their corresponding fields
                audio_mapping = {
                    'Word_Audio': f"ch{chapter_num}_{idx}_Word.mp3",
                    'Meaning_Definition_Audio': f"ch{chapter_num}_{idx}_Meaning_Definition.mp3",
                    'Related_Words_Notes_Audio': f"ch{chapter_num}_{idx}_Related_Words_Notes.mp3",
                }

                for field_name, file_name in audio_mapping.items():
                    audio_path = os.path.join(audio_folder, file_name)
                    if os.path.exists(audio_path):
                        media_files.append(audio_path)
                        fields[field_name] = f"[sound:{file_name}]"
                    else:
                        fields[field_name] = ''

                # Create the note
                note = genanki.Note(
                    model=ANKI_MODEL,
                    fields=[
                        fields.get('Word', ''), fields.get('Word_Audio', ''),
                        fields.get('Part_of_Speech', ''), fields.get('Meaning_Definition', ''),
                        fields.get('Meaning_Definition_Audio', ''), fields.get('Antonyms', ''),
                        fields.get('Examples', ''), fields.get('Related_Words_Notes', ''),
                        fields.get('Related_Words_Notes_Audio', '')
                    ]
                )
                subdeck.add_note(note)

        package.decks.append(subdeck)

    # Add all unique media files to the package
    package.media_files = list(set(media_files))
    package.write_to_file(output_filename)
    print(f"\n✅ Deck exported successfully to '{output_filename}' with {len(package.decks)} sub-decks.")