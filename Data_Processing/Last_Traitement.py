import json
import math
import os
import random
from pathlib import Path

# === TOLERANCE MAPPING ===
# This table encodes geometric tolerance characteristics for different industrial standards.
# It's helpful for scoring manufacturability or calculating derived metrics.
TOLERANCE_MAPPING = {
    "EN 755-9": {"linear_tol": 0.15, "angular_tol": 0.5, "flatness": 0.2, "gd_t_index": 2.1},
    "ISO 2768-m": {"linear_tol": 0.1, "angular_tol": 0.3, "flatness": 0.15, "gd_t_index": 2.8},
    "ASME Y14.5": {"linear_tol": 0.05, "angular_tol": 0.2, "flatness": 0.1, "gd_t_index": 3.5},
    "DIN 7168": {"linear_tol": 0.08, "angular_tol": 0.25, "flatness": 0.12, "gd_t_index": 3.0},
    "ISO 286": {"linear_tol": 0.06, "angular_tol": 0.22, "flatness": 0.08, "gd_t_index": 3.2},
    "JIS B 0401": {"linear_tol": 0.07, "angular_tol": 0.28, "flatness": 0.11, "gd_t_index": 2.9},
    "ISO 2768-1": {"linear_tol": 0.09, "angular_tol": 0.31, "flatness": 0.14, "gd_t_index": 2.7},
    "ISO 8015": {"linear_tol": 0.04, "angular_tol": 0.18, "flatness": 0.07, "gd_t_index": 3.6},
    "ASME B4.1": {"linear_tol": 0.12, "angular_tol": 0.35, "flatness": 0.18, "gd_t_index": 2.5},
    "BS 4500": {"linear_tol": 0.11, "angular_tol": 0.33, "flatness": 0.16, "gd_t_index": 2.6},
    "ISO 1829": {"linear_tol": 0.13, "angular_tol": 0.4, "flatness": 0.19, "gd_t_index": 2.4},
    "DEFAULT": {"linear_tol": 0.3, "angular_tol": 1.0, "flatness": 0.5, "gd_t_index": 1.0}
}

# List of alloy categories used to encode categorical material types
ALLOY_CATEGORIES = [
    "Aluminium 1050 Rå", "Aluminium 2017 T4", "Aluminium 3003 H14",
    "Aluminium 4043 O", "Aluminium 5083 H111", "Aluminium 6061 T6",
    "Aluminium 7075 T651", "Aluminium 2024 T351", "Rå"
]

# Material density (aluminium) in kg/m³
DENSITY_ALU = 2700

def calculate_geometric_features(weight_kg_per_m, length_m):
    """
    Here I compute a set of shape-related geometric features derived from product mass and length.

    These metrics are used to estimate profile thickness, manufacturability (DFM), and surface ratios.

    Parameters
    ----------
    weight_kg_per_m : float
        Mass of the profile per meter.
    length_m : float
        Length of the profile.

    Returns
    -------
    dict
        Dictionary of calculated features: thinness, area-to-length ratio, wall factor, etc.
    """
    area_mm2 = (weight_kg_per_m / DENSITY_ALU) * 1e6
    height = math.sqrt(area_mm2 * 2)
    width = area_mm2 / height
    perimeter = 2 * (height + width)
    thinness_ratio = (4 * math.pi * area_mm2) / (perimeter ** 2)
    area_to_length = area_mm2 / (length_m * 1000)
    wall_factor = area_mm2 / perimeter
    dfm_index = min(1.0, 0.7 / (weight_kg_per_m ** 0.25))
    symmetry_score = 0.8

    return {
        "thinness_ratio": round(thinness_ratio, 4),
        "area_to_length": round(area_to_length, 5),
        "wall_factor": round(wall_factor, 4),
        "dfm_index": round(dfm_index, 4),
        "symmetry_score": round(symmetry_score, 4)
    }

def find_key(data, possible_keys):
    """
    Tries to retrieve a value from a list of possible field names.

    Parameters
    ----------
    data : dict
        Dictionary containing raw product data.
    possible_keys : list
        List of key names to try.

    Returns
    -------
    value
        The matched value from the input dictionary.

    Raises
    ------
    KeyError
        If none of the possible keys are found.
    """
    for key in possible_keys:
        if key in data:
            return data[key]
    raise KeyError(f"None of {possible_keys} found in: {data.keys()}")

def process_single_file(input_path, output_path):
    """
    Processes a single product JSON file and adds derived features.

    I include geometry, alloy encoding, tolerance mappings,
    and simulated LME prices for enrichment.

    Parameters
    ----------
    input_path : str
        Path to the original file.
    output_path : str
        Destination where the processed file will be saved.

    Returns
    -------
    bool
        Whether the file was successfully processed.
    """
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        processed = {
            "Vikt_kg_m": find_key(data, ["Vikt kg/m", "Weight kg/m"]),
            "Längd_m_m": find_key(data, ["Längd/m m", "Length/m"]),
            "Kap_truml_Pris_st": find_key(data, ["Kap + truml Pris/st"]),
            "Årsvolym_st": find_key(data, ["ca antal Årsvolym st"]),
            "Verktygskostnad": find_key(data, ["Verktygskostnad"]),
            "Lev_tid": find_key(data, ["Lev. tid"]),
            "NOT": find_key(data, ["NOT"]),
            "alloy_series": find_key(data, ["alloy_series"]),
            "alloy_strength": find_key(data, ["alloy_strength"]),
            "temper_code": find_key(data, ["temper_code"]),
            "european_std": find_key(data, ["european_std"]),
            "Råvara": find_key(data, ["Råvara"]),
            "Pris_kr_st_SEK": find_key(data, ["Prix kr/st SEK"])
        }

        # Geometry & material-based metrics
        processed.update(calculate_geometric_features(
            processed["Vikt_kg_m"],
            processed["Längd_m_m"]
        ))

        # Tolerance mapping
        tolerance = find_key(data, ["Toleranser"])
        processed.update(TOLERANCE_MAPPING.get(tolerance, TOLERANCE_MAPPING["DEFAULT"]))

        # Encode alloy category as index
        alloy = find_key(data, ["Legering"])
        processed["alloy_category"] = ALLOY_CATEGORIES.index(alloy) if alloy in ALLOY_CATEGORIES else len(ALLOY_CATEGORIES) - 1

        # Simulate LME price indicators
        base_price = processed["Råvara"]
        processed["LME_price_MA3"] = round(base_price * random.uniform(0.9, 1.1), 2)
        processed["LME_price_Lag1"] = round(base_price * random.uniform(0.95, 1.05), 2)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(processed, f, indent=2, ensure_ascii=False)
        return True

    except Exception as e:
        print(f"✗ Failed: {os.path.basename(input_path)} → {str(e)}")
        return False

def prepare_dataset(input_dir, output_dir):
    """
    Converts all enriched JSON variants into a flat dataset ready for training.

    I apply processing to every file, including geometric augmentation,
    categorical encoding, and numerical normalization.

    Parameters
    ----------
    input_dir : str
        Folder with the synthetic JSON input files.
    output_dir : str
        Destination for the processed outputs.

    Returns
    -------
    int
        Number of files successfully processed.
    """
    os.makedirs(output_dir, exist_ok=True)
    processed, errors = 0, 0

    for file in os.listdir(input_dir):
        if file.endswith('.json'):
            success = process_single_file(
                os.path.join(input_dir, file),
                os.path.join(output_dir, f"processed_{file}")
            )
            if success:
                print(f"✓ Processed: {file}")
                processed += 1
            else:
                errors += 1

    print("\n Dataset preparation complete.")
    print(f" Success: {processed} files")
    print(f" Failed: {errors} files")
    print(f" Output: {output_dir}")
    return processed

# === MAIN EXECUTION ===
def main():
    input_dir = "Odens/Data_Processing/json_variants"
    output_dir = "Odens/Data_Processing/json_ready"
    print(" Starting dataset preparation...")
    prepare_dataset(input_dir, output_dir)

if __name__ == "__main__":
    main()
