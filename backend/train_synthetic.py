# backend/train_synthetic.py
import os
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.model_selection import train_test_split
import joblib, json

os.makedirs("backend/models", exist_ok=True)

def gen_fractions(total):
    if total < 150:
        shares = np.array([0.35, 0.05, 0.20, 0.25, 0.15])
    elif total < 400:
        shares = np.array([0.30, 0.20, 0.18, 0.18, 0.14])
    else:
        shares = np.array([0.20, 0.45, 0.12, 0.13, 0.10])
    noise = np.random.normal(0, 0.05, 5)
    shares = np.abs(shares + noise)
    shares = shares / shares.sum()
    return shares

def create_dataset(n=3000, seed=42):
    np.random.seed(seed)
    rows = []
    for _ in range(n):
        total = int(np.random.randint(50, 1200))
        month = int(np.random.randint(1,13))
        household_size = int(np.random.randint(1,6))
        fr = gen_fractions(total)
        fan, ac, fridge, lights, geyser = (fr * total)
        rows.append([total, month, household_size,
                     round(fan,1), round(ac,1), round(fridge,1), round(lights,1), round(geyser,1)])
    cols = ['total','month','household_size','fan','ac','fridge','lights','geyser']
    return pd.DataFrame(rows, columns=cols)

def train_and_save(df, model_path="backend/models/appliance_model.joblib", meta_path="backend/models/metrics.json"):
    X = df[['total','month','household_size']]
    y = df[['fan','ac','fridge','lights','geyser']]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.15, random_state=42)

    model = MultiOutputRegressor(RandomForestRegressor(n_estimators=120, random_state=42, n_jobs=-1))
    model.fit(X_train, y_train)
    joblib.dump(model, model_path)
    print("Saved model to", model_path)

    preds = model.predict(X_test)
    y_true = y_test.values

    # compute per-target MAE and MAPE
    mae = np.mean(np.abs(preds - y_true), axis=0).tolist()
    mape = (np.mean(np.abs((preds - y_true) / np.maximum(y_true, 1e-6)), axis=0) * 100).tolist()
    targets = ['fan','ac','fridge','lights','geyser']
    metrics = {targets[i]: {"MAE": round(mae[i],2), "MAPE%": round(mape[i],2)} for i in range(len(targets))}
    metrics["overall_mean_MAE"] = round(float(np.mean(mae)),2)
    metrics["overall_mean_MAPE%"] = round(float(np.mean(mape)),2)

    with open(meta_path, "w") as f:
        json.dump(metrics, f, indent=2)

    print("Saved metrics to", meta_path)
    print("Metrics summary:", metrics)

if __name__ == "__main__":
    print("Creating synthetic dataset...")
    df = create_dataset(n=3000)
    train_and_save(df)
