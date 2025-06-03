import re
from pathlib import Path

def extract_leg_from_conditions(conditions):
    """
    I use this function to extract the alloy (Legering) from a list of condition strings.
    If no alloy is found, I return an empty string.

    Parameters:
    ----------
    conditions : list[str]
        A list of lines representing product conditions.

    Returns:
    -------
    str
        Extracted alloy value (Legering), or empty string if not found.
    """
    for cond in conditions:
        if cond.startswith("Legering:"):
            parts = cond.split(":", 1)
            if len(parts) > 1:
                return parts[1].strip()
    return ""


def parse_product_line(tokens, fallback_name, default_legering):
    """
    I use this function to convert a line of raw product data into structured product information.

    Parameters:
    ----------
    tokens : list[str]
        Tokens from the product line.
    fallback_name : str
        A default name if none is found in the tokens.
    default_legering : str
        Default alloy value if none is found in the line.

    Returns:
    -------
    list
        A list of cleaned values: name, vikt, längd, kap, antal, pris, legering.
    """
    name = fallback_name
    vikt = längd = kap = antal = pris = ""
    legering = default_legering

    # I split numeric and non-numeric tokens
    numbers = [token.replace(",", ".") for token in tokens if re.match(r'^\d+[,.]?\d*$', token)]
    strings = [token for token in tokens if not re.match(r'^\d+[,.]?\d*$', token)]

    # I update the name if a string is available
    if strings:
        name = strings[0]

    # I assign values based on business rules
    for num in numbers:
        num_float = float(num)
        if num_float > 1000 and not antal:
            antal = num
        elif num_float > 10 and not längd:
            längd = num
        elif 1 < num_float < 2 and not vikt:
            vikt = num
        elif num_float < 1 and not kap:
            kap = num
        else:
            pris = num

    return [name, vikt, längd, kap, antal, pris, legering]


def format_offer(input_file: Path, output_file: Path):
    """
    I use this function to transform raw text extracted from PDF into a clean offer summary
    including metadata, products, and conditions. Everything is written to a new .txt file.

    Parameters:
    ----------
    input_file : Path
        Path to the original raw .txt file.
    output_file : Path
        Path to write the formatted offer to.

    Returns:
    -------
    None
    """
    # I read and clean up lines
    with input_file.open('r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]

    metadata, raw_products, products, conditions = [], [], [], []
    in_products_section = False

    # Condition headers I use to split sections
    condition_starters = [
        "Verktygskostnad:", "Legering:", "Toleranser:", "Ytbehandling:",
        "Lev. längd:", "Lev. villkor:", "Lev. tid:", "NOT:",
        "Betalningsvillkor:", "Giltighet:", "Allmänna villkor:", "Råvara:"
    ]

    # I separate metadata, product data, and conditions
    for line in lines:
        if line.startswith("Profil nr / Vikt"):
            in_products_section = True
            continue

        if any(line.startswith(starter) for starter in condition_starters):
            in_products_section = False
            conditions.append(line)
            continue

        if not in_products_section and not conditions:
            metadata.append(line)
            continue

        if in_products_section:
            if line.startswith("Kund ref.") or line in ("SEK", "Pris/st SEK"):
                continue
            raw_products.append(line.split())

    # I use the first valid string as fallback name
    fallback_name = next((tokens[0] for tokens in raw_products if not re.match(r'^\d+[,.]?\d*$', tokens[0])), "")
    default_legering = extract_leg_from_conditions(conditions)

    # I process all product lines
    for tokens in raw_products:
        parsed = parse_product_line(tokens, fallback_name, default_legering)
        products.append(parsed)

    # I now write the formatted data to a file
    with output_file.open('w', encoding='utf-8') as f:
        f.write("=== MÉTADONNÉES ===\n")
        f.write("\n".join(metadata[:5]) + "\n\n")

        if len(products) > 2:
            f.write("=== PRODUITS ===\n")
            f.write("Profil nr/Kund ref | Vikt kg/m | Längd/m m | Kap + truml Pris/st | ca antal Årsvolym st | Prix kr/st SEK | Legering\n")
            f.write("-------------------|-----------|-----------|---------------------|----------------------|----------------|---------\n")
            for prod in products:
                formatted_line = (
                    f"{prod[0]:<18} | {prod[1]:>9} | {prod[2]:>9} | "
                    f"{prod[3]:>19} | {prod[4]:>20} | {prod[5]:>14} | {prod[6]}"
                )
                f.write(formatted_line + "\n")
            f.write("\n")

        f.write("=== CONDITIONS ===\n")
        f.write("\n".join(conditions))


def format_all_txt_files_in_folder(input_dir, output_dir):
    """
    I use this function to apply `format_offer()` to every .txt file in a given folder.

    Parameters:
    ----------
    input_dir : str
        Folder containing raw .txt files.
    output_dir : str
        Folder where I want to save the formatted versions.

    Returns:
    -------
    None
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    for input_file in input_path.glob("*.txt"):
        output_file = output_path / input_file.name
        format_offer(input_file, output_file)
        print(f"[✓] {input_file.name} ➔ {output_file.name}")


def main():
    """
    I use this `main()` function to test the script directly.
    You can adjust the input/output folders here.
    """
    format_all_txt_files_in_folder("Odens/Data_Processing/txt files", "Odens/Data_Processing/txt_Corrected")


if __name__ == "__main__":
    main()
