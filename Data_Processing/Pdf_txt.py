import pdfplumber
from pathlib import Path

def extract_text_from_single_pdf(pdf_path: Path) -> str:
    """
    I use this function to extract all the text from a single PDF file.

    Parameters:
    ----------
    pdf_path : Path
        Path object pointing to the PDF file.

    Returns:
    -------
    str
        Full extracted text from the PDF.
    """
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
    return text


def save_text_to_file(text: str, output_path: Path):
    """
    I use this function to save the extracted text into a .txt file.

    Parameters:
    ----------
    text : str
        Text to save into the file.
    output_path : Path
        Path object where the .txt file will be written.

    Returns:
    -------
    None
    """
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"[INFO] Saved extracted text to '{output_path.name}'.")


def extract_text_from_pdfs(input_folder: str, output_folder: str):
    """
    I use this main function to extract text from all PDF files in a given folder
    and save them as .txt files in the output folder.

    Parameters:
    ----------
    input_folder : str
        Folder that contains all PDF files.
    output_folder : str
        Folder where I want to save the .txt files.

    Returns:
    -------
    None
    """
    input_path = Path(input_folder)
    output_path = Path(output_folder)

    # I make sure the output folder exists
    output_path.mkdir(parents=True, exist_ok=True)

    # I loop through each PDF and process it
    for pdf_file in input_path.glob("*.pdf"):
        print(f"[INFO] Processing: {pdf_file.name}")
        text = extract_text_from_single_pdf(pdf_file)
        txt_file = output_path / f"{pdf_file.stem}.txt"
        save_text_to_file(text, txt_file)


# Main entry point for testing or actual use
def main():
    input_dir = "Odens/Data_Processing/Test files"
    output_dir = "Odens/Data_Processing/txt files"
    extract_text_from_pdfs(input_dir, output_dir)

# I use this block to test the code when running the script directly
if __name__ == "__main__":
    main()
