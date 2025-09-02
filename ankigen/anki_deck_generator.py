# anki_deck_generator.py

import os
import csv
import json
import genanki
from pathlib import Path
import random

class AnkiDeckGenerator:
    """
    Generates Anki decks from CSV files with a structure defined by a JSON file.
    It handles merged rows and dynamically maps audio files.
    """

    def __init__(self, json_structure_path, key_column, css):
        """
        Initializes the AnkiDeckGenerator.

        Args:
            json_structure_path (str): Path to the JSON file defining the card structure.
            key_column (str): The column name in the CSV that should not be split (e.g., 'Word').
            css (str): The CSS styling for the Anki cards.
        """
        with open(json_structure_path, 'r', encoding='utf-8') as f:
            self.structure = json.load(f)
        self.key_column = key_column
        self.css = css
        self.model = self._create_dynamic_model()

    def _create_dynamic_model(self):
        """
        Dynamically creates a genanki.Model based on the JSON structure.
        """
        all_fields = set()
        for side in ['front', 'back']:
            for item in self.structure.get(side, []):
                all_fields.add(item['type'])

        model_fields = []
        for field_name in sorted(list(all_fields)): # Sort for consistent order
            # Sanitize field name for Anki (replace spaces)
            sanitized_name = field_name.replace(' ', '_')
            model_fields.append({'name': sanitized_name})
            # Check if any use of this field requires audio
            has_audio = any(
                item.get('audio') and item.get('type') == field_name
                for side in ['front', 'back']
                for item in self.structure.get(side, [])
            )
            if has_audio:
                model_fields.append({'name': f"{sanitized_name}_Audio"})

        # Generate qfmt (Front Template)
        qfmt = '<div class="card-front">\n'
        for item in self.structure.get('front', []):
            field_type = item['type']
            sanitized_name = field_type.replace(' ', '_')
            qfmt += f'    <div class="{sanitized_name.lower()}">{{{{{sanitized_name}}}}}</div>\n'
            if item.get('audio'):
                qfmt += f'    <div class="audio">{{{{{sanitized_name}_Audio}}}}</div>\n'
        qfmt += '</div>'

        # Generate afmt (Back Template)
        afmt = '<div class="card-back">\n'
        afmt += '    <div class="front-word">{{FrontSide}}</div>\n'
        afmt += '    <hr>\n'
        for item in self.structure.get('back', []):
            field_type = item['type']
            sanitized_name = field_type.replace(' ', '_')
            label = field_type # Use original name for label
            
            afmt += f'    {{#{{{sanitized_name}}}}}\n'
            afmt += '    <div class="section">\n'
            afmt += f'        <div class="label">{label}:</div>\n'
            afmt += f'        <div class="content">{{{{{sanitized_name}}}}}'
            if item.get('audio'):
                afmt += f' {{{{Audio}}}}' # Note: Simplified audio handling on back
            afmt += '</div>\n'
            afmt += '    </div>\n'
            afmt += f'    {{/{{{sanitized_name}}}}}\n'
        afmt += '</div>'


        model_id = abs(hash(json.dumps(self.structure) + self.css)) % (1 << 63)
        
        return genanki.Model(
            model_id,
            'Dynamic Vocabulary Model',
            fields=model_fields,
            templates=[{
                'name': 'Dynamic Card',
                'qfmt': qfmt,
                'afmt': afmt,
            }],
            css=self.css
        )

    def _process_row(self, row):
        """
        Processes a single CSV row, splitting merged data into multiple note definitions.

        Returns:
            list[dict]: A list of dictionaries, where each dict represents one card.
        """
        split_data = {}
        max_parts = 1
        for key, value in row.items():
            if key != self.key_column and value:
                parts = value.split('#')
                split_data[key] = [p.strip() for p in parts]
                if len(parts) > max_parts:
                    max_parts = len(parts)
            else:
                # For the key column or empty columns, we don't split
                split_data[key] = [value.strip() if value else ""]

        # Pad shorter lists and duplicate the key column
        for key, values in split_data.items():
            if key == self.key_column:
                split_data[key] = values * max_parts
            else:
                current_len = len(values)
                if current_len < max_parts:
                    split_data[key].extend([''] * (max_parts - current_len))
        
        # Transpose the data from a dict of lists to a list of dicts
        processed_rows = []
        for i in range(max_parts):
            new_row = {key: values[i] for key, values in split_data.items()}
            processed_rows.append(new_row)
            
        return processed_rows

    def generate_deck(self, csv_folder, audio_folder, output_filename, deck_name_prefix):
        """
        Generates the complete Anki deck package.
        """
        package = genanki.Package([])
        media_files = set()

        csv_files = sorted(Path(csv_folder).glob('Ch*.csv'))
        
        if not csv_files:
            print("No CSV files found to build the deck.")
            return

        for csv_file in csv_files:
            chapter_num = int(csv_file.stem.replace('Ch', ''))
            subdeck_name = f"{deck_name_prefix}::Chapter {chapter_num}"
            subdeck_id = abs(hash(subdeck_name)) % (10**10)
            subdeck = genanki.Deck(deck_id=subdeck_id, name=subdeck_name)

            with open(csv_file, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row_idx, row in enumerate(reader):
                    if not row.get(self.key_column):
                        continue

                    processed_rows = self._process_row(row)

                    for part_num, processed_row in enumerate(processed_rows, 1):
                        note_fields = []
                        # Iterate in the same order as model fields were created
                        for model_field in self.model.fields:
                            field_name = model_field['name']
                            
                            if field_name.endswith('_Audio'):
                                base_name = field_name[:-6] # Remove '_Audio'
                                original_col_name = base_name.replace('_', ' ')
                                
                                audio_filename = f"ch{chapter_num}_r{row_idx}_c{base_name}_p{part_num}.mp3"
                                audio_path = os.path.join(audio_folder, audio_filename)
                                
                                if os.path.exists(audio_path):
                                    media_files.add(audio_path)
                                    note_fields.append(f"[sound:{audio_filename}]")
                                else:
                                    note_fields.append('')
                            else:
                                original_col_name = field_name.replace('_', ' ')
                                note_fields.append(processed_row.get(original_col_name, ''))
                        
                        note = genanki.Note(model=self.model, fields=note_fields)
                        subdeck.add_note(note)

            package.decks.append(subdeck)

        package.media_files = list(media_files)
        package.write_to_file(output_filename)
        print(f"\n✅ Deck exported successfully to '{output_filename}' with {len(package.decks)} sub-decks.")


# --- Main Execution ---
if __name__ == '__main__':
    # --- Configuration ---
    CSV_FOLDER = 'path/to/your/csv_files'
    AUDIO_FOLDER = 'path/to/your/audio_files'
    JSON_STRUCTURE_FILE = 'path/to/your/structure.json'
    OUTPUT_FILENAME = 'TOEFL_Vocabulary_Deck.apkg'
    DECK_NAME_PREFIX = 'TOEFL Vocabulary'
    KEY_COLUMN = 'Word' # The column that identifies a unique entry

    # --- Card Styling (CSS) ---
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

    # --- Create and run the generator ---
    # Ensure paths exist before running
    if not all(os.path.exists(p) for p in [CSV_FOLDER, AUDIO_FOLDER, JSON_STRUCTURE_FILE]):
        print("Error: One or more required paths (CSV folder, Audio folder, JSON file) do not exist.")
        print("Please create placeholder folders and the JSON file before running.")
    else:
        generator = AnkiDeckGenerator(
            json_structure_path=JSON_STRUCTURE_FILE,
            key_column=KEY_COLUMN,
            css=CARD_CSS
        )
        generator.generate_deck(
            csv_folder=CSV_FOLDER,
            audio_folder=AUDIO_FOLDER,
            output_filename=OUTPUT_FILENAME,
            deck_name_prefix=DECK_NAME_PREFIX
        )

# # In anki_deck_generator.py

# import os
# import csv
# import genanki
# from pathlib import Path
# import random


# ANKI_MODEL = genanki.Model(
#         random.randrange(1 << 63),  # New unique ID for the updated model
#         'TOEFL Vocabulary Model - Styled',
#         fields=[
#             {'name': 'Word'},
#             {'name': 'Word_Audio'},
#             {'name': 'Part_of_Speech'},
#             {'name': 'Meaning_Definition'},
#             {'name': 'Meaning_Definition_Audio'},
#             {'name': 'Antonyms'},
#             {'name': 'Examples'},
#             {'name': 'Related_Words_Notes'},
#             {'name': 'Related_Words_Notes_Audio'},
#         ],
#         templates=[
#             {
#                 'name': 'Card 1',
#                 'qfmt': '''
#                     <div class="card-front">
#                         <div class="word">{{Word}}</div>
#                         <div class="audio">{{Word_Audio}}</div>
#                     </div>
#                 ''',

#                 'afmt': '''
#                     <div class="card-back">
#                         <div class="front-word">{{Word}} {{Word_Audio}}</div>
#                         <hr>
#                         <div class="section">
#                             <div class="label meaning-label">Meaning / Definition:</div>
#                             <div class="content">{{Meaning_Definition}} {{Meaning_Definition_Audio}}</div>
#                         </div>

#                         {{#Antonyms}}
#                         <div class="section">
#                             <div class="label">Antonym(s):</div>
#                             <div class="content antonym">{{Antonyms}}</div>
#                         </div>
#                         {{/Antonyms}}

#                         {{#Related_Words_Notes}}
#                         <div class="section">
#                             <div class="label">Related Words / Notes:</div>
#                             <div class="content">{{Related_Words_Notes}} {{Related_Words_Notes_Audio}}</div>
#                         </div>
#                         {{/Related_Words_Notes}}

#                         <div class="section">
#                             <div class="label">Examples:</div>
#                             <div class="examples">{{Examples}}</div>
#                         </div>
#                     </div>
#                 ''',
#             },
#         ],
#         # --- ALL CSS STYLING CHANGES ARE HERE ---
#         css='''
#             .card {
#                 font-family: Arial, sans-serif;
#                 font-size: 22px;
#                 text-align: center; /* Center all content by default */
#                 color: #f0f0f0; /* Light grey default text for dark background */
#                 background-color: #2c2c2c; /* Dark background color */
#             }
#             .card-front .word {
#                 font-size: 52px;
#                 font-weight: bold;
#                 margin-bottom: 20px;
#                 color: #FFFFFF; /* White word color */
#             }
#             .card-back .front-word {
#                 font-size: 36px;
#                 font-weight: bold;
#                 margin-bottom: 10px;
#                 color: #FFFFFF; /* White word color */
#             }
#             hr {
#                 border-color: #555;
#             }
#             .section {
#                 margin-bottom: 20px;
#             }
#             .label {
#                 font-weight: bold;
#                 color: #ccc; /* Light grey for labels */
#                 font-size: 18px;
#                 margin-bottom: 5px;
#             }
#             .content, .examples {
#                 line-height: 1.5;
#             }
#             .examples {
#                 white-space: pre-wrap;
#                 color: #89cff0; /* A nice light blue for examples */
#             }
#             .synonym {
#                 color: #28a745; /* Green for synonyms */
#                 font-weight: 500;
#             }
#             .antonym {
#                 color: #dc3545; /* Red for antonyms */
#                 font-weight: 500;
#             }
#             .meaning-label {
#                 color: #88d8b0; /* Light Green for "Meaning / Definition" label */
#             }
#         '''
#     )

# def create_anki_deck(csv_folder, audio_folder, output_filename, deck_name_prefix):
#     """
#     Creates an Anki deck from CSV files and their corresponding audio.
#     """
#     package = genanki.Package([])
#     media_files = []

#     csv_files = sorted(Path(csv_folder).glob('Ch*.csv'))
#     if not csv_files:
#         print("No CSV files found to build the deck.")
#         return

#     for csv_file in csv_files:
#         chapter_num = int(csv_file.stem.replace('Ch', ''))
#         subdeck_name = f"{deck_name_prefix}::Chapter {chapter_num}"
#         # Using a hash of the name for a more robust unique ID
#         subdeck_id = abs(hash(subdeck_name)) % (10**10)
#         subdeck = genanki.Deck(deck_id=subdeck_id, name=subdeck_name)

#         with open(csv_file, newline='', encoding='utf-8') as f:
#             reader = csv.DictReader(f)
#             for idx, row in enumerate(reader):
#                 if not row.get('Word'):
#                     continue

#                 # Prepare fields for the Anki note
#                 fields = {
#                     'Word': str(row.get('Word', '')).strip(),
#                     'Part_of_Speech': str(row.get('Part of Speech', '')).strip(),
#                     'Meaning_Definition': str(row.get('Meaning Definition', '')).strip(),
#                     'Antonyms': str(row.get('Antonym', '')).strip(),
#                     'Examples': str(row.get('Examples', '')).strip().replace('\n', '<br>'),
#                     'Related_Words_Notes': str(row.get('Related Words Notes', '')).strip(),
#                 }

#                 # Map audio files to their corresponding fields
#                 audio_mapping = {
#                     'Word_Audio': f"ch{chapter_num}_{idx}_Word.mp3",
#                     'Meaning_Definition_Audio': f"ch{chapter_num}_{idx}_Meaning_Definition.mp3",
#                     'Related_Words_Notes_Audio': f"ch{chapter_num}_{idx}_Related_Words_Notes.mp3",
#                 }

#                 for field_name, file_name in audio_mapping.items():
#                     audio_path = os.path.join(audio_folder, file_name)
#                     if os.path.exists(audio_path):
#                         media_files.append(audio_path)
#                         fields[field_name] = f"[sound:{file_name}]"
#                     else:
#                         fields[field_name] = ''

#                 # Create the note
#                 note = genanki.Note(
#                     model=ANKI_MODEL,
#                     fields=[
#                         fields.get('Word', ''), fields.get('Word_Audio', ''),
#                         fields.get('Part_of_Speech', ''), fields.get('Meaning_Definition', ''),
#                         fields.get('Meaning_Definition_Audio', ''), fields.get('Antonyms', ''),
#                         fields.get('Examples', ''), fields.get('Related_Words_Notes', ''),
#                         fields.get('Related_Words_Notes_Audio', '')
#                     ]
#                 )
#                 subdeck.add_note(note)

#         package.decks.append(subdeck)

#     # Add all unique media files to the package
#     package.media_files = list(set(media_files))
#     package.write_to_file(output_filename)
#     print(f"\n✅ Deck exported successfully to '{output_filename}' with {len(package.decks)} sub-decks.")