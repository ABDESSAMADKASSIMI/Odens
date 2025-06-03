import json
import os
import random
import copy
from pathlib import Path

# --- CONFIGURATION ---

ALLOWED_SERIES = [1, 2, 3, 4, 5, 6, 7]
TEMPER_CODES = list(range(1, 10))
EUROPEAN_STDS = [0, 1]

ALLOY_STRENGTH_RANGES = {
    1: (50, 80),
    2: (120, 180),
    3: (110, 160),
    4: (100, 150),
    5: (150, 250),
    6: (150, 300),
    7: (300, 500)
}

TOLERANCE_STANDARDS = [
    "EN 755-9", "ISO 2768-m", "ASME Y14.5", "DIN 7168",
    "ISO 286", "JIS B 0401", "ISO 2768-1", "ISO 8015",
    "ASME B4.1", "DEFAULT", "BS 4500", "ISO 1829"
]

ALLOY_CATEGORIES = [
    "Aluminium 1050 Rå", "Aluminium 2017 T4", "Aluminium 3003 H14",
    "Aluminium 4043 O", "Aluminium 5083 H111", "Aluminium 6061 T6",
    "Aluminium 7075 T651", "Aluminium 2024 T351", "Rå"
]

# --- HELPERS ---

def same_decimal_round(original_value, new_value):
    """
    Conserve le nombre de décimales d'une valeur originale.
    """
    if isinstance(original_value, float):
        decimals = len(str(original_value).split(".")[1])
        return round(new_value, decimals)
    return int(new_value)


def apply_consistent_variation(value, variation):
    """
    Applique une variation uniforme à une valeur numérique.
    """
    if not isinstance(value, (int, float)) or value == 0:
        return value
    return value * (1 + variation)


def modify_large_number_consistent(value, variation):
    """
    Applique une variation à une grande valeur entière et arrondit à 1000 près.
    """
    if not isinstance(value, (int, float)) or value <= 0:
        return value
    varied = value * (1 + variation)
    return int(varied // 1000) * 1000

def modify_alloy_fields():
    """
    Génère aléatoirement des infos d’alliage.
    """
    series = random.choice(ALLOWED_SERIES)
    min_str, max_str = ALLOY_STRENGTH_RANGES[series]
    return {
        "alloy_series": series,
        "alloy_strength": random.randint(min_str, max_str),
        "temper_code": random.choice(TEMPER_CODES),
        "european_std": random.choice(EUROPEAN_STDS)
    }

# --- MAIN FUNCTION ---

def generate_variants(input_folder: str, output_folder: str, num_variants: int = 19):
    input_path = Path(input_folder)
    output_path = Path(output_folder)
    output_path.mkdir(parents=True, exist_ok=True)

    total = 0
    for file in input_path.glob("*.json"):
        with open(file, 'r', encoding='utf-8') as f:
            original = json.load(f)

        base_name = file.stem

        # Save the original copy
        original_output = output_path / f"{base_name}_0_original.json"
        with open(original_output, 'w', encoding='utf-8') as f:
            json.dump(original, f, indent=2, ensure_ascii=False)
        total += 1

        for i in range(1, num_variants + 1):
            new_data = copy.deepcopy(original)

            # 1️⃣ Tirer une seule valeur de variation pour ce fichier
            variation = random.uniform(-0.10, 0.10)

            # 2️⃣ Champs numériques à modifier (SANS toucher à la target)
            numeric_fields = [
                "Vikt kg/m",
                "Längd/m m",
                "Kap + truml Pris/st",
                "Lev. tid",
                "Råvara"
            ]
            for field in numeric_fields:
                if field in new_data:
                    old_value = new_data[field]
                    new_value = apply_consistent_variation(old_value, variation)
                    new_data[field] = same_decimal_round(old_value, new_value)

            # 3️⃣ Champs entiers à modifier (volume, outil, NOT)
            for field in ["ca antal Årsvolym st", "Verktygskostnad", "NOT"]:
                if field in new_data:
                    new_data[field] = modify_large_number_consistent(new_data[field], variation)

            # 4️⃣ Categorical changes (sans effet sur la target)
            new_data["Legering"] = random.choice(ALLOY_CATEGORIES)
            new_data.update(modify_alloy_fields())
            new_data["Toleranser"] = random.choice(TOLERANCE_STANDARDS)

            # 5️⃣ Sauvegarde du fichier modifié
            variant_output = output_path / f"{base_name}_{i}.json"
            with open(variant_output, 'w', encoding='utf-8') as f:
                json.dump(new_data, f, indent=2, ensure_ascii=False)
            total += 1

    print(f"✅ {total} fichiers générés dans '{output_folder}'")

# --- SCRIPT EXECUTION ---
if __name__ == "__main__":
    generate_variants("Odens/Data_Processing/json_transformed", "Odens/Data_Processing/json_variants")
