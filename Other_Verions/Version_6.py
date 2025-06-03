import os, json
import torch
import torch.nn as nn
import torch.optim as optim
import pandas as pd
import numpy as np
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_percentage_error, r2_score

# === CONFIGURATION ===
DATA_DIR = "AI_Model_2/json_ready_2"
TARGET_COL = "Pris_kr_st_SEK"
EPOCHS = 3000
BATCH_SIZE = 128
LR = 0.00005

# === LOAD DATA ===
def load_data(data_dir):
    records = []
    for file in os.listdir(data_dir):
        if file.endswith(".json"):
            try:
                with open(os.path.join(data_dir, file), "r") as f:
                    records.append(json.load(f))
            except: continue
    return pd.DataFrame(records)

df = load_data(DATA_DIR)
df = df.dropna()

X = df.drop(columns=[TARGET_COL])
y = df[TARGET_COL]

# === SCALING ===
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

X_train, X_val, y_train, y_val = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

# === TORCH DATASET ===
class PriceDataset(Dataset):
    def __init__(self, X, y):
        self.X = torch.tensor(X, dtype=torch.float32)
        self.y = torch.tensor(y.values, dtype=torch.float32).view(-1, 1)
    def __len__(self): return len(self.X)
    def __getitem__(self, idx): return self.X[idx], self.y[idx]

train_loader = DataLoader(PriceDataset(X_train, y_train), batch_size=BATCH_SIZE, shuffle=True)
val_loader = DataLoader(PriceDataset(X_val, y_val), batch_size=BATCH_SIZE)

# === MODEL ===
class MLP(nn.Module):
    def __init__(self, input_dim):
        super().__init__()
        self.model = nn.Sequential(
            nn.Linear(input_dim, 512),
            nn.Tanh(),
            nn.Linear(512, 256),
            nn.Tanh(),
            nn.Linear(256, 128),
            nn.Tanh(),
            nn.Linear(128, 64),
            nn.Tanh(),
            nn.Linear(64, 1)
        )
    def forward(self, x): return self.model(x)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = MLP(X.shape[1]).to(device)

optimizer = optim.Adam(model.parameters(), lr=LR)
criterion = nn.MSELoss()

# === TRAINING ===
for epoch in range(EPOCHS):
    model.train()
    for xb, yb in train_loader:
        xb, yb = xb.to(device), yb.to(device)
        optimizer.zero_grad()
        loss = criterion(model(xb), yb)
        loss.backward()
        optimizer.step()

    # === VALIDATION ===
    model.eval()
    all_preds, all_targets = [], []
    with torch.no_grad():
        for xb, yb in val_loader:
            xb = xb.to(device)
            preds = model(xb).cpu().numpy()
            all_preds.extend(preds)
            all_targets.extend(yb.numpy())

    if (epoch+1) % 10 == 0:
        mape = mean_absolute_percentage_error(all_targets, all_preds)
        r2 = r2_score(all_targets, all_preds)
        print(f"Epoch {epoch+1}/{EPOCHS} | MAPE: {mape*100:.2f}% | R2: {r2:.4f}")

# === FINAL METRICS ===
mape = mean_absolute_percentage_error(all_targets, all_preds)
r2 = r2_score(all_targets, all_preds)
print(f"\n FINAL => MAPE: {mape*100:.3f}% | R²: {r2:.5f}")
