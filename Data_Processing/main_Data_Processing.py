import os
import shutil
import json

from pathlib import Path
from Pdf_txt import extract_text_from_pdfs
from txt_Correction import format_all_txt_files_in_folder
from txt_json import batch_convert_txt_folder
from Handling import process_quote_files
from CSV_json import convert_csv_to_json_rows
from Organisation_json import transform_json_files
from Simulation import generate_variants
from Last_Traitement import prepare_dataset


def copy_extra_json_folder_into_ready_folder(extra_folder_path: str, destination_folder: str):
    """
    I use this function to copy all valid JSON files from a given folder into the final 'json_ready' folder.

    Parameters:
    ----------
    extra_folder_path : str
        Path to the folder that contains additional JSON files.
    destination_folder : str
        Final destination folder where the JSON files should be copied.

    Returns:
    -------
    None
    """
    extra_path = Path(extra_folder_path)
    dest_path = Path(destination_folder)
    dest_path.mkdir(parents=True, exist_ok=True)

    if not extra_path.exists() or not extra_path.is_dir():
        print(f"⚠️ Extra folder '{extra_folder_path}' not found or not a directory.")
        return

    for json_file in extra_path.glob("*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                content = json.load(f)  # I validate it's proper JSON

            # If valid, I copy the file
            target_file = dest_path / json_file.name
            with open(target_file, 'w', encoding='utf-8') as f_out:
                json.dump(content, f_out, ensure_ascii=False, indent=4)

            print(f"[INFO]  Added '{json_file.name}' to {destination_folder}")

        except Exception as e:
            print(f" Skipped '{json_file.name}' — invalid JSON: {e}")


def main(input_dir: str, output_dir: str, extra_json_folder: str = None):
    """
    I use this pipeline to process raw PDF data all the way to enriched JSONs.
    If an additional folder of JSON files is provided, I include its content in the final dataset.

    Parameters
    ----------
    input_dir : str
        Folder containing original PDF files.
    output_dir : str
        Folder to save all output files.
    extra_json_folder : str, optional
        Path to a folder containing extra JSON files to add to final output.

    Returns
    -------
    None
    """
    print("Step 1: Extracting text from PDFs...")
    extract_text_from_pdfs(input_dir, f"{output_dir}/txt files")

    print("Step 2: Formatting .txt files...")
    format_all_txt_files_in_folder(f"{output_dir}/txt files", f"{output_dir}/txt_Corrected")

    print("Step 3: Converting .txt to JSON...")
    batch_convert_txt_folder(f"{output_dir}/txt_Corrected", f"{output_dir}/json files")

    print("Step 4: Flattening JSON and saving to CSV...")
    os.makedirs(output_dir, exist_ok=True)
    processed_df = process_quote_files(f"{output_dir}/json files")
    csv_path = f"{output_dir}/processed_quotes.csv"

    if not processed_df.empty:
        processed_df.to_csv(csv_path, index=False)
        print(f" Processing complete. Data saved to {csv_path}")
    else:
        print("⚠️ No data processed.")
        return

    print("Step 5: Splitting CSV into individual JSON rows...")
    convert_csv_to_json_rows(csv_path, f"{output_dir}/json_output_from_csv")

    print("Step 6: Transforming JSON fields...")
    transform_json_files(f"{output_dir}/json_output_from_csv", f"{output_dir}/json_transformed")

    print("Step 7: Generating data variants...")
    generate_variants(f"{output_dir}/json_transformed", f"{output_dir}/json_variants")

    print("Step 8: Preparing dataset with features...")
    prepare_dataset(f"{output_dir}/json_variants", f"{output_dir}/json_ready")

    # OPTIONAL STEP
    if extra_json_folder:
        print("Step 9: Adding extra JSON files from folder to final dataset...")
        copy_extra_json_folder_into_ready_folder(extra_json_folder, f"{output_dir}/json_ready")

    print(" Full data pipeline completed successfully!")


if __name__ == "__main__":
    # Example usage
    main(
        input_dir="Odens/Data_Processing/Test files",
        output_dir="Odens/Data_Processing",
        extra_json_folder="Odens/Data_Processing/extra_jsons"
    )
