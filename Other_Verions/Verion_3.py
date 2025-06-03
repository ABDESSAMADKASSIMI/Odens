import os
import json
import optuna
import joblib
import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    r2_score, mean_squared_error, mean_absolute_error,
    mean_absolute_percentage_error, max_error
)
from sklearn.preprocessing import StandardScaler

# ----------------------------------------------
# STEP 1: Load JSON to DataFrame
# ----------------------------------------------
def load_jsons(folder_path):
    records = []
    for file in os.listdir(folder_path):
        if file.endswith(".json"):
            with open(os.path.join(folder_path, file), 'r', encoding='utf-8') as f:
                try:
                    records.append(json.load(f))
                except:
                    continue
    return pd.DataFrame(records)

# ----------------------------------------------
# STEP 2: Preprocess and Split Data
# ----------------------------------------------
def preprocess(df):
    selected_features = [
        "Längd_m_m", "NOT", "dfm_index", "Verktygskostnad",
        "Vikt_kg_m", "Årsvolym_st", "Kap_truml_Pris_st",
        "Råvara", "Lev_tid"
    ]
    target = "Pris_kr_st_SEK"

    df = df[selected_features + [target]].dropna()
    X = df[selected_features]
    y = df[target]

    # Scale numeric columns
    numeric_cols = X.select_dtypes(include=[np.number]).columns
    scaler = StandardScaler()
    X.loc[:, numeric_cols] = scaler.fit_transform(X[numeric_cols])

    return train_test_split(X, y, test_size=0.2, random_state=42)

# ----------------------------------------------
# STEP 3: Optuna Objective Function
# ----------------------------------------------
def objective(trial):
    params = {
        "objective": "regression",
        "metric": "mae",
        "verbosity": -1,
        "boosting_type": "gbdt",
        "n_estimators": 1000,
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3),
        "num_leaves": trial.suggest_int("num_leaves", 20, 300),
        "max_depth": trial.suggest_int("max_depth", 3, 15),
        "min_child_samples": trial.suggest_int("min_child_samples", 5, 100),
        "subsample": trial.suggest_float("subsample", 0.5, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
        "reg_alpha": trial.suggest_float("reg_alpha", 0.0, 1.0),
        "reg_lambda": trial.suggest_float("reg_lambda", 0.0, 1.0),
    }
    model = lgb.LGBMRegressor(**params)
    model.fit(
        X_train, y_train,
        eval_set=[(X_valid, y_valid)],
        eval_metric="mae",
        callbacks=[lgb.early_stopping(50)]
    )
    preds = model.predict(X_valid)
    return mean_absolute_percentage_error(y_valid, preds)

# ----------------------------------------------
# STEP 4: Train Final Model
# ----------------------------------------------
def train_best_model(best_params):
    model = lgb.LGBMRegressor(**best_params)
    model.fit(X_train, y_train)
    return model

# ----------------------------------------------
# STEP 5: Evaluate Model
# ----------------------------------------------
def evaluate(y_true, y_pred):
    print("\n MODEL EVALUATION")
    print(f" R² Score   : {r2_score(y_true, y_pred):.5f}")
    print(f" MAPE       : {mean_absolute_percentage_error(y_true, y_pred)*100:.2f}%")
    print(f" MAE        : {mean_absolute_error(y_true, y_pred):.5f}")
    print(f" RMSE       : {mean_squared_error(y_true, y_pred, squared=False):.5f}")
    print(f" Max Error  : {max_error(y_true, y_pred):.5f}")

# ----------------------------------------------
# MAIN
# ----------------------------------------------
def main(data_folder):
    df = load_jsons(data_folder)
    global X_train, X_valid, y_train, y_valid
    X_train, X_valid, y_train, y_valid = preprocess(df)

    study = optuna.create_study(direction="minimize")
    study.optimize(objective, n_trials=50)

    print("\n Best Trial:")
    print(study.best_trial)

    best_model = train_best_model(study.best_params)
    preds = best_model.predict(X_valid)
    evaluate(y_valid, preds)

    joblib.dump(best_model, "lightgbm_selected_features.pkl")
    print("\n Model saved: lightgbm_selected_features.pkl")

# ----------------------------------------------
# Run the main process
# ----------------------------------------------
if __name__ == "__main__":
    main("Odens/Data_Processing/json_ready")
