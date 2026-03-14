"""
Download the UCI Diabetes 130-US Hospitals dataset and process it
into the 6-column format used for model training.

Run once before training:
    python scripts/prepare_data.py

Source: https://archive.ics.uci.edu/dataset/296/diabetes+130-us+hospitals+for+years+1999-2008
101,766 diabetic patients from 130 US hospitals (1999-2008).
Target: readmitted within 30 days (binary).
"""

import os
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def download_raw():
    from ucimlrepo import fetch_ucirepo
    print("Downloading UCI Diabetes 130-US Hospitals dataset...")
    ds = fetch_ucirepo(id=296)
    raw = ds.data.features.copy()
    raw['readmitted'] = ds.data.targets['readmitted'].values
    os.makedirs("data/raw", exist_ok=True)
    raw.to_csv("data/raw/diabetes_readmission.csv", index=False)
    print(f"Saved {len(raw):,} rows to data/raw/diabetes_readmission.csv")
    return raw


def process(raw):
    df = raw.copy()

    # Age: convert ranges like "[70-80)" to midpoint integer
    def age_midpoint(s):
        s = str(s).strip()
        if s.startswith('['):
            low = int(s[1:s.index('-')])
            high = int(s[s.index('-')+1:s.index(')')])
            return (low + high) // 2
        return np.nan

    df['age_int'] = df['age'].apply(age_midpoint)

    # Keep only Male/Female
    df = df[df['gender'].isin(['Male', 'Female'])].copy()

    processed = pd.DataFrame({
        'age':               df['age_int'],
        'num_conditions':    df['number_diagnoses'],
        'num_medications':   df['num_medications'],
        'recent_encounters': df['number_inpatient'],
        'gender':            df['gender'].str.lower(),
        'readmitted':        df['readmitted'].map({'<30': 1, '>30': 0, 'NO': 0}),
    }).dropna().astype(int)

    os.makedirs("data/processed", exist_ok=True)
    processed.to_csv("data/processed/patients.csv", index=False)
    print(f"Processed {len(processed):,} patients saved to data/processed/patients.csv")
    print(f"Readmitted within 30 days: {processed['readmitted'].sum():,} ({processed['readmitted'].mean()*100:.1f}%)")
    return processed


if __name__ == "__main__":
    raw_path = "data/raw/diabetes_readmission.csv"
    if os.path.exists(raw_path):
        print(f"Raw file already exists — loading from {raw_path}")
        raw = pd.read_csv(raw_path)
    else:
        raw = download_raw()
    process(raw)
