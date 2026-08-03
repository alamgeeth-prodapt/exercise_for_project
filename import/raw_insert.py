import csv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import engine, telecom_partner,location,customer,customer_usage
from datetime import datetime

Session = sessionmaker(bind=engine)
session = Session()

partners = set()

with open("telecom_churn_clean.csv","r",encoding="utf-8") as f:
    reader = csv.DictReader(f)

    for row in reader:
        if row["telecom_partner"] not in partners:
            partners.add(row["telecom_partner"])

for partner in partners:
    session.add(
        telecom_partner(
            partner_name = partner
        )
    )

session.commit()

locations = {}

with open("telecom_churn_clean.csv","r",encoding="utf-8") as f:
    reader = csv.DictReader(f)

    for row in reader:
        locations[row["pincode"]] = (
            row["city"],
            row["state"]
        )

for pincode,values in locations.items():
    city,state = values

    session.add(
        location(
            pincode = pincode,
            city = city,
            state = state
        )
    )

session.commit()

partner_lookup = {
    p.partner_name: p.partner_id
    for p in session.query(telecom_partner).all()
}

with open("telecom_churn_clean.csv","r",encoding="utf-8") as f:
    reader = csv.DictReader(f)

    for row in reader:

        cust = customer(
            customer_id = int(row["customer_id"]),
            partner_id = partner_lookup[row["telecom_partner"]],
            pincode = row["pincode"],
            gender=row["gender"],
            age=int(row["age"]),
            date_of_registration=datetime.strptime(
                row["date_of_registration"],
                "%Y-%m-%d"
            ).date(),
            num_dependents=int(row["num_dependents"]),
            estimated_salary=float(row["estimated_salary"]),
            churn = (row["churn"].lower()=="true")
        )

        session.add(cust)

session.commit()

with open("telecom_churn_clean.csv","r",encoding="utf-8") as f:
    reader = csv.DictReader(f)

    for row in reader:
        usage = customer_usage(
            customer_id=int(row["customer_id"]),
            calls_made=int(row["calls_made"]),
            sms_sent=int(row["sms_sent"]),
            data_used=float(row["data_used"])
        )

        session.add(usage)

session.commit()


session.close()
