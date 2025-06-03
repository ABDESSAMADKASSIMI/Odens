import json
import re
from pathlib import Path


def convert_num(value):
    """
    Attempts to convert a string to a float or int.
    If conversion fails, the value is stripped and returned as a string.
    """
    if not value:
        return None
    v = value.replace(',', '.').replace(' ', '')
    try:
        if '.' in v:
            return float(v)
        else:
            return int(v)
    except ValueError:
        return value.strip()


def parse_section_key_val(text):
    """
    Extracts key-value pairs from a text block where each line is formatted as 'key: value'.
    Returns a dictionary mapping keys to values.
    """
    result = {}
    for line in text.split('\n'):
        if ':' in line:
            key, val = line.split(':', 1)
            result[key.strip()] = val.strip()
    return result


def txt_to_json(text):
    """
    Processes structured text and organizes it into a JSON-serializable dictionary.
    Sections for metadata, product details, and conditions are parsed independently.
    """
    sections = re.split(r'===\s*(.+?)\s*===', text)
    data_sections = {}
    for i in range(1, len(sections), 2):
        key = sections[i].strip().lower()
        val = sections[i+1].strip()
        data_sections[key] = val

    # Extract metadata lines
    metadonnees_lines = data_sections.get('métadonnées', '').split('\n')
    metadonnees = {}
    for line in metadonnees_lines:
        if ':' in line:
            k, v = line.split(':', 1)
            metadonnees[k.strip()] = v.strip()
        elif line.strip():
            metadonnees['offert'] = line.strip()

    # Extract product lines
    produits_txt = data_sections.get('produits', '')
    produits_lines = [l.strip() for l in produits_txt.split('\n') if l.strip()]
    if len(produits_lines) < 3:
        produits = []
    else:
        headers_line = produits_lines[0]
        headers = [h.strip() for h in headers_line.split('|')]
        produits_data_lines = produits_lines[2:]

        produits = []
        for line in produits_data_lines:
            cols = [c.strip() for c in line.split('|')]
            if len(cols) < len(headers):
                cols += [''] * (len(headers) - len(cols))
            elif len(cols) > len(headers):
                cols = cols[:len(headers)-1] + [' '.join(cols[len(headers)-1:])]
            produit_dict = {h: convert_num(c) for h, c in zip(headers, cols)}
            produits.append(produit_dict)

    # Extract conditions
    conditions_txt = data_sections.get('conditions', '')
    conditions = parse_section_key_val(conditions_txt)
    for key in conditions:
        conditions[key] = convert_num(conditions[key])

    return {
        "metadonnees": metadonnees,
        "produits": produits,
        "conditions": conditions
    }


def batch_convert_txt_folder(input_folder, output_folder):
    """
    Here, all .txt files in a given folder are read and converted into structured JSON format.
    Converted files are saved to the specified output directory using the original filename base.
    """
    input_path = Path(input_folder)
    output_path = Path(output_folder)
    output_path.mkdir(parents=True, exist_ok=True)

    txt_files = list(input_path.glob("*.txt"))
    print(f"Found {len(txt_files)} .txt files to process.")

    for txt_file in txt_files:
        with open(txt_file, 'r', encoding='utf-8') as f:
            text = f.read()

        json_data = txt_to_json(text)

        output_file = output_path / (txt_file.stem + ".json")
        with open(output_file, 'w', encoding='utf-8') as fjson:
            json.dump(json_data, fjson, ensure_ascii=False, indent=4)

        print(f"Processed {txt_file.name} ➔ {output_file.name}")


def main():
    input_folder = "Odens/Data_Processing/txt_Corrected"
    output_folder = "Odens/Data_Processing/json files"
    batch_convert_txt_folder(input_folder, output_folder)


if __name__ == "__main__":
    main()
