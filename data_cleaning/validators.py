import pandas as pd


def validate_pincode(df: pd.DataFrame, column="pincode"):
    invalid = df[~df[column].astype(str).str.match(r"^\d{6}$", na=False)]
    return invalid


def convert_boolean(df: pd.DataFrame, column):
    df[column] = df[column].astype(bool)