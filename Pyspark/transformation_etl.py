from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    datediff,
    abs,
    year,
    month,
    when,
    lit,
)


BASE_DIR = Path(__file__).resolve().parent

INPUT_PATH = BASE_DIR / "telecom_churn_clean_spark"
OUTPUT_PATH = BASE_DIR / "telecom_churn_features"


spark = (
    SparkSession.builder
    .appName("TelecomChurnFeatureEngineeringETL")
    .master("local[*]")
    .config("spark.driver.memory", "4g")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")


print("\n========== LOADING CLEANED DATA ==========")

df = (
    spark.read
    .option("header", True)
    .option("inferSchema", True)
    .csv(str(INPUT_PATH))
)

print(f"Rows: {df.count()}")
print(f"Columns: {len(df.columns)}")


REFERENCE_DATE = "2026-08-01"

print("\n========== DATE FEATURE ENGINEERING ==========")

df = df.withColumn(
    "date_of_registration",
    col("date_of_registration").cast("date")
)

df = df.withColumn(
    "customer_tenure",
    abs(
        datediff(
            lit(REFERENCE_DATE).cast("date"),
            col("date_of_registration")
        )
    )
)

df = df.withColumn(
    "year_of_registration",
    year(col("date_of_registration"))
)

df = df.withColumn(
    "month_of_registration",
    month(col("date_of_registration"))
)


df = df.drop("date_of_registration")


print("\n========== GENDER ENCODING ==========")

df = df.withColumn(
    "gender",
    when(col("gender") == "M", 0)
    .when(col("gender") == "F", 1)
    .otherwise(None)
)


df = df.drop(
    "customer_id",
    "pincode"
)


categorical_columns = [
    "telecom_partner",
    "state",
    "city"
]


for column_name in categorical_columns:

    print(
        f"\nEncoding categorical column: "
        f"{column_name}"
    )

    categories = (
        df
        .select(column_name)
        .distinct()
        .where(col(column_name).isNotNull())
        .rdd
        .map(lambda row: row[0])
        .collect()
    )

    categories = sorted(categories)

    print(f"Categories: {categories}")

    # Equivalent to pandas drop_first=True
    categories_to_encode = categories[1:]

    for category in categories_to_encode:

        # Create the same style of column name
        feature_name = (
            f"{column_name}_{category}"
        )

        df = df.withColumn(
            feature_name,
            when(
                col(column_name) == category,
                1
            ).otherwise(0)
        )

    # Remove original categorical column
    df = df.drop(column_name)


target_column = "churn"

feature_columns = [
    column_name
    for column_name in df.columns
    if column_name != target_column
]

df = df.select(
    feature_columns + [target_column]
)

print("\n========== FINAL FEATURE DATASET ==========")

print(f"Rows: {df.count()}")
print(f"Columns: {len(df.columns)}")

print("\nFeature columns:")

for column_name in df.columns:
    print(column_name)

df.show(10, truncate=False)


print("\n========== WRITING FEATURE DATASET ==========")

(
    df.write
    .mode("overwrite")
    .option("header", True)
    .csv(str(OUTPUT_PATH))
)

print(
    f"Feature dataset written to:\n"
    f"{OUTPUT_PATH}"
)


spark.stop()

print("\n========== TRANSFORMATION ETL COMPLETE ==========")