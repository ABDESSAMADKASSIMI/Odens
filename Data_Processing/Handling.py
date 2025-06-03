import os
import json
import pandas as pd
import numpy as np
from typing import List, Optional
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel, Field, validator
from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import IterativeImputer
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import TargetEncoder
import warnings

warnings.filterwarnings('ignore')

# -----------------------------
# SCHEMA DEFINITIONS (PYDANTIC)
# -----------------------------

class Metadata(BaseModel):
    """
    Describes general information about the quote.
    Dates are validated to match the expected format.
    """
    offert: str
    datum: str = Field(..., alias="Datum")
    vår_referens: str = Field(..., alias="Vår referens")
    er_referens: str = Field(..., alias="Er referens")
    kund: str = Field(..., alias="Kund")

    @validator('datum')
    def validate_date(cls, v):
        datetime.strptime(v, '%Y-%m-%d')
        return v


class Product(BaseModel):
    """
    Represents one product line within the quote.
    Includes weight, length, and price-related attributes.
    """
    profil_ref: str = Field(..., alias="Profil nr/Kund ref")
    vikt_kg_per_m: Optional[float] = Field(None, alias="Vikt kg/m", gt=0)
    längd_m: Optional[float] = Field(None, alias="Längd/m m", gt=0)
    kap_truml_pris: Optional[float] = Field(None, alias="Kap + truml Pris/st")
    årsvolym: Optional[int] = Field(None, alias="ca antal Årsvolym st", gt=0)
    pris_per_st: Optional[float] = Field(None, alias="Prix kr/st SEK")
    legering: str = Field(..., alias="Legering")


class Conditions(BaseModel):
    """
    Captures quote-wide commercial and technical conditions.
    """
    verktygskostnad: str = Field(..., alias="Verktygskostnad")
    legering: str = Field(..., alias="Legering")
    toleranser: str = Field(..., alias="Toleranser")
    ytbehandling: str = Field(..., alias="Ytbehandling")
    lev_längd: str = Field(..., alias="Lev. längd")
    lev_villkor: str = Field(..., alias="Lev. villkor")
    lev_tid: str = Field(..., alias="Lev. tid")
    not_: str = Field(..., alias="NOT")
    betalningsvillkor: str = Field(..., alias="Betalningsvillkor")
    giltighet: str = Field(..., alias="Giltighet")
    allmänna_villkor: str = Field(..., alias="Allmänna villkor")
    råvara: str = Field(..., alias="Råvara")


class Quote(BaseModel):
    """
    Combines metadata, product lines, and conditions into a structured quote.
    Enforces schema correctness using Pydantic.
    """
    metadonnees: Metadata
    produits: List[Product]
    conditions: Conditions

    class Config:
        extra = 'forbid'
        allow_population_by_field_name = True


# -----------------------------------
# DATA LOADING AND PREPROCESSING
# -----------------------------------

def load_and_validate_json(file_path: str) -> Quote:
    """
    Loads a JSON file and parses it into a validated Quote object.
    Raises a validation error if structure or types don't match the schema.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return Quote(**data)


def flatten_quote(quote: Quote) -> List[dict]:
    """
    Unpacks each product line into a flat dictionary by combining it
    with metadata and shared conditions for model training.
    """
    flat_data = []
    for product in quote.produits:
        combined = {
            **quote.metadonnees.dict(by_alias=True),
            **product.dict(by_alias=True),
            **quote.conditions.dict(by_alias=True)
        }
        flat_data.append(combined)
    return flat_data


def advanced_imputation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Performs multivariate imputation on numerical features.
    Here, I relied on iterative imputation to maintain statistical coherence.
    """
    num_cols = ['Vikt kg/m', 'Längd/m m', 'ca antal Årsvolym st', 'Kap + truml Pris/st', 'Prix kr/st SEK']
    for col in num_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    imputer = IterativeImputer(max_iter=10, random_state=42)
    df[num_cols] = imputer.fit_transform(df[num_cols])
    return df


def handle_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """
    Detects and handles outliers using isolation forest.
    Each numeric field is clipped to its 5th–95th percentile to smooth anomalies.
    """
    clf = IsolationForest(contamination=0.05, random_state=42)
    num_cols = ['Vikt kg/m', 'Längd/m m', 'ca antal Årsvolym st', 'Prix kr/st SEK']
    df['outlier_flag'] = clf.fit_predict(df[num_cols]) == -1
    for col in num_cols:
        df[col] = df[col].clip(df[col].quantile(0.05), df[col].quantile(0.95))
    return df


def advanced_encoding(df: pd.DataFrame) -> pd.DataFrame:
    """
    Encodes high-cardinality features using target encoding.
    Also creates a derived feature for price per kilogram.
    """
    encoder = TargetEncoder(smooth='auto')
    high_card_cols = ['Profil nr/Kund ref', 'Kund']
    for col in high_card_cols:
        df[col] = encoder.fit_transform(df[[col]], df['Prix kr/st SEK'])
    df['pris_per_kg'] = df['Prix kr/st SEK'] / (df['Vikt kg/m'] * df['Längd/m m'])
    return df


# --------------------------------------
# MAIN PIPELINE FUNCTION
# --------------------------------------

def process_quote_files(directory: str) -> pd.DataFrame:
    """
    This function reads all valid JSON quotes from the given directory.
    Each file is validated and flattened, then the resulting DataFrame
    undergoes imputation, outlier smoothing, and encoding.
    """
    all_quotes = []
    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            file_path = os.path.join(directory, filename)
            try:
                quote = load_and_validate_json(file_path)
                flat_data = flatten_quote(quote)
                all_quotes.extend(flat_data)
            except Exception as e:
                print(f"⚠️ Skipping {filename} due to error: {e}")

    if not all_quotes:
        print("⚠️ No valid quotes found.")
        return pd.DataFrame()

    df = pd.DataFrame(all_quotes)
    df = advanced_imputation(df)
    df = handle_outliers(df)
    df = advanced_encoding(df)

    return df


# --------------------------------------
# EXECUTION ENTRY POINT
# --------------------------------------

if __name__ == "__main__":
    input_directory = 'Odens/Data_Processing/json files'
    output_csv = 'Odens/Data_Processing/processed_quotes.csv'

    os.makedirs('AI_Model_2', exist_ok=True)
    processed_df = process_quote_files(input_directory)

    if not processed_df.empty:
        processed_df.to_csv(output_csv, index=False)
        print(f" Processing complete. Data saved to {output_csv}")
    else:
        print("⚠️ No data processed.")
