# anki_deck_generator.py

import os
import csv
import json
import genanki
from pathlib import Path
import random

import os
import json
import csv
from pathlib import Path
import genanki

class AnkiDeckGenerator:
    """
    Generates Anki decks from CSV files with a structure defined by a JSON file.
    It handles merged rows and dynamically maps audio files.
    """

    def __init__(self, json_structure_path, key_column, css):
        """
        Initializes the AnkiDeckGenerator.
        """
        with open(json_structure_path, 'r', encoding='utf-8') as f:
            self.structure = json.load(f)
        self.key_column = key_column
        self.css = css
        self.model = self._create_dynamic_model()

    def _create_dynamic_model(self):
        """
        Dynamically creates a genanki.Model based on the JSON structure.
        (This version adds titles/labels to the front of the card).
        """
        all_fields = set()
        for side in ['front', 'back']:
            for item in self.structure.get(side, []):
                all_fields.add(item['type'])

        model_fields = []
        for field_name in sorted(list(all_fields)):
            sanitized_name = field_name.replace(' ', '_')
            model_fields.append({'name': sanitized_name})
            has_audio = any(
                item.get('audio') and item.get('type') == field_name
                for side in ['front', 'back']
                for item in self.structure.get(side, [])
            )
            if has_audio:
                model_fields.append({'name': f"{sanitized_name}_Audio"})

        # --- Generate qfmt (Front Template) - UPDATED FOR LABELS ---
        qfmt = '<div class="card-front">\n'
        for item in self.structure.get('front', []):
            field_type = item['type'] # This is our title/label
            sanitized_name = field_type.replace(' ', '_')
            
            # Create a container for each item on the front
            qfmt += '    <div class="front-section">\n'
            # Add the label
            qfmt += f'        <div class="front-label">{field_type}</div>\n'
            # Add the content
            qfmt += f'        <div class="front-content {sanitized_name.lower()}">{{{{{sanitized_name}}}}}</div>\n'
            # Add the audio if it exists
            if item.get('audio'):
                qfmt += f'        <div class="audio">{{{{{sanitized_name}_Audio}}}}</div>\n'
            qfmt += '    </div>\n'
        qfmt += '</div>'


        # --- Generate afmt (Back Template) - No changes needed here ---
        afmt = '<div class="card-back">\n'
        afmt += '    <div class="front-word">{{FrontSide}}</div>\n'
        afmt += '    <hr>\n'
        for item in self.structure.get('back', []):
            field_type = item['type']
            sanitized_name = field_type.replace(' ', '_')
            label = field_type
            
            opening_tag = '{{#' + sanitized_name + '}}'
            closing_tag = '{{/' + sanitized_name + '}}'
            content_field = '{{' + sanitized_name + '}}'

            afmt += f'    {opening_tag}\n'
            afmt += '    <div class="section">\n'
            afmt += f'        <div class="label">{label}:</div>\n'
            afmt += f'        <div class="content">{content_field}'
            if item.get('audio'):
                audio_field = '{{' + sanitized_name + '_Audio}}'
                afmt += f' {audio_field}'
            afmt += '</div>\n'
            afmt += '    </div>\n'
            afmt += f'    {closing_tag}\n'
        afmt += '</div>'


        model_id = abs(hash(json.dumps(self.structure, sort_keys=True) + self.css)) % (1 << 63)
        
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
        (This method is rewritten for clarity and correctness)
        """
        # Step 1: Split all relevant columns into lists of values
        split_data = {}
        max_parts = 1
        for key, value in row.items():
            if key != self.key_column and value:
                parts = [p.strip() for p in value.split('#')]
                split_data[key] = parts
                max_parts = max(max_parts, len(parts))
            else:
                # Store even the key_column and empty values
                split_data[key] = [value.strip() if value else ""]

        # Step 2: Create the list of final rows for cards
        processed_rows = []
        for i in range(max_parts):
            new_row = {}
            # The key_column value is the same for all split cards
            new_row[self.key_column] = split_data[self.key_column][0]

            for key, values in split_data.items():
                if key == self.key_column:
                    continue # Already handled
                
                # If the list of values for this key has an item at the current index, use it.
                # Otherwise, use an empty string. This prevents data duplication.
                if i < len(values):
                    new_row[key] = values[i]
                else:
                    new_row[key] = ''
            processed_rows.append(new_row)
            
        return processed_rows

    def generate_deck(self, csv_folder, audio_folder, output_filename, deck_name_prefix):
        """
        Generates the complete Anki deck package.
        - If multiple CSVs exist, creates a sub-deck for each CSV file.
        - If only one CSV exists, creates a single main deck.
        """
        # This method was already well-structured and required no changes.
        # The fixes in the other methods will resolve the deck generation issues.
        package = genanki.Package([])
        media_files = set()

        csv_files = sorted(Path(csv_folder).glob('*.csv'))
        
        if not csv_files:
            print("No CSV files found to build the deck.")
            return

        is_single_deck = len(csv_files) == 1
        
        if is_single_deck:
            deck_name = deck_name_prefix
            deck = genanki.Deck(abs(hash(deck_name)) % (10**10), deck_name)
            self._populate_deck(deck, csv_files[0], audio_folder, media_files)
            package.decks.append(deck)
            print(f"Found one CSV file. Building single deck: '{deck_name}'")
        else:
            print(f"Found {len(csv_files)} CSV files. Building sub-decks...")
            for csv_file in csv_files:
                subdeck_name = f"{deck_name_prefix}::{csv_file.stem}"
                subdeck = genanki.Deck(abs(hash(subdeck_name)) % (10**10), subdeck_name)
                self._populate_deck(subdeck, csv_file, audio_folder, media_files)
                package.decks.append(subdeck)
                print(f"- Created sub-deck: '{subdeck_name}'")

        package.media_files = list(media_files)
        package.write_to_file(output_filename)
        
        num_decks = len(package.decks)
        deck_type = "sub-deck" if not is_single_deck else "deck"
        if not is_single_deck:
            deck_type += "s"
            
        print(f"\n✅ Deck exported successfully to '{output_filename}' with {num_decks} {deck_type}.")

    def _populate_deck(self, deck, csv_file, audio_folder, media_files):
        """Helper function to process a single CSV and add notes to a deck."""
        with open(csv_file, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row_idx, row in enumerate(reader, 1):
                if not row.get(self.key_column):
                    continue

                processed_rows = self._process_row(row)

                for part_num, processed_row in enumerate(processed_rows, 1):
                    note_fields = []
                    for model_field in self.model.fields:
                        field_name = model_field['name']
                        
                        if field_name.endswith('_Audio'):
                            base_name = field_name[:-6]
                            audio_filename = f"{csv_file.stem}_r{row_idx}_c{base_name}_p{part_num}.mp3"
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
                    deck.add_note(note)
