import os
import json
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import r2_score, mean_absolute_percentage_error
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer

# ------------------------------
# 1. DATA LOADING & PREPROCESSING
# ------------------------------

def load_json_data(directory):
    """Load all JSON files from specified directory"""
    all_data = []
    for file in os.listdir(directory):
        if file.endswith('.json'):
            with open(os.path.join(directory, file), encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    all_data.append(data)
                except json.JSONDecodeError:
                    print(f"Skipping invalid JSON: {file}")
    return pd.DataFrame(all_data)

# Load dataset
data_dir = "Odens/Data_Processing/json_ready"
df = load_json_data(data_dir)

# Define features and target
candidate_features = [
    "Längd_m_m", "NOT", "Verktygskostnad", "Vikt_kg_m",
    "dfm_index", "Årsvolym_st", "Kap_truml_Pris_st",
    "Lev_tid", "Råvara", 

]
target = "Pris_kr_st_SEK"

# Clean data - drop rows where target is missing
df_clean = df.dropna(subset=[target]).copy()

# ------------------------------
# 2. FEATURE ENGINEERING (TARGET-FREE)
# ------------------------------

# Create new features WITHOUT using target
df_clean['cost_per_kg'] = df_clean['Verktygskostnad'] / df_clean['Vikt_kg_m'].replace(0, np.nan)
df_clean['volume_to_length'] = df_clean['Årsvolym_st'] / df_clean['Längd_m_m'].replace(0, np.nan)
df_clean['complexity_index'] = df_clean['dfm_index'] * df_clean['wall_factor']

# Add to candidate features
candidate_features += ['cost_per_kg', 'volume_to_length', 'complexity_index']

# ------------------------------
# 3. FEATURE SELECTION
# ------------------------------

X = df_clean[candidate_features]
y = df_clean[target]

# Impute missing values for feature selection
imputer = SimpleImputer(strategy='median')
X_imputed = imputer.fit_transform(X)

# Identify top 9 features using Random Forest
rf = RandomForestRegressor(n_estimators=200, random_state=42, n_jobs=-1)
rf.fit(X_imputed, y)

feature_importances = pd.Series(rf.feature_importances_, index=candidate_features)
top_9_features = feature_importances.nlargest(9).index.tolist()

print("🔍 Top 9 Features Selected:")
print(top_9_features)

# ------------------------------
# 4. MODEL TRAINING
# ------------------------------

# Prepare final dataset with top features only
X_final = df_clean[top_9_features]
X_train, X_test, y_train, y_test = train_test_split(
    X_final, y, test_size=0.15, random_state=42
)

# Imputation and Scaling
imputer = SimpleImputer(strategy='median')
scaler = StandardScaler()

X_train_imp = imputer.fit_transform(X_train)
X_train_scaled = scaler.fit_transform(X_train_imp)

X_test_imp = imputer.transform(X_test)
X_test_scaled = scaler.transform(X_test_imp)

# Initialize XGBoost model
xgb_model = xgb.XGBRegressor(
    objective='reg:squarederror',
    n_estimators=2000,
    learning_rate=0.015,
    max_depth=5,
    subsample=0.85,
    colsample_bytree=0.92,
    gamma=0.1,
    random_state=42,
    n_jobs=-1
)

# Train with early stopping
xgb_model.fit(
    X_train_scaled, y_train,
    eval_set=[(X_test_scaled, y_test)],
    verbose=50
)

# ------------------------------
# 5. EVALUATION
# ------------------------------

# Generate predictions
y_pred = xgb_model.predict(X_test_scaled)

# Calculate metrics
r2 = r2_score(y_test, y_pred)
mape = mean_absolute_percentage_error(y_test, y_pred) * 100

print("\n EVALUATION RESULTS")
print(f" R² Score: {r2:.6f}")
print(f" MAPE: {mape:.4f}%")

# ------------------------------
# 6. MODEL PERSISTENCE
# ------------------------------

if r2 >= 0.99 and mape < 1.0:
    # Save model and preprocessing artifacts
    xgb_model.save_model('price_predictor.model')
    
    # Save preprocessing details
    preprocessing_artifacts = {
        'features': top_9_features,
        'imputer_stats': {
            'medians': imputer.statistics_.tolist()
        },
        'scaler_stats': {
            'mean': scaler.mean_.tolist(),
            'scale': scaler.scale_.tolist()
        }
    }
    
    with open('preprocessing.json', 'w') as f:
        json.dump(preprocessing_artifacts, f)
    
    print(" Model saved successfully!")
else:
    print(" Model didn't meet targets - check data quality")

# ------------------------------
# 7. PREDICTION UTILITY FOR NEW JSON
# ------------------------------

def predict_price(json_path):
    """Predict price for new JSON data without target"""
    # Load model
    model = xgb.XGBRegressor()
    model.load_model('price_predictor.model')
    
    # Load preprocessing artifacts
    with open('preprocessing.json') as f:
        artifacts = json.load(f)
    
    # Load input data
    with open(json_path) as f:
        raw_data = json.load(f)
    
    # Create input vector with required features
    input_data = {}
    for feature in artifacts['features']:
        # Use raw value if available, otherwise NaN
        input_data[feature] = raw_data.get(feature, np.nan)
    
    # Convert to DataFrame
    input_df = pd.DataFrame([input_data])
    
    # Apply preprocessing pipeline
    # 1. Impute missing values with saved medians
    input_imputed = np.where(
        input_df.isna(), 
        artifacts['imputer_stats']['medians'], 
        input_df
    )
    
    # 2. Scale features
    input_scaled = (input_imputed - artifacts['scaler_stats']['mean']) / artifacts['scaler_stats']['scale']
    
    # Predict
    return model.predict(input_scaled)[0]

# Example usage
# print(f"Predicted price: {predict_price('new_quote.json'):.2f} SEK")
