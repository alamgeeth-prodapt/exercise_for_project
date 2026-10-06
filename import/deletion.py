import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from sqlalchemy.orm import sessionmaker
from database import (
    engine,
    telecom_partner,
    location,
    customer,
    customer_usage,
    customer_risk
)
Session = sessionmaker(bind=engine)
session = Session()

try:
    # session.query(customer_usage).delete()
    # session.query(customer).delete()
    # session.query(location).delete()
    # session.query(telecom_partner).delete()
    session.query(customer_risk).delete()
    session.commit()

except Exception as e:
    session.rollback()
    print("err")
finally:
    session.close()
