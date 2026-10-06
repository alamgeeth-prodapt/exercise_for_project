import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from database import engine, customer_risk
from sqlalchemy.dialects.mysql import insert
load_dotenv()

from logging_config import setup_logger

logger = setup_logger("risk_etl", "etl.log")

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not configured.")


MYSQL_JDBC_URL = os.getenv("JDBC_URL")


if not MYSQL_JDBC_URL:
    raise ValueError("MYSQL_JDBC_URL is not configured.")


spark = (
    SparkSession.builder
    .appName("CustomerRiskBatchETL")
    .master("local[*]")
    .config("spark.jars", "D:\\mysql-connector-j-26.7.0.jar") \
    .config("spark.driver.memory", "4g")
    .getOrCreate()
)

logger.info("Customer Risk ETL started")

jdbc_properties = {
    "user": "root",
    "password": "root",
    "driver": "com.mysql.cj.jdbc.Driver"
}


logger.info("Reading customer data from MySQL...")

customer_df = (
    spark.read
    .jdbc(
        url=MYSQL_JDBC_URL,
        table="customer",
        properties=jdbc_properties
    )
    .filter(
           F.col("churn") == False
       )
    .select(
        "customer_id",
        "age",
        "date_of_registration",
        "num_dependents",
        "estimated_salary",
    )
   
)


logger.info("Reading customer usage data from MySQL...")

usage_df = (
    spark.read
    .jdbc(
        url=MYSQL_JDBC_URL,
        table="customer_usage",
        properties=jdbc_properties
    )
    .select(
        "customer_id",
        "calls_made",
        "sms_sent",
        "data_used"
    )
)


logger.info("Customer rows:", customer_df.count())
logger.info("Usage rows:", usage_df.count())


df = customer_df.join(
    usage_df,
    on="customer_id",
    how="left"
)


df = df.withColumn(
    "tenure",
    F.datediff(
        F.current_date(),
        F.col("date_of_registration")
    )
)


# Tenure risk
df = df.withColumn(
    "tenure_risk",
    F.when(F.col("tenure") < 180, 2).otherwise(0)
)


# Age risk
df = df.withColumn(
    "age_risk",
    F.when(
        (F.col("age") >= 18) &
        (F.col("age") <= 30),
        1
    ).otherwise(0)
)


# Dependents risk
df = df.withColumn(
    "dependent_risk",
    F.when(
        F.col("num_dependents") <= 1,
        1
    ).otherwise(0)
)


# Calls risk
df = df.withColumn(
    "calls_risk",
    F.when(
        F.col("calls_made") < 10,
        1
    ).otherwise(0)
)


# SMS risk
df = df.withColumn(
    "sms_risk",
    F.when(
        F.col("sms_sent") < 20,
        1
    ).otherwise(0)
)


# Data usage risk
df = df.withColumn(
    "data_risk",
    F.when(
        F.col("data_used") < 500,
        1
    ).otherwise(0)
)


# High salary + low engagement
df = df.withColumn(
    "salary_engagement_risk",
    F.when(
        (F.col("estimated_salary") > 75000) &
        (F.col("calls_made") < 10) &
        (F.col("data_used") < 1),
        1
    ).otherwise(0)
)


df = df.withColumn(
    "risk_score",
    F.col("tenure_risk")
    + F.col("age_risk")
    + F.col("dependent_risk")
    + F.col("calls_risk")
    + F.col("sms_risk")
    + F.col("data_risk")
    + F.col("salary_engagement_risk")
)



df = df.withColumn(
    "risk_category",
    F.when(
        F.col("risk_score") >= 6,
        "High Risk"
    )
    .when(
        F.col("risk_score") >= 3,
        "Medium Risk"
    )
    .otherwise("Low Risk")
)


risk_df = df.select(
    "customer_id",
    "risk_score",
    "risk_category"
)


logger.info("Risk calculation completed.")

risk_df.show(20, truncate=False)


print("Risk records:", risk_df.count())

print("Risk distribution:")

(
    risk_df
    .groupBy("risk_category")
    .count()
    .orderBy("risk_category")
    .show()
)

risk_rows = risk_df.collect()


with engine.begin() as connection:

    for row in risk_rows:

        statement = insert(customer_risk).values(customer_id=row.customer_id,risk_score=row.risk_score,risk_category=row.risk_category)

        statement = statement.on_duplicate_key_update(
            risk_score=statement.inserted.risk_score,
            risk_category=statement.inserted.risk_category
        )

        connection.execute(statement)

spark.stop()

print("Customer risk batch ETL completed.")
