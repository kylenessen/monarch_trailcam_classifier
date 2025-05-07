import json
import argparse
import os

def reset_confirmations(file_path):
    """
    Resets the 'confirmed' status to False for entries in a JSON file,
    except where 'isNight' is True.

    Args:
        file_path (str): The path to the configurations.json file.
    """
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return

    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in {file_path}")
        return
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return

    modified = False
    if 'classifications' in data and isinstance(data['classifications'], dict):
        for image_name, classification_data in data['classifications'].items():
            if isinstance(classification_data, dict):
                is_night = classification_data.get('isNight', False)
                confirmed = classification_data.get('confirmed', False)

                if confirmed is True and is_night is False:
                    classification_data['confirmed'] = False
                    modified = True
                    print(f"Reset 'confirmed' for {image_name}")
            else:
                print(f"Warning: Skipping invalid classification data for {image_name}")
    else:
        print("Error: 'classifications' key not found or is not a dictionary in the JSON file.")
        return

    if modified:
        try:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2) # Using indent=2 for readability
            print(f"Successfully updated {file_path}")
        except Exception as e:
            print(f"Error writing updated data to {file_path}: {e}")
    else:
        print("No changes were needed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Resets the 'confirmed' status in a configurations.json file.")
    parser.add_argument("file_path", help="Path to the configurations.json file")
    args = parser.parse_args()

    reset_confirmations(args.file_path)
