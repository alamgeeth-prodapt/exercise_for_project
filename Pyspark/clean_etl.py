from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    to_date,
    when,
    trim,
)
from pyspark.sql.types import (
    BooleanType,
    IntegerType,
    DecimalType,
)


# ============================================================
# 1. Spark Session
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

INPUT_PATH = BASE_DIR / "telecom_churn.csv"
OUTPUT_PATH = BASE_DIR / "telecom_churn_clean_spark"


spark = (
    SparkSession.builder
    .appName("TelecomChurnCleaningETL")
    .master("local[*]")
    .config("spark.driver.memory", "4g")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")


# ============================================================
# 2. Load Data
# ============================================================

print("\n========== LOADING DATA ==========")

df = (
    spark.read
    .option("header", True)
    .option("inferSchema", True)
    .csv(str(INPUT_PATH))
)

print(f"Initial row count: {df.count()}")
print(f"Initial columns: {len(df.columns)}")

df.printSchema()


# ============================================================
# 3. Clean Numeric Columns
# ============================================================
#
# Equivalent to:
#
# self.df[columns] = self.df[columns].clip(lower=0)
#
# in the Pandas implementation.
#
# Negative values are converted to 0.
# ============================================================

print("\n========== CLEANING NUMERIC COLUMNS ==========")

numeric_columns = [
    "data_used",
    "calls_made",
    "sms_sent"
]

for column_name in numeric_columns:

    negative_count = df.filter(
        col(column_name) < 0
    ).count()

    print(
        f"{column_name}: "
        f"{negative_count} negative values found"
    )

    df = df.withColumn(
        column_name,
        when(
            col(column_name) < 0,
            0
        ).otherwise(
            col(column_name)
        )
    )


# ============================================================
# 4. Normalize Dates
# ============================================================
#
# Equivalent to:
#
# pd.to_datetime(..., errors="coerce")
#
# Invalid dates become NULL in Spark.
# ============================================================

print("\n========== NORMALIZING DATES ==========")

df = df.withColumn(
    "date_of_registration",
    to_date(
        col("date_of_registration"),
        "yyyy-MM-dd"
    )
)

invalid_date_count = df.filter(
    col("date_of_registration").isNull()
).count()

print(
    f"Invalid / NULL registration dates: "
    f"{invalid_date_count}"
)


# ============================================================
# 5. Validate Pincodes
# ============================================================
#
# Your existing validator is external:
#
# validate_pincode(self.df)
#
# We reproduce the validation logic here by checking that
# pincodes contain exactly 6 digits.
#
# Change this rule if your validators.py uses a different
# validation rule.
# ============================================================

print("\n========== VALIDATING PINCODES ==========")

df = df.withColumn(
    "pincode",
    trim(col("pincode").cast("string"))
)

invalid_pincode_df = df.filter(
    ~col("pincode").rlike("^[0-9]{6}$")
)

invalid_pincode_count = invalid_pincode_df.count()

print(
    f"Invalid pincodes: "
    f"{invalid_pincode_count}"
)

if invalid_pincode_count > 0:
    invalid_pincode_df.select(
        "customer_id",
        "pincode"
    ).show(20, truncate=False)


# ============================================================
# 6. Convert Churn
# ============================================================
#
# Equivalent to:
#
# convert_boolean(self.df, "churn")
#
# We support common representations:
#
# 0 / 1
# True / False
# "true" / "false"
# ============================================================

print("\n========== CONVERTING CHURN ==========")

df = df.withColumn(
    "churn",
    when(
        col("churn").cast("string").isin(
            "1",
            "true",
            "True",
            "TRUE"
        ),
        True
    )
    .when(
        col("churn").cast("string").isin(
            "0",
            "false",
            "False",
            "FALSE"
        ),
        False
    )
    .otherwise(None)
    .cast(BooleanType())
)

invalid_churn_count = df.filter(
    col("churn").isNull()
).count()

print(
    f"NULL / invalid churn values: "
    f"{invalid_churn_count}"
)


# ============================================================
# 7. Data Usage Summary
# ============================================================
#
# Equivalent to:
#
# (self.df["data_used"] == 0).sum()
# ============================================================

print("\n========== TELECOM SUMMARY ==========")

zero_data_usage = df.filter(
    col("data_used") == 0
).count()

print(
    f"Customers with data_used = 0: "
    f"{zero_data_usage}"
)


# ============================================================
# 8. Final Data Summary
# ============================================================

print("\n========== FINAL DATA SUMMARY ==========")

print(f"Final row count: {df.count()}")
print(f"Final column count: {len(df.columns)}")

df.printSchema()

df.describe().show()


# ============================================================
# 9. Display Sample
# ============================================================

print("\n========== CLEANED DATA SAMPLE ==========")

df.show(
    10,
    truncate=False
)


# ============================================================
# 10. Write Cleaned Dataset
# ============================================================

print("\n========== WRITING CLEANED DATA ==========")

(
    df.write
    .mode("overwrite")
    .option("header", True)
    .csv(str(OUTPUT_PATH))
)

print(
    f"Cleaned dataset written to:\n"
    f"{OUTPUT_PATH}"
)


# ============================================================
# 11. Stop Spark
# ============================================================

spark.stop()

print("\n========== CLEANING ETL COMPLETE ==========")