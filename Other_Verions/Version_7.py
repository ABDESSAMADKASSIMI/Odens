import os
import json
import pandas as pd
import xgboost as xgb
import matplotlib.pyplot as plt
import seaborn as sns

def feature_importance_from_json_folder(
    json_folder,
    target_column="Pris_kr_st_SEK",
    exclude_cols=None,
    top_n=20,
    output_plot_path="feature_importance.png"
):
    records = []
    for filename in os.listdir(json_folder):
        if filename.endswith(".json"):
            filepath = os.path.join(json_folder, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                try:
                    records.append(json.load(f))
                except Exception as e:
                    print(f" Error reading {filename}: {e}")

    if not records:
        raise ValueError(" No valid JSON files found in the folder.")

    df = pd.DataFrame(records)
    df = df.drop(columns=["symmetry_score"], errors="ignore")

    if exclude_cols is None:
        exclude_cols = []

    exclude_cols = set(exclude_cols + [target_column, "price_per_kg", "price_per_meter", "cost_efficiency"])
    features = [col for col in df.columns if col not in exclude_cols]

    if target_column not in df.columns:
        raise KeyError(f" Target column '{target_column}' not found in data.")

    X = df[features]
    y = df[target_column]

    model = xgb.XGBRegressor(n_estimators=100, max_depth=4, random_state=42)
    model.fit(X, y)

    importance_df = pd.DataFrame({
        "Feature": features,
        "Importance": model.feature_importances_
    }).sort_values(by="Importance", ascending=False)

    # Plot
    plt.figure(figsize=(10, 6))
    sns.barplot(data=importance_df.head(top_n), x="Importance", y="Feature", palette="Blues_d")
    plt.title("Top Feature Importances (no leakage)")
    plt.tight_layout()
    plt.savefig(output_plot_path)
    plt.show()

    print(f" Feature importance plot saved to: {output_plot_path}")
    return importance_df

# Exemple : adapte le chemin ici
if __name__ == "__main__":
    json_folder = "Odens/Data_Processing/json_ready"  # Mets le chemin réel vers tes JSONs
    feature_importance_from_json_folder(json_folder)
