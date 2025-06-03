import pandas as pd
import numpy as np
import json
from pathlib import Path
import time
import joblib
import os
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_percentage_error, r2_score
from lightgbm import LGBMRegressor

# Paths
DATA_DIR = "AI_Model_2/json_ready_2"
MODEL_OUTPUT_PATH = "AI_Model_2/lightgbm_model.zip"

def load_json_files(directory):
    rows = []
    directory = Path(directory)
    for file in directory.glob("*.json"):
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
        rows.append(data)
    return pd.DataFrame(rows)

def train_lgbm(X_train, y_train):
    model = LGBMRegressor(
        objective='regression',
        n_estimators=1000,
        learning_rate=0.05,
        num_leaves=31,
        max_depth=-1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42
    )
    model.fit(X_train, y_train)
    return model

def evaluate_model(model, X_test, y_test):
    preds = model.predict(X_test)

    rmse = mean_squared_error(y_test, preds) ** 0.5
    mape = mean_absolute_percentage_error(y_test, preds)
    r2 = r2_score(y_test, preds)

    print(f" Résultats sur validation :")
    print(f"🔹 RMSE : {rmse:.4f}")
    print(f"🔹 MAPE : {mape*100:.2f}%")
    print(f"🔹 R²   : {r2:.4f}")
    return rmse, mape, r2

def save_model(model, output_path):
    joblib.dump(model, output_path)
    print(f" Modèle sauvegardé : {output_path}")

if __name__ == "__main__":
    start = time.time()
    print(" Chargement des données...")
    df = load_json_files(DATA_DIR)
    print(f" {len(df)} fichiers JSON chargés.")

    df = df.apply(pd.to_numeric, errors="coerce")
    df = df.dropna(subset=["Pris_kr_st_SEK"]).dropna(axis=1)

    # Si tu veux multiplier les targets par 100 (comme tu avais dit)
    df["Pris_kr_st_SEK"] *= 100

    X = df.drop(columns=["Pris_kr_st_SEK"])
    y = df["Pris_kr_st_SEK"]

    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

    print("\n Entraînement du modèle LightGBM...")
    model = train_lgbm(X_train, y_train)

    print("\n🔍 Évaluation finale...")
    rmse, mape, r2 = evaluate_model(model, X_val, y_val)

    if mape < 0.01:
        print(" Objectif atteint : MAPE < 1% ")
    else:
        print(" Encore à optimiser : MAPE > 1% ")

    print("\n Sauvegarde du modèle optimisé...")
    save_model(model, MODEL_OUTPUT_PATH)

    print(f"\n⏱ Terminé en {time.time() - start:.2f} secondes")
