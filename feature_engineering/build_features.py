import pandas as pd
import numpy as np
from joblib import load
from sklearn.preprocessing import StandardScaler

def build_features_for_db(data):
    reference_date = load("feature_engineering\\reference_date.joblib")
    features = load("feature_engineering\\feature_columns.joblib")
    scaler = load("feature_engineering\\scaler.joblib")
    df = pd.DataFrame([data])

    df["date_of_registration"] = pd.to_datetime(df["date_of_registration"])

    df["customer_tenure"] = abs((
        reference_date - df["date_of_registration"]
    ).dt.days)

    df["year_of_registration"] = (
        df["date_of_registration"].dt.year
    )

    df["month_of_registration"] = (
        df["date_of_registration"].dt.month
    )

    df = df.drop(columns=["date_of_registration"])
    df["gender"] = df["gender"].map({"M":0,"F":1})
    df = pd.get_dummies(
        df,
        columns=["telecom_partner", "state", "city"],
        drop_first=True,
        dtype=int
    )

    df = df.reindex(
    columns=features,
    fill_value=0
)   
    df = scaler.transform(df)
    return df

# def build_features_for_input(data):
