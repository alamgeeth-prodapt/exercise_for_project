import pandas as pd
import csv
import matplotlib.pyplot as plt
# from import.raw_insert import pincode

df = pd.read_csv("telecom_churn.csv")

# print(df.isnull().sum())
# print(df.nunique())
# print(df.dtypes)


print(df[[
    "data_used","calls_made","sms_sent"
]].describe())
# print(df.describe())

df[["data_used","calls_made","sms_sent"]] = df[["data_used","calls_made","sms_sent"]].clip(lower=0)

print(df[[
    "data_used","calls_made","sms_sent"
]].describe())

df["date_of_registration"] = pd.to_datetime(df["date_of_registration"])

print(df["date_of_registration"].dtypes)

# print(df["date_of_registration"].isna().sum())

df["pincode"] = df["pincode"].astype(str)
print(df.dtypes)

invalid = df[~df["pincode"].str.match(r"^\d{6}$")]
print(invalid)

df["churn"] = df["churn"].astype(bool)

print(df.dtypes)

df["data_used"].hist(bins=30)

plt.show()

print((df["data_used"]==0).sum())
print(df["data_used"].describe())

df.to_csv("telecom_churn_clean.csv",index=False)
