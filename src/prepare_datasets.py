import os
import pandas as pd
from pathlib import Path

DATA_DIR = Path("../datasets")
OUT_DIR = Path("../datasets/prepared")
OUT_DIR.mkdir(parents=True, exist_ok=True)

def unify_and_split():
    csvs = list(DATA_DIR.glob("*.csv"))
    if not csvs:
        print("Nenhum dataset encontrado.")
        return

    dfs = [pd.read_csv(c) for c in csvs]
    df = pd.concat(dfs).sample(frac=1, random_state=42)

    n = len(df)
    train = df.iloc[:int(0.7*n)]
    val = df.iloc[int(0.7*n):int(0.85*n)]
    test = df.iloc[int(0.85*n):]

    train.to_csv(OUT_DIR/"train.csv", index=False)
    val.to_csv(OUT_DIR/"val.csv", index=False)
    test.to_csv(OUT_DIR/"test.csv", index=False)

    print("Datasets gerados.")
