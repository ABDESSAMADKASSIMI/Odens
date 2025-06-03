import re
import json
from pathlib import Path
import pandas as pd

def extract_number(text):
    """
    Extracts the first numeric value from a string and returns it as a float.

    This helps clean up and normalize formats like "1 200,50" or "1.200,50"
    which are common in European number formats.

    Parameters
    ----------
    text : str
        The text containing a number (possibly mixed with other characters).

    Returns
    -------
    float or None
        A float if a number is found, otherwise None.
    """
    match = re.search(r"([0-9]+(?:[.,][0-9]+)?)", str(text))
    return float(match.group(1).replace(',', '.')) if match else None


def parse_ytbehandling(text):
    """
    Parses the 'Ytbehandling' (surface treatment) string and extracts
    alloy and temper-related information into structured fields.

    Here, I’m checking for EN standard, 6000-series alloy markers, and temper codes.

    Parameters
    ----------
    text : str
        Raw ytbehandling string from the JSON.

    Returns
    -------
    dict
        Dictionary containing parsed alloy details.
    """
    result = {
        "alloy_series": None,
        "alloy_strength": None,
        "temper_code": None,
        "european_std": 0
    }
    if "EN-AW" in text:
        result["european_std"] = 1
    if "606" in text:
        result["alloy_series"] = 6
        result["alloy_strength"] = 63
    temper_match = re.search(r"T(\d)", text)
    if temper_match:
        result["temper_code"] = int(temper_match.group(1))
    return result


def transform_json(data):
    """
    Cleans and standardizes fields in a single JSON object.

    I extract and convert numerical fields, process date ranges in delivery time,
    and decompose surface treatment codes into structured fields.

    Parameters
    ----------
    data : dict
        The original JSON data (as Python dict) to be transformed.

    Returns
    -------
    dict
        Transformed JSON data with normalized values.
    """
    if "Verktygskostnad" in data:
        data["Verktygskostnad"] = extract_number(data["Verktygskostnad"])

    if "Lev. tid" in data:
        weeks = re.findall(r'(\d+)[-–](\d+)', data["Lev. tid"])
        if weeks:
            ranges = [(int(a) + int(b)) / 2 for a, b in weeks]
            data["Lev. tid"] = round(sum(ranges) / len(ranges), 2)

    if "Råvara" in data:
        data["Råvara"] = extract_number(data["Råvara"])

    if "NOT" in data:
        data["NOT"] = int(extract_number(data["NOT"]) or 0)

    if "Ytbehandling" in data:
        yt = parse_ytbehandling(data["Ytbehandling"])
        data.update(yt)
        del data["Ytbehandling"]

    return data


def transform_json_files(input_dir, output_dir):
    """
    Processes all JSON files in a folder and applies the transformation function.

    Each input file is read, normalized, and then saved into a new folder.

    Parameters
    ----------
    input_dir : str
        Directory containing original JSON files.

    output_dir : str
        Destination folder for the transformed JSONs.

    Returns
    -------
    None
        Writes output JSON files and prints a summary table.
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    transformed_files = []

    for json_file in input_path.glob("*.json"):
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        transformed = transform_json(data)

        out_path = output_path / json_file.name
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(transformed, f, ensure_ascii=False, indent=4)

        transformed_files.append(out_path.name)

    print(f" {len(transformed_files)} JSON files transformed and saved to '{output_path}'")
    print(pd.DataFrame(transformed_files, columns=["Fichier JSON"]).head())


if __name__ == "__main__":
    transform_json_files(
        "Odens/Data_Processing/json_output_from_csv",
        "Odens/Data_Processing/json_transformed"
    )
