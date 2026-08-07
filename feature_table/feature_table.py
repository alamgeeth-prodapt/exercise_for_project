from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,Session
import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv()
database_url = os.getenv("DATABASE_URL")
if not database_url:
    raise ValueError("Err")
engine = create_engine(database_url)
SessionLocal = sessionmaker(bind=engine)
Session = SessionLocal()
df = pd.read_csv("../data/feature_engineered_telecom_churn.csv")

df.to_sql("telecom_features",con=engine,if_exists="replace",index=False)
