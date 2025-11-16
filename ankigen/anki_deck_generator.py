# anki_deck_generator.py

import os
import csv
import json
import genanki
from pathlib import Path


class AnkiDeckGenerator:
    """
    Generates Anki decks from CSV files with a structure defined by a JSON file.
    Supports merged CSV rows (merge_duplicates=True), producing a single card
    whose back side repeats all split segments separated by "-----------".
    """

    def __init__(self, json_structure_path, key_column, css, include_front_on_back=True, merge_duplicates=False):
        """
        merge_duplicates controls MERGED CARD MODE.
        If True → one card per merged CSV row, repeated blocks on card back.
        """
        with open(json_structure_path, 'r', encoding='utf-8') as f:
            self.structure = json.load(f)

        self.key_column = key_column
        self.css = css
        self.include_front_on_back = include_front_on_back

        # THIS IS THE KEY NEW FLAG
        self.merge_mode = merge_duplicates

        self.model = self._create_dynamic_model()

    # ----------------------------------------------------------
    # Utility: detect autoplay existence in JSON template
    # ----------------------------------------------------------
    def _side_has_autoplay(self, side_items):
        return any(item.get("autoplay") for item in side_items)

    # ----------------------------------------------------------
    # Create MODEL dynamically
    # ----------------------------------------------------------
    def _create_dynamic_model(self):
        """
        If merge_mode=False → normal behavior (individual fields per column)
        If merge_mode=True  → add "MergedBack" field and simplify back template
        """
        all_fields = set()

        # In merged mode, the back is replaced by one large field,
        # but the front stays normal.
        for item in self.structure.get("front", []):
            all_fields.add(item["type"])

        model_fields = []
        fields_with_audio = set()

        # FRONT fields have audio mapping as usual
        for field_name in sorted(list(all_fields)):
            sanitized = field_name.replace(" ", "_")
            model_fields.append({"name": sanitized})

            # add audio field if needed
            front_has_audio = any(
                item.get('audio') and item.get('type') == field_name
                for item in self.structure.get("front", [])
            )
            if front_has_audio:
                model_fields.append({"name": f"{sanitized}_Audio"})
                fields_with_audio.add(sanitized)

        # If merge card mode → add a single "MergedBack" field
        if self.merge_mode:
            model_fields.append({"name": "MergedBack"})
        else:
            # Normal mode → include all back fields as separate fields
            for item in self.structure.get("back", []):
                field_name = item["type"]
                sanitized = field_name.replace(" ", "_")
                if sanitized not in [f["name"] for f in model_fields]:
                    model_fields.append({"name": sanitized})

                if item.get("audio"):
                    model_fields.append({"name": f"{sanitized}_Audio"})
                    fields_with_audio.add(sanitized)

        # AUTOPLAY flags
        front_autoplay = self._side_has_autoplay(self.structure.get("front", []))
        back_autoplay = self._side_has_autoplay(self.structure.get("back", []))

        # ----------------------------------------------------------
        # FRONT TEMPLATE (same always)
        # ----------------------------------------------------------
        qfmt = '<div class="card-front">\n'
        for item in self.structure.get("front", []):
            ftype = item["type"]
            sanitized = ftype.replace(" ", "_")
            content = "{{" + sanitized + "}}"
            if sanitized in fields_with_audio:
                content += " {{%s_Audio}}" % sanitized

            qfmt += (
                '    <div class="front-section">\n'
                f'        <div class="front-label">{ftype}</div>\n'
                f'        <div class="front-content {sanitized.lower()}">{content}</div>\n'
                '    </div>\n'
            )

        if front_autoplay:
            qfmt += '    <span id="autoplay_front">{{de_audio}}</span>\n'

        qfmt += '</div>'

        # ----------------------------------------------------------
        # BACK TEMPLATE
        # ----------------------------------------------------------

        if self.merge_mode:
            # MERGED CARD MODE — simplified template
            afmt = '<div class="card-back">\n'
            afmt += '    {{FrontSide}}\n'
            afmt += '    <hr>\n'
            afmt += '    {{MergedBack}}\n'
            if back_autoplay:
                afmt += '    <span id="autoplay_back">{{de_audio}}</span>\n'
            afmt += '</div>'

        else:
            # NORMAL MODE — use JSON structure as usual
            afmt = '<div class="card-back">\n'
            if self.include_front_on_back:
                afmt += '    {{FrontSide}}\n'
                afmt += '    <hr>\n'

            for item in self.structure.get("back", []):
                ftype = item["type"]
                sanitized = ftype.replace(" ", "_")
                open_tag = "{{#" + sanitized + "}}"
                close_tag = "{{/" + sanitized + "}}"

                content = "{{" + sanitized + "}}"
                if sanitized in fields_with_audio:
                    content += " {{%s_Audio}}" % sanitized

                afmt += (
                    f'    {open_tag}\n'
                    '    <div class="front-section">\n'
                    f'        <div class="front-label">{ftype}</div>\n'
                    f'        <div class="front-content {sanitized.lower()}">{content}</div>\n'
                    '    </div>\n'
                    f'    {close_tag}\n'
                )

            if back_autoplay:
                afmt += '    <span id="autoplay_back">{{de_audio}}</span>\n'
            afmt += '</div>'

        # ----------------------------------------------------------
        # Return MODEL
        # ----------------------------------------------------------
        model_id = abs(hash(json.dumps(self.structure, sort_keys=True) + self.css)) % (1 << 63)

        return genanki.Model(
            model_id,
            "Dynamic Vocabulary Model",
            fields=model_fields,
            templates=[{
                "name": "Dynamic Card",
                "qfmt": qfmt,
                "afmt": afmt
            }],
            css=self.css
        )

    # ----------------------------------------------------------
    # Split merged cell values (same as before)
    # ----------------------------------------------------------
    def _process_row(self, row):
        """Return list of split row dictionaries."""
        split_data = {}
        max_parts = 1

        for key, value in row.items():
            if key != self.key_column and value:
                parts = [p.strip() for p in value.split("#")]
                split_data[key] = parts
                max_parts = max(max_parts, len(parts))
            else:
                split_data[key] = [value.strip() if value else ""]

        processed = []
        for i in range(max_parts):
            new_r = {}
            new_r[self.key_column] = split_data[self.key_column][0]

            for key, values in split_data.items():
                if key == self.key_column:
                    continue
                new_r[key] = values[i] if i < len(values) else ""
            processed.append(new_r)

        return processed

    # ----------------------------------------------------------
    # Generate DECK
    # ----------------------------------------------------------
    def generate_deck(self, csv_folder, audio_folder, output_filename, deck_name_prefix):
        package = genanki.Package([])
        media_files = set()

        csv_files = sorted(Path(csv_folder).glob("*.csv"))
        if not csv_files:
            print("No CSVs found.")
            return

        if len(csv_files) == 1:
            deck_name = deck_name_prefix
            deck = genanki.Deck(abs(hash(deck_name)) % (10**10), deck_name)
            self._populate_deck(deck, csv_files[0], audio_folder, media_files)
            package.decks.append(deck)
        else:
            for csv_file in csv_files:
                sdname = f"{deck_name_prefix}::{csv_file.stem}"
                subdeck = genanki.Deck(abs(hash(sdname)) % (10**10), sdname)
                self._populate_deck(subdeck, csv_file, audio_folder, media_files)
                package.decks.append(subdeck)

        package.media_files = list(media_files)
        package.write_to_file(output_filename)

    # ----------------------------------------------------------
    # Populate DECK with notes
    # ----------------------------------------------------------
    def _populate_deck(self, deck, csv_file, audio_folder, media_files):
        with open(csv_file, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row_idx, row in enumerate(reader, 1):
                if not row.get(self.key_column):
                    continue

                processed_rows = self._process_row(row)

                if self.merge_mode:
                    # ------------------------------------------------------
                    # MERGED CARD MODE (Option A)
                    # ONE NOTE per original CSV row
                    # ------------------------------------------------------
                    blocks = []
                    for prow in processed_rows:
                        block_html = []
                        for item in self.structure.get("back", []):
                            ftype = item["type"]
                            val = prow.get(ftype, "")
                            sanitized = ftype.replace(" ", "_")

                            html = (
                                '<div class="front-section">\n'
                                f'  <div class="front-label">{ftype}</div>\n'
                                f'  <div class="front-content {sanitized.lower()}">{val}</div>\n'
                                '</div>'
                            )
                            block_html.append(html)

                        blocks.append("\n".join(block_html))

                    merged_html = "\n-----------\n".join(blocks)

                    # Build fields for note
                    note_fields = []
                    for mf in self.model.fields:
                        name = mf["name"]
                        if name == "MergedBack":
                            note_fields.append(merged_html)
                        elif name.endswith("_Audio"):
                            base = name[:-6]
                            # DO NOT load audio for merged mode (left intact but blank)
                            note_fields.append("")
                        else:
                            col = name.replace("_", " ")
                            note_fields.append(processed_rows[0].get(col, ""))

                    note = genanki.Note(
                        model=self.model,
                        fields=note_fields
                    )
                    deck.add_note(note)
                    continue

                # ------------------------------------------------------
                # NORMAL MODE (unchanged)
                # ------------------------------------------------------
                for part_num, prow in enumerate(processed_rows, 1):
                    note_fields = []
                    for mf in self.model.fields:
                        name = mf["name"]

                        if name.endswith("_Audio"):
                            base = name[:-6]
                            audio_filename = f"ch{part_num}_r{row_idx}_c{base}_p{part_num}.mp3"
                            path = os.path.join(audio_folder, audio_filename)

                            if os.path.exists(path):
                                media_files.add(path)
                                note_fields.append(f"[sound:{audio_filename}]")
                            else:
                                note_fields.append("")
                        else:
                            col = name.replace("_", " ")
                            note_fields.append(prow.get(col, ""))

                    note = genanki.Note(model=self.model, fields=note_fields)
                    deck.add_note(note)
