import pandas as pd
import numpy as np
import json
from pathlib import Path
import time
import joblib
from catboost import CatBoostRegressor, Pool
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_percentage_error, r2_score

# Chemins
DATA_DIR = "AI_Model_2/json_ready_2"
MODEL_OUTPUT_PATH = "AI_Model_2/catboost_model.zip"

def load_json_files(directory):
    rows = []
    directory = Path(directory)
    for file in directory.glob("*.json"):
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
        rows.append(data)
    return pd.DataFrame(rows)

def train_catboost(X_train, y_train, X_val, y_val):
    model = CatBoostRegressor(
        iterations=3000,
        learning_rate=0.02,
        depth=8,
        loss_function='MAE',
        eval_metric='MAPE',
        early_stopping_rounds=3000,
        verbose=100,
        task_type="GPU"  # ou "CPU" si tu n'as pas de GPU
    )

    train_pool = Pool(X_train, y_train)
    val_pool = Pool(X_val, y_val)

    model.fit(train_pool, eval_set=val_pool)
    return model

def evaluate_model(model, X_val, y_val):
    y_val_true = np.expm1(y_val)
    y_pred_log = model.predict(X_val)
    y_pred = np.expm1(y_pred_log)

    rmse = mean_squared_error(y_val_true, y_pred) ** 0.5
    mape = mean_absolute_percentage_error(y_val_true, y_pred)
    r2 = r2_score(y_val_true, y_pred)

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

    # Transformation de la target
    df["Pris_kr_st_SEK"] = np.log1p(df["Pris_kr_st_SEK"])

    X = df.drop(columns=["Pris_kr_st_SEK"])
    y = df["Pris_kr_st_SEK"]

    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

    print("\n Entraînement du modèle CatBoost...")
    model = train_catboost(X_train, y_train, X_val, y_val)

    print("\n Évaluation finale...")
    rmse, mape, r2 = evaluate_model(model, X_val, y_val)

    if mape < 0.01:
        print(" Objectif atteint : MAPE < 1% ")
    else:
        print(" Encore à optimiser : MAPE > 1% ")

    print("\n Sauvegarde du modèle optimisé...")
    save_model(model, MODEL_OUTPUT_PATH)

    print(f"\n⏱ Terminé en {time.time() - start:.2f} secondes")
