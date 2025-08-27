import copy
import pandas as pd
from pathlib import Path
import json

def get_csv_headers(csv_folder):
    """
    Reads the first CSV file and returns its headers.
    """
    csv_files = sorted(Path(csv_folder).glob('Ch*.csv'))
    if not csv_files:
        raise FileNotFoundError("No CSV files found in input folder.")
    
    df = pd.read_csv(csv_files[0])
    return df.columns.tolist(), csv_files[0]

def save_structure_to_json(structure_data, csv_file_path):
    """
    Saves the card structure dictionary to a JSON file.

    The JSON file will be saved in the same directory as the source CSV
    file and will have the same name, but with a .json extension.

    Args:
        structure_data (dict): The dictionary containing the card structure.
        csv_file_path (str or Path): The path to the source CSV file.
    """
    try:
        # Using pathlib is robust for handling file paths
        source_path = Path(csv_file_path)
        # Create the new filename by replacing the extension with .json
        json_path = source_path.with_suffix('.json')

        print(f"\nAttempting to save structure to: {json_path}")

        # Open the file and write the JSON data
        with open(json_path, 'w', encoding='utf-8') as f:
            # indent=4 makes the JSON file readable
            json.dump(structure_data, f, indent=4)
        
        print(f"--> Success! Structure saved successfully.")
        
    except (IOError, PermissionError) as e:
        print(f"Error: Could not save the file. Reason: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during saving: {e}")

def _display_creation_state(available_headers, new_structure):
    """Helper to show the current state during creation."""
    print("\n" + "="*50)
    print("CARD STRUCTURE CREATION")
    print("="*50)

    # The list of available headers is now the "pool" of options
    print("\n[Available Headers Pool (can be duplicated)]")
    if not available_headers:
        print("  (Warning: No headers were provided.)")
    for i, header in enumerate(available_headers, 1):
        print(f"  {i}. {header}")

    print("\n[Card Front]")
    if not new_structure['front']:
        print("  (empty)")
    for field in new_structure['front']:
        audio_str = " (audio)" if field['audio'] else ""
        print(f"  - {field['type']}{audio_str}")

    print("\n[Card Back]")
    if not new_structure['back']:
        print("  (empty)")
    for field in new_structure['back']:
        audio_str = " (audio)" if field['audio'] else ""
        print(f"  - {field['type']}{audio_str}")
    print("="*50 + "\n")

def _assign_field_with_duplicates(side, new_structure, available_headers):
    """Helper function to assign headers to a side in a loop."""
    while True:
        # Display state inside the loop so the user sees updates
        _display_creation_state(available_headers, new_structure)
        
        if not available_headers:
            print("There are no headers available to add.")
            input("Press Enter to return to the main menu...")
            return

        try:
            choice_str = input(f"Enter the number of the header to add to the '{side}' (or 'exit' to return to menu): ")
            if choice_str.lower() == 'exit':
                return # Exit this function, returning to the main creation menu
            
            choice = int(choice_str)
            if not (1 <= choice <= len(available_headers)):
                print("Invalid number. Please choose from the list.")
                continue

            chosen_header = available_headers[choice - 1]

            while True:
                has_audio = input(f"Does '{chosen_header}' have an audio field? (y/n): ").lower()
                if has_audio in ['y', 'n']: break
                print("Invalid input. Please enter 'y' or 'n'.")

            new_structure[side].append({'type': chosen_header, 'audio': has_audio == 'y'})
            print(f"--> '{chosen_header}' added to the {side}.\n")

        except ValueError:
            print("Invalid input. Please enter a number.")

def create_initial_structure(headers, csv_file_path):
    """
    Interactively creates an initial card data structure and saves it to a file.

    Args:
        headers (list): A list of available fields from the CSV.
        csv_file_path (str or Path): The path to the source CSV for naming the output file.

    Returns:
        dict: The newly created card data structure.
    """
    available_headers = headers[:]
    new_structure = {'front': [], 'back': []}

    while True:
        _display_creation_state(available_headers, new_structure)
        
        print("--- Initial Structure Menu ---")
        print("1. Add headers to the 'front' of the card")
        print("2. Add headers to the 'back' of the card")
        print("3. Finish and create the structure")
        choice = input("Enter your choice (1-3): ")

        if choice == '1':
            _assign_field_with_duplicates('front', new_structure, available_headers)
        elif choice == '2':
            _assign_field_with_duplicates('back', new_structure, available_headers)
        elif choice == '3':
            print("Initial structure configured.")
            save_structure_to_json(new_structure, csv_file_path)
            return new_structure
        else:
            print("Invalid choice, please try again.")

# You would also need the _display_creation_state function from the previous answer
def _display_creation_state(available_headers, new_structure):
    """Helper to show the current state during creation."""
    print("\n" + "="*50)
    print("CARD STRUCTURE CREATION")
    print("="*50)
    print("\n[Available Headers Pool (can be duplicated)]")
    if not available_headers: print("  (Warning: No headers were provided.)")
    for i, header in enumerate(available_headers, 1): print(f"  {i}. {header}")
    print("\n[Card Front]")
    if not new_structure['front']: print("  (empty)")
    for field in new_structure['front']: print(f"  - {field['type']}{' (audio)' if field['audio'] else ''}")
    print("\n[Card Back]")
    if not new_structure['back']: print("  (empty)")
    for field in new_structure['back']: print(f"  - {field['type']}{' (audio)' if field['audio'] else ''}")
    print("="*50 + "\n")
            
def _print_structure(data):
    """Helper function to print the current card structure with numbers."""
    print("\n--- Current Card Structure ---")
    print("Front:")
    if not data['front']: print("  (empty)")
    for i, field in enumerate(data['front'], 1):
        print(f"  {i}. {field['type']}{' (audio)' if field['audio'] else ''}")
    print("\nBack:")
    if not data['back']: print("  (empty)")
    for i, field in enumerate(data['back'], 1):
        print(f"  {i}. {field['type']}{' (audio)' if field['audio'] else ''}")
    print("----------------------------\n")

def _add_field(data):
    """Handles adding new fields in a loop until the user exits."""
    while True:
        _print_structure(data)
        side = input("Add to 'front' or 'back'? (or type 'exit' to return to menu): ").lower()
        if side == 'exit':
            return
        if side not in ['front', 'back']:
            print("Invalid input. Please enter 'front' or 'back'.")
            continue

        field_name = input(f"Enter the new field name for '{side}' (or 'exit' to cancel): ").strip()
        if field_name.lower() == 'exit':
            continue # Go back to asking for the side
        if not field_name:
            print("Field name cannot be empty.")
            continue

        while True:
            has_audio = input(f"Does '{field_name}' have an audio field? (y/n): ").lower()
            if has_audio in ['y', 'n']:
                break
            print("Invalid input. Please enter 'y' or 'n'.")

        data[side].append({'type': field_name, 'audio': has_audio == 'y'})
        print(f"--> Field '{field_name}' added to {side}.\n")

def _remove_field(data):
    """Handles removing fields in a loop until the user exits."""
    while True:
        _print_structure(data)
        side = input("Remove from 'front' or 'back'? (or type 'exit' to return to menu): ").lower()
        if side == 'exit':
            return
        if side not in ['front', 'back']:
            print("Invalid input. Please enter 'front' or 'back'.")
            continue
        
        if not data[side]:
            print(f"The '{side}' is already empty. Nothing to remove.\n")
            continue

        try:
            choice_str = input(f"Enter the number of the field to remove from '{side}' (or 'exit'): ")
            if choice_str.lower() == 'exit':
                continue # Go back to asking for the side

            choice = int(choice_str)
            if 1 <= choice <= len(data[side]):
                removed = data[side].pop(choice - 1)
                print(f"--> Removed '{removed['type']}' from the {side}.\n")
            else:
                print("Invalid number.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def _reorder_fields(data):
    """Handles reordering fields using swaps in a loop until the user exits."""
    # This function already had a good internal loop, we just adjust the exit command
    # and add an exit option for the initial side selection.
    while True:
        side = input("Reorder fields on 'front' or 'back'? (or type 'exit' to return): ").lower()
        if side == 'exit':
            return
        if side not in ['front', 'back']:
            print("Invalid input.")
            continue
            
        if len(data[side]) < 2:
            print(f"Not enough fields on the '{side}' to reorder.")
            continue

        # Inner loop for performing swaps on the selected side
        while True:
            print(f"\n--- Current '{side}' Order ---")
            for i, field in enumerate(data[side], 1):
                print(f"  {i}. {field['type']}{' (audio)' if field['audio'] else ''}")
            print("------------------------")
            user_input = input("Enter two numbers to swap (e.g., '1-3'), or type 'exit' to finish reordering this side: ").lower()

            if user_input == 'exit':
                break # Breaks inner loop, goes back to asking for the side

            try:
                parts = user_input.split('-')
                if len(parts) != 2: raise ValueError
                idx1, idx2 = int(parts[0]) - 1, int(parts[1]) - 1
                if not (0 <= idx1 < len(data[side]) and 0 <= idx2 < len(data[side])):
                    print("Error: One or both numbers are out of range.")
                    continue
                
                data[side][idx1], data[side][idx2] = data[side][idx2], data[side][idx1]
                print(f"--> Swapped positions {idx1+1} and {idx2+1}.\n")
            except (ValueError, IndexError):
                print("Invalid input. Please use the format 'number-number'.")
        # After breaking the inner loop, the outer loop continues, asking for the side again.
        
def _toggle_audio_flag(data):
    """
    Handles toggling the audio flag for a field in a loop until the user exits.
    """
    while True:
        # Display the structure each time to show the current audio status
        _print_structure(data)
        
        side = input("Select side to toggle audio flag on ('front' or 'back') or 'exit': ").lower()
        if side == 'exit':
            return
        if side not in ['front', 'back']:
            print("Invalid input. Please enter 'front' or 'back'.\n")
            continue
        
        if not data[side]:
            print(f"The '{side}' is empty. Nothing to toggle.\n")
            continue

        try:
            choice_str = input(f"Enter the number of the field on '{side}' to toggle its audio flag (or 'exit'): ")
            if choice_str.lower() == 'exit':
                continue # Go back to asking for the side

            choice = int(choice_str)
            if 1 <= choice <= len(data[side]):
                # Access the chosen dictionary directly
                field_index = choice - 1
                field = data[side][field_index]
                field_name = field['type']
                
                # Invert the boolean value
                field['audio'] = not field['audio']
                
                new_status = "enabled" if field['audio'] else "disabled"
                print(f"--> Audio for '{field_name}' is now {new_status}.\n")
            else:
                print("Invalid number. Please choose from the list.\n")
        except ValueError:
            print("Invalid input. Please enter a number.\n")
            

def edit_card_structure(card_data,csv_file_path):
    """
    Interactively edits a card structure and overwrites the saved file upon exit.

    Args:
        card_data (dict): The original card data structure to edit.
        csv_file_path (str or Path): The path to the source CSV for saving the output file.

    Returns:
        dict: The modified card data structure.
    """
    data = copy.deepcopy(card_data)
    while True:
        print("\n======= Edit Card Structure Menu =======")
        _print_structure(data)
        print("1. Add Fields")
        print("2. Remove Fields")
        print("3. Reorder Fields")
        print("4. Toggle Audio Flag")
        print("5. Save and Exit")
        choice = input("Enter your choice (1-5): ")

        if choice == '1':
            _add_field(data)
        elif choice == '2':
            _remove_field(data)
        elif choice == '3':
            _reorder_fields(data)
        elif choice == '3':
            _toggle_audio_flag(data)
        elif choice == '5':
            print("Structure saved.")
            save_structure_to_json(data, csv_file_path)
            return data
        else:
            print("Invalid choice, please try again.")

class AnkiCardGenerator:
    """
    A class to dynamically generate and visualize Anki flashcard templates.
    """

    def __init__(self, css, initial_data=None):
        """
        Initializes the AnkiCardGenerator.

        Args:
            css (str): The CSS styling for the Anki card.
            initial_data (dict, optional): A dictionary with 'front' and 'back' keys,
                                         each containing a list of field dictionaries.
                                         Defaults to a default structure.
        """
        self.css = css
        if initial_data is None:
            self.card_data = {
                'front': [
                    {'type': 'Word', 'audio': True},
                ],
                'back': [
                    {'type': 'Meaning_Definition', 'audio': True},
                    {'type': 'Antonyms', 'audio': False},
                    {'type': 'Related_Words_Notes', 'audio': True},
                    {'type': 'Examples', 'audio': False},
                ]
            }
        else:
            self.card_data = initial_data

    def make_template(self, data):
        """
        Generates the Anki template from the given data structure.

        Args:
            data (dict): The data structure defining the card's front and back.

        Returns:
            dict: A dictionary containing the template name, qfmt, and afmt.
        """
        qfmt = '<div class="card-front">\n'
        for item in data.get('front', []):
            field_name = item.get('type')
            qfmt += f'    <div class="{field_name.lower()}">{{{{{field_name}}}}}</div>\n'
            if item.get('audio'):
                qfmt += f'    <div class="audio">{{{{{field_name}_Audio}}}}</div>\n'
        qfmt += '</div>'

        afmt = '<div class="card-back">\n'
        afmt += '    <div class="front-word">{{FrontSide}}</div>\n'
        afmt += '    <hr>\n'

        for item in data.get('back', []):
            field_name = item.get('type')
            label = field_name.replace('_', ' ')
            
            afmt += f'    {{#{{{field_name}}}}}\n'
            afmt += '    <div class="section">\n'
            afmt += f'        <div class="label">{label}:</div>\n'
            afmt += f'        <div class="content">{{{{{field_name}}}}}'
            if item.get('audio'):
                afmt += f' {{{{Audio}}}}'
            afmt += '</div>\n'
            afmt += '    </div>\n'
            afmt += f'    {{/{{{field_name}}}}}\n'
        afmt += '</div>'
        
        return {
            'name': 'Dynamic Card',
            'qfmt': qfmt,
            'afmt': afmt,
        }

    def _draw_card(self, title, items, width=50):
        """Helper function to draw a character-based card."""
        top_bottom_border = '#' * width
        title_line = f"#{title.center(width - 2)}#"
        empty_line = f"#{' ' * (width - 2)}#"
        
        lines = [top_bottom_border, title_line, empty_line]

        for item in items:
            field_name = item.get('type')
            placeholder = f"{{{{{field_name}}}}}"
            lines.append(f"#{placeholder.center(width - 2)}#")
            if item.get('audio'):
                audio_placeholder = f"{{{{{field_name}_Audio}}}}"
                lines.append(f"#{audio_placeholder.center(width - 2)}#")
            lines.append(empty_line)
        
        lines.append(top_bottom_border)
        return "\n".join(lines)

    def visualize(self, data):
        """
        Prints a character-based visualization of the card template to the shell.

        Args:
            data (dict): The data structure to visualize.
        """
        front_items = data.get('front', [])
        back_items = data.get('back', [])
        
        # Add the {{FrontSide}} placeholder to the back visualization
        back_display_items = [{'type': 'FrontSide', 'audio': False}] + back_items

        print("Visualizing Card Layout:\n")
        
        front_viz = self._draw_card('front', front_items)
        print(front_viz)
        print("\n" + "="*50 + "\n") # Separator
        back_viz = self._draw_card('back', back_display_items)
        print(back_viz)

# Example Usage
default_css = '''
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

# 1. Get the headers from your CSV file.

csv_headers, csv_path = get_csv_headers('/home/cin/projects/English Vocabulary Anki Deck Generator/input/')

print("Found the following headers from your data source:")
print(csv_headers)

# 2. Call the new function to build the initial structure.
#    The script will now enter the interactive setup menu.
initial_card_structure = create_initial_structure(csv_headers, csv_path)
print(f"Configuration saved to '{csv_path.with_suffix('.json')}'")

# use a pretty printer or a helper function to display it

print(json.dumps(initial_card_structure, indent=4))




# 3. Initialize the generator with your CSS
generator = AnkiCardGenerator(css=default_css)

# 3. Visualize the template with your structure in the shell
generator.visualize(initial_card_structure)

# 4. You can still generate the Anki template as before
anki_template = generator.make_template(initial_card_structure)

# Print the generated template to see the data structure
# import json
# print("\n\nGenerated Anki Template Data:\n")
# print(json.dumps(anki_template, indent=4))


edited_structure = edit_card_structure(initial_card_structure, csv_path)
print("\n--- Structure after further edits ---")
print(json.dumps(edited_structure, indent=4))
print(f"Configuration saved to '{csv_path.with_suffix('.json')}'")


print("\nFinal, updated structure:")
_print_structure(edited_structure) # Using the helper to print the final result
print(f"Configuration saved to '{csv_path.with_suffix('.json')}'")
