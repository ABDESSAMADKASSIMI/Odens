import pandas as pd
import json
from pathlib import Path

def convert_csv_to_json_rows(csv_path: str, output_dir: str):
    """
    Converts each row of a CSV file into a separate JSON file.

    Here, I read the CSV file and loop through each row to serialize it as an individual JSON object.
    The resulting JSON files are stored in the specified output directory.

    Parameters
    ----------
    csv_path : str
        Path to the input CSV file that contains structured data.

    output_dir : str
        Folder where all the output JSON files will be saved.

    Returns
    -------
    None
        The function writes JSON files to disk and prints a summary to the console.
    """
    df = pd.read_csv(csv_path)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    json_file_paths = []
    for idx, row in df.iterrows():
        row_dict = row.to_dict()
        json_path = output_path / f"quote_{idx+1}.json"
        json_file_paths.append(json_path.name)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(row_dict, f, ensure_ascii=False, indent=4)

    print(f" {len(json_file_paths)} JSON files generated in '{output_path}'")
    print(pd.DataFrame(json_file_paths, columns=["Fichier JSON"]).head())

if __name__ == "__main__":
    convert_csv_to_json_rows(
        "Odens/Data_Processing/processed_quotes.csv",
        "Odens/Data_Processing/json_output_from_csv"
    )
