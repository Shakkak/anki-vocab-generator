import os
import re
import csv
import json
import genanki
from pathlib import Path


class AnkiDeckGenerator:
    """
    Generates Anki decks from CSV files with a structure defined by a JSON file.
    Supports merged CSV rows (merge_duplicates=True), producing a single card
    whose back side repeats all split segments separated by "-----------".

    Audio filename format (exact, literal column names included):
        ch{chapter}_r{row}_c{Column Name}_p{part}.mp3

    Chapter is extracted from the CSV filename (first integer found in the stem).
    Example: "Ch3.csv" or "chapter3.csv" -> chapter = 3

    Behavior:
      - merge_mode (merge_duplicates=True) -> one Note per merged CSV row; MergedBack
        contains repeated blocks for each split part with inline [sound:...] tags.
      - merge_mode False -> one Note per split part; dedicated *_Audio fields populated.
      - Empty values are skipped (no label/title shown).
      - Autoplay: the template includes a small JS that will try to click Anki's
        generated sound links / replay buttons (broad approach, doesn't require a
        special "de_audio" field). This mimics the snippet you referenced but is
        applied globally so it's robust.
    """

    def __init__(self, json_structure_path, key_column, css, include_front_on_back=True, merge_duplicates=False):
        with open(json_structure_path, "r", encoding="utf-8") as f:
            self.structure = json.load(f)

        self.key_column = key_column
        self.css = css
        self.include_front_on_back = include_front_on_back
        self.merge_mode = merge_duplicates

        self.model = self._create_dynamic_model()

    # -----------------------
    # Helpers
    # -----------------------
    def _side_has_autoplay(self, side_items):
        return any(item.get("autoplay") for item in side_items)

    def _extract_chapter_from_filename(self, csv_path: Path):
        """
        Extract first integer from the csv filename stem to use as chapter.
        Defaults to 1 if not found.
        """
        stem = csv_path.stem
        m = re.search(r"(\d+)", stem)
        if m:
            return int(m.group(1))
        return 1

    def _find_audio_exact(self, audio_folder, filename):
        """
        Check if the exact filename exists in audio_folder.
        Returns full path or None.
        """
        path = os.path.join(audio_folder, filename)
        if os.path.exists(path):
            return path
        return None

    # -----------------------
    # Build dynamic model
    # -----------------------
    def _create_dynamic_model(self):
        """
        Build genanki.Model according to the JSON structure.
        Uses mustache conditionals so empty fields don't show their labels.
        Adds autoplay JS that attempts to click the first sound link / replaybutton
        or play HTML5 audio elements sequentially.
        """
        # The model MUST contain all possible fields.
        # So we scan both front and back to find all fields that EVER need an _Audio companion.
        all_items = self.structure.get("front", []) + self.structure.get("back", [])
        unique_field_names = sorted(list(set(item["type"] for item in all_items)))

        model_fields = []
        for field_name in unique_field_names:
            sanitized = field_name.replace(" ", "_")
            model_fields.append({"name": sanitized})
            # If any definition of a field needs audio, create the audio field for it.
            if any(item.get("audio") and item.get("type") == field_name for item in all_items):
                model_fields.append({"name": sanitized + "_Audio"})

        # The MergedBack field is only needed for merge_mode
        if self.merge_mode:
            model_fields.append({"name": "MergedBack"})

        # Autoplay flag detection
        front_autoplay = self._side_has_autoplay(self.structure.get("front", []))
        back_autoplay = self._side_has_autoplay(self.structure.get("back", []))

        autoplay_js = (
            "<script>\n"
            "  setTimeout(function() {\n"
            "    try {\n"
            "      var elem = document.querySelector('#autoplay .soundLink, #autoplay .replaybutton');\n"
            "      if (elem) {\n"
            "        elem.click();\n"
            "      }\n"
            "    } catch (e) { /* ignore */ }\n"
            "  }, 10);\n"
            "</script>\n"
        )

        # ---------------- FRONT TEMPLATE ----------------
        # The template, unlike the model, must be specific.
        # It only includes an audio field if the JSON for THIS SIDE says so.
        qfmt = '<div class="card-front">\n'
        for item in self.structure.get("front", []):
            ftype = item["type"]
            sanitized = ftype.replace(" ", "_")
            open_tag = "{{#" + sanitized + "}}"
            close_tag = "{{/" + sanitized + "}}"
            content = "{{" + sanitized + "}}"
            # BUG FIX: Check the item specific to this side (front).
            if item.get("audio"):
                content += " {{" + sanitized + "_Audio}}"

            autoplay_id = ' id="autoplay"' if item.get("autoplay") else ""
            qfmt += f"    {open_tag}\n"
            qfmt += "    <div class=\"front-section\">\n"
            qfmt += f"        <div class=\"front-label\">{ftype}</div>\n"
            qfmt += f'        <div{autoplay_id} class="front-content {sanitized.lower()}">{content}</div>\n'
            qfmt += "    </div>\n"
            qfmt += f"    {close_tag}\n"

        if front_autoplay:
            qfmt += autoplay_js
        qfmt += "</div>"

        # ---------------- BACK TEMPLATE ----------------
        if self.merge_mode:
            afmt = "<div class=\"card-back\">\n"
            afmt += "    {{FrontSide}}\n"
            afmt += "    <hr>\n"
            afmt += "    {{MergedBack}}\n"
            if back_autoplay:
                afmt += autoplay_js
            afmt += "</div>"
        else: # Normal mode
            afmt = "<div class=\"card-back\">\n"
            if self.include_front_on_back:
                afmt += "    {{FrontSide}}\n"
                afmt += "    <hr>\n"

            for item in self.structure.get("back", []):
                ftype = item["type"]
                sanitized = ftype.replace(" ", "_")
                open_tag = "{{#" + sanitized + "}}"
                close_tag = "{{/" + sanitized + "}}"
                content = "{{" + sanitized + "}}"
                # BUG FIX: Check the item specific to this side (back).
                if item.get("audio"):
                    content += " {{" + sanitized + "_Audio}}"

                autoplay_id = ' id="autoplay"' if item.get("autoplay") else ""
                afmt += f"    {open_tag}\n"
                afmt += "    <div class=\"front-section\">\n"
                afmt += f"        <div class=\"front-label\">{ftype}</div>\n"
                afmt += f'        <div{autoplay_id} class="front-content {sanitized.lower()}">{content}</div>\n'
                afmt += "    </div>\n"
                afmt += f"    {close_tag}\n"

            if back_autoplay:
                afmt += autoplay_js
            afmt += "</div>"

        model_id = abs(hash(json.dumps(self.structure, sort_keys=True) + self.css)) % (1 << 63)
        return genanki.Model(
            model_id, "Dynamic Vocabulary Model", fields=model_fields,
            templates=[{"name": "Dynamic Card", "qfmt": qfmt, "afmt": afmt}],
            css=self.css
        )

    # -----------------------
    # Process (split) a CSV row
    # -----------------------
    def _process_row(self, row):
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
                if key == self.key_column: continue
                new_r[key] = values[i] if i < len(values) else ""
            processed.append(new_r)
        return processed

    # -----------------------
    # Generate deck package
    # -----------------------
    def generate_deck(self, csv_folder, audio_folder, output_filename, deck_name_prefix):
        package = genanki.Package([])
        media_files = set()

        csv_files = sorted(Path(csv_folder).glob("*.csv"))
        if not csv_files:
            print("No CSVs found.")
            return

        deck_list = []
        if len(csv_files) == 1:
            deck_name = deck_name_prefix
            deck = genanki.Deck(abs(hash(deck_name)) % (10**10), deck_name)
            self._populate_deck(deck, csv_files[0], audio_folder, media_files)
            deck_list.append(deck)
        else:
            for csv_file in csv_files:
                sdname = f"{deck_name_prefix}::{csv_file.stem}"
                subdeck = genanki.Deck(abs(hash(sdname)) % (10**10), sdname)
                self._populate_deck(subdeck, csv_file, audio_folder, media_files)
                deck_list.append(subdeck)
        
        package.decks.extend(deck_list)
        package.media_files = list(media_files)
        package.write_to_file(output_filename)
        print(f"✅ Wrote {output_filename} (media files: {len(package.media_files)})")

    # -----------------------
    # Populate a deck from one CSV
    # -----------------------
    def _populate_deck(self, deck, csv_file: Path, audio_folder, media_files: set):
        """
        csv_file is a Path so we can extract chapter number from its stem.
        """
        chapter = self._extract_chapter_from_filename(csv_file)

        with open(csv_file, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row_idx, row in enumerate(reader, 1):
                if not row.get(self.key_column):
                    continue

                processed_rows = self._process_row(row)

                if self.merge_mode:
                    blocks = []
                    for part_index, prow in enumerate(processed_rows, 1):
                        block_html_items = []
                        # Build the merged back using only the "back" definition
                        for item in self.structure.get("back", []):
                            ftype = item["type"]

                            # Logic to include the key_column only ONCE on the back
                            if ftype == self.key_column and part_index > 1:
                                continue

                            sanitized = ftype.replace(" ", "_")
                            value = (prow.get(ftype, "") or "").strip()

                            if not value:
                                continue

                            audio_tag = ""
                            # BUG FIX: Add audio inline based on THIS item's property.
                            if item.get("audio"):
                                audio_filename = f"ch{chapter}_r{row_idx}_c{ftype}_p{part_index}.mp3"
                                audio_path = os.path.join(audio_folder, audio_filename)
                                if os.path.exists(audio_path):
                                    media_files.add(audio_path)
                                    audio_tag = " [sound:" + audio_filename + "]"
                                else:
                                    print(f"⚠️ Missing audio: {audio_path}")
                            
                            autoplay_id = ' id="autoplay"' if item.get("autoplay") else ""

                            block_html = (
                                f'<div class="front-section">\n'
                                f'  <div class="front-label">{ftype}</div>\n'
                                f'  <div{autoplay_id} class="front-content {sanitized.lower()}">{value}{audio_tag}</div>\n'
                                '</div>'
                            )
                            block_html_items.append(block_html)

                        if block_html_items:
                            blocks.append("\n".join(block_html_items))

                    merged_html = "\n-----------\n".join(blocks)

                    # Build the note fields. In merge_mode, ALL _Audio fields are empty
                    # because all audio is rendered inline in the MergedBack field.
                    note_fields = []
                    for mf in self.model.fields:
                        name = mf["name"]
                        if name == "MergedBack":
                            note_fields.append(merged_html)
                        elif name.endswith("_Audio"):
                            note_fields.append("")
                        else:
                            col = name.replace("_", " ")
                            note_fields.append(processed_rows[0].get(col, ""))

                    note = genanki.Note(model=self.model, fields=note_fields)
                    deck.add_note(note)
                    continue

                # NORMAL MODE (unchanged):
                for part_num, prow in enumerate(processed_rows, 1):
                    note_fields = []
                    for mf in self.model.fields:
                        name = mf["name"]
                        if name.endswith("_Audio"):
                            base = name[:-6]
                            original_header = None
                            # Find the original header for this audio field
                            for item in all_items:
                                if item["type"].replace(" ", "_") == base:
                                    original_header = item["type"]
                                    break
                            if not original_header: original_header = base.replace("_", " ")

                            audio_filename = f"ch{chapter}_r{row_idx}_c{original_header}_p{part_num}.mp3"
                            audio_path = os.path.join(audio_folder, audio_filename)
                            if os.path.exists(audio_path):
                                media_files.add(audio_path)
                                note_fields.append(f"[sound:{audio_filename}]")
                            else:
                                note_fields.append("")
                        else:
                            col = name.replace("_", " ")
                            note_fields.append(prow.get(col, ""))

                    note = genanki.Note(model=self.model, fields=note_fields)
                    deck.add_note(note)