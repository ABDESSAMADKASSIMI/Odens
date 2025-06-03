import pandas as pd
import numpy as np
import json
from pathlib import Path
import time
import joblib
import os
from pytorch_tabnet.tab_model import TabNetRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_percentage_error, r2_score
import torch

# Paths
DATA_DIR = "AI_Model_2/json_ready_2"
MODEL_OUTPUT_PATH = "AI_Model_2/tabnet_3.zip"

def load_json_files(directory):
    rows = []
    directory = Path(directory)
    for file in directory.glob("*.json"):
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
        rows.append(data)
    return pd.DataFrame(rows)

def train_tabnet(X_train, y_train, X_val, y_val):
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"🖥️ Device used: {device.upper()}")

    model = TabNetRegressor(
        optimizer_params=dict(lr=5e-2),
        scheduler_params={"step_size": 50, "gamma": 1.3},
        mask_type='entmax',
        n_d=32, n_a=32,
        n_steps=10,
        gamma=1.3,
        lambda_sparse=1e-2,
        n_shared=0,
        device_name=device
    )

    model.fit(
        X_train.values, y_train.values.reshape(-1, 1),
        eval_set=[(X_val.values, y_val.values.reshape(-1, 1))],
        eval_name=["val"],
        eval_metric=["mae"],
        max_epochs=2000,
        patience=2000,
        batch_size=4096,
        virtual_batch_size=4096,
        num_workers=0,
        drop_last=False
    )

    return model

def evaluate_model(model, X_test, y_test):
    X_test = X_test.reset_index(drop=True)
    y_test = y_test.reset_index(drop=True)

    #  On divise par 100 pour revenir à l’échelle originale
    y_test_1d = y_test.values.ravel() / 100
    preds = model.predict(X_test.values).ravel() / 100

    rmse = mean_squared_error(y_test_1d, preds) ** 0.5
    mape = mean_absolute_percentage_error(y_test_1d, preds)
    r2 = r2_score(y_test_1d, preds)

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

    # Nettoyage
    df = df.apply(pd.to_numeric, errors="coerce")
    df = df.dropna(subset=["Pris_kr_st_SEK"]).dropna(axis=1)

    X = df.drop(columns=["Pris_kr_st_SEK"])
    y = df["Pris_kr_st_SEK"]  #  Multiplie la cible pour entraînement plus stable

    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

    print("\n Entraînement du modèle TabNet...")
    model = train_tabnet(X_train, y_train, X_val, y_val)

    print("\n🔍 Évaluation finale...")
    rmse, mape, r2 = evaluate_model(model, X_val, y_val)

    if mape < 0.01:
        print(" Objectif atteint : MAPE < 1% ")
    else:
        print(" Encore à optimiser : MAPE > 1% ")

    print("\n Sauvegarde du modèle optimisé...")
    save_model(model, MODEL_OUTPUT_PATH)

    print(f"\n⏱ Terminé en {time.time() - start:.2f} secondes")
