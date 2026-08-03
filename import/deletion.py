from sqlalchemy.orm import sessionmaker
from database import (
    engine,
    telecom_partner,
    location,
    customer,
    customer_usage
)
Session = sessionmaker(bind=engine)
session = Session()

try:
    session.query(customer_usage).delete()
    session.query(customer).delete()
    session.query(location).delete()
    session.query(telecom_partner).delete()

    session.commit()

except Exception as e:
    session.rollback()
    print("err")
finally:
    session.close()
