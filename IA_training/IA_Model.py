import os
import sys
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import xgboost as xgb
import joblib
import time

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPRegressor
from sklearn.ensemble import VotingRegressor
from sklearn.metrics import (
    r2_score,
    mean_absolute_error,
    mean_squared_error,
    mean_absolute_percentage_error,
    max_error
)

# ==== CORRECTION ABSOLUE DES CHEMINS ====
def absolute_path(*args):
    """Always return an absolute normalized path, cross-platform."""
    return os.path.abspath(os.path.join(*args))

# Set up paths
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, ".."))
data_processing_dir = os.path.join(parent_dir, "Data_Processing")
sys.path.extend([parent_dir, data_processing_dir])

from Data_Processing.main_Data_Processing import main as run_data_processing
from Data_Processing.main_Data_Processing import copy_extra_json_folder_into_ready_folder

def json_to_csv(folder_path, output_csv):
    records = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".json"):
            path = os.path.join(folder_path, filename)
            with open(path, 'r', encoding='utf-8') as f:
                try:
                    records.append(json.load(f))
                except Exception:
                    pass
    df = pd.DataFrame(records)
    df.to_csv(output_csv, index=False)
    print(f"✅ Converted {len(df)} JSONs to CSV at: {output_csv}")
    return df

def style_plot(ax):
    ax.set_facecolor("#192233")
    for spine in ax.spines.values():
        spine.set_color("white")
    ax.tick_params(axis='x', colors='white', labelsize=13)
    ax.tick_params(axis='y', colors='white', labelsize=13)
    ax.xaxis.label.set_color('white')
    ax.yaxis.label.set_color('white')
    ax.title.set_color('white')
    ax.grid(True, color='white', alpha=0.11)

def train_model(csv_path, assets_path):
    start_time = time.time()
    # === Correction: always absolute
    assets_path = absolute_path(assets_path)

    df = pd.read_csv(csv_path)
    df = df.drop(columns=["symmetry_score"], errors="ignore")

    y = df["Pris_kr_st_SEK"]

    selected_features = [
        "Längd_m_m",
        "NOT",
        "Årsvolym_st",
        "Verktygskostnad",
        "Vikt_kg_m",
        "dfm_index",
        "area_to_length",
        "Råvara",
        "Lev_tid"
    ]

    X = df[selected_features]

    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)

    mlp = MLPRegressor(
        hidden_layer_sizes=(1024, 512, 256, 128, 64),
        learning_rate_init=0.00005,
        max_iter=5000,
        early_stopping=True,
        random_state=42
    )

    xgb_model = xgb.XGBRegressor(
        n_estimators=500,
        max_depth=6,
        learning_rate=0.03,
        subsample=0.8,
        colsample_bytree=0.8,
        tree_method='hist',
        device='cuda',
        random_state=42
    )

    model = VotingRegressor([('mlp', mlp), ('xgb', xgb_model)])
    model.fit(X_train_scaled, y_train)

    y_pred = model.predict(X_val_scaled)
    y_true = y_val

    r2 = r2_score(y_true, y_pred)
    mape = mean_absolute_percentage_error(y_true, y_pred)
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    maxerr = max_error(y_true, y_pred)

    print(f"\n📊 EVALUATION")
    print(f"✅ R² Score   : {r2:.5f}")
    print(f"✅ MAPE       : {mape*100:.2f}%")
    print(f"✅ MAE        : {mae:.4f}")
    print(f"✅ RMSE       : {rmse:.4f}")
    print(f"✅ Max Error  : {maxerr:.4f}")

    # === SAVE MODEL + SCALER always absolute ===
    model_path = absolute_path(assets_path, "IA_")
    os.makedirs(model_path, exist_ok=True)
    joblib.dump(model, os.path.join(model_path, "ensemble_model.pkl"))
    joblib.dump(scaler, os.path.join(model_path, "scaler.pkl"))

    # === SAVE STATS IMAGES always absolute ===
    stats_dir = absolute_path(model_path, "Statistiques")
    os.makedirs(stats_dir, exist_ok=True)

    def save_plot(fig, name):
        save_path = absolute_path(stats_dir, name)
        print(f"[DEBUG] Saving stat image: {save_path}")
        fig.savefig(save_path, bbox_inches="tight", facecolor=fig.get_facecolor())
        plt.close()

    # --- PLOT 1: Error Distribution ---
    # 1. Error Distribution
    # 1. Error Distribution
    fig, ax = plt.subplots(figsize=(6.5, 4.3))
    sns.histplot(y_true - y_pred, bins=40, kde=True, color="white", edgecolor="white", alpha=0.7, ax=ax)
    ax.set_facecolor("#192233")
    fig.patch.set_facecolor("#192233")
    ax.set_title("Error Distribution", color="white")
    ax.set_xlabel("Prediction Error", color="white")
    ax.set_ylabel("Count", color="white")
    ax.tick_params(axis='x', colors='white')
    ax.tick_params(axis='y', colors='white')
    for spine in ax.spines.values():
        spine.set_color("white")
    plt.tight_layout()
    fig.savefig(os.path.join(stats_dir, "error_distribution.png"), facecolor=fig.get_facecolor())
    plt.close(fig)

    # 2. True vs Predicted
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.scatter(y_true, y_pred, c="white", alpha=0.7)
    ax.set_facecolor("#192233")
    fig.patch.set_facecolor("#192233")
    ax.set_title("True vs Predicted", color="white")
    ax.set_xlabel("True Value", color="white")
    ax.set_ylabel("Predicted Value", color="white")
    ax.tick_params(axis='x', colors='white')
    ax.tick_params(axis='y', colors='white')
    for spine in ax.spines.values():
        spine.set_color("white")
    plt.tight_layout()
    fig.savefig(os.path.join(stats_dir, "true_vs_pred.png"), facecolor=fig.get_facecolor())
    plt.close(fig)

    # 3. Residuals
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.scatter(y_pred, y_true - y_pred, c="orange", alpha=0.5)
    ax.set_facecolor("#192233")
    fig.patch.set_facecolor("#192233")
    ax.set_title("Residuals Plot", color="white")
    ax.set_xlabel("Predicted Value", color="white")
    ax.set_ylabel("Residual", color="white")
    ax.tick_params(axis='x', colors='white')
    ax.tick_params(axis='y', colors='white')
    for spine in ax.spines.values():
        spine.set_color("white")
    plt.tight_layout()
    fig.savefig(os.path.join(stats_dir, "residuals.png"), facecolor=fig.get_facecolor())
    plt.close(fig)



    # Tu peux ajouter d'autres stats ici avec save_plot(fig, "autre_nom.png")

    duration = time.time() - start_time
    hours, rem = divmod(duration, 3600)
    minutes, seconds = divmod(rem, 60)
    formatted_time = f"{int(hours)}h {int(minutes)}min {int(seconds)}s" if hours >= 1 else f"{int(minutes)}min {int(seconds)}s"

    report_path = os.path.join(model_path, "training_report.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("📅 MODEL TRAINING REPORT\n")
        f.write(f"✅ R² Score   : {r2:.5f}\n")
        f.write(f"✅ MAPE       : {mape*100:.2f}%\n")
        f.write(f"✅ MAE        : {mae:.4f}\n")
        f.write(f"✅ RMSE       : {rmse:.4f}\n")
        f.write(f"✅ Max Error  : {maxerr:.4f}\n")
        f.write(f"⏱️ Total Training Time: {formatted_time}\n")

    print(f"\n📅 Metrics saved to: {report_path}")

def Model_Training(input_dir, output_dir, assets_path, extra_json_folder=None):
    # Always make sure paths are absolute (robust in any context)
    input_dir = absolute_path(input_dir)
    output_dir = absolute_path(output_dir)
    assets_path = absolute_path(assets_path)
    if extra_json_folder:
        extra_json_folder = absolute_path(extra_json_folder)

    run_data_processing(input_dir, output_dir, extra_json_folder)

    json_input = os.path.join(output_dir, "json_ready")
    csv_output = os.path.join(output_dir, "all_quotes.csv")

    json_to_csv(json_input, csv_output)
    train_model(csv_output, assets_path)

    # === SUPPRESSION CONTENU PATH4 ===
    if extra_json_folder and os.path.exists(extra_json_folder):
        import shutil
        try:
            shutil.rmtree(extra_json_folder)
            os.makedirs(extra_json_folder, exist_ok=True)
            print(f"✅ extra_json_folder ({extra_json_folder}) cleaned after training.")
        except Exception as e:
            print(f"⚠️ Error deleting extra_json_folder ({extra_json_folder}): {e}")


if __name__ == "__main__":
    Model_Training(
        input_dir="Odens/Data_Processing/Test files",
        output_dir="Odens/Data_Processing",
        assets_path="Odens/IA_training",
        extra_json_folder="Odens/Data_Processing/extra_jsons"
    )
