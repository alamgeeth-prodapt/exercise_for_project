from fastapi import APIRouter,Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from io import BytesIO, StringIO
from database import get_db, customer, telecom_partner, location, customer_usage, customer_risk
from schemas import CustomerPaginationResponse, CustomerResponse
import math
from routes.auth import get_current_user
import pandas as pd

router = APIRouter(
    prefix="/customer",
    tags=["Customers"],
    dependencies=[Depends(get_current_user)]
)

@router.get("/export")
def export(
    current_user: str = Depends(get_current_user),
    partner: str | None = None,
    state: str | None = None,
    city: str | None = None,
    gender: str | None = None,
    churn: bool | None = None,
    age_min: int | None = None,
    age_max: int | None = None,
    search_id: int | None = None,
    db: Session = Depends(get_db)
):
    query = (
        db.query(
            customer.customer_id,
            telecom_partner.partner_name.label("telecom_partner"),
            customer.gender,
            customer.age,
            location.state,
            location.city,
            customer.pincode,
            customer.date_of_registration,
            customer.num_dependents,
            customer.estimated_salary,
            customer_usage.calls_made,
            customer_usage.sms_sent,
            customer_usage.data_used,
            customer.churn,
            customer_risk.risk_category,
        ).join(telecom_partner, customer.partner_id == telecom_partner.partner_id
        ).join(location,customer.pincode == location.pincode
        ).join(customer_usage, customer.customer_id == customer_usage.customer_id
        ).outerjoin(customer_risk, customer.customer_id == customer_risk.customer_id)
        )


    if partner:
        query = query.filter(telecom_partner.partner_name == partner)
    if state:
        query = query.filter(location.state == state)
    if city:
        query = query.filter(location.city == city)
    if gender:
        query = query.filter(customer.gender == gender)
    if churn is not None:
        query = query.filter(customer.churn == churn)
    if age_min is not None:
        query = query.filter(customer.age >= age_min)
    if age_max is not None:
        query = query.filter(customer.age <= age_max)
    if search_id is not None:
        query = query.filter(customer.customer_id == search_id)

    results = query.order_by(customer.customer_id.asc()).all()

    output = BytesIO()

    data = [
        {
        "customer_id": row.customer_id,
        "telecom_partner": row.telecom_partner,
        "gender": row.gender,
        "age": row.age,
        "state": row.state,
        "city": row.city,
        "pincode": row.pincode,
        "date_of_registration": row.date_of_registration,
        "num_dependents": row.num_dependents,
        "estimated_salary": row.estimated_salary,
        "calls_made": row.calls_made,
        "sms_sent": row.sms_sent,
        "data_used": row.data_used,
        "churn": row.churn,
        "risk":row.risk_category
        }
        for row in results
    ]

    df = pd.DataFrame(data)

    with pd.ExcelWriter(output, "openpyxl") as writer:
        df.to_excel(
            writer,
            index=False,
            sheet_name="customers"
        )

    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
        "Content-Disposition": "attachment; filename=customers.xlsx"
        }
    )

@router.get("/", response_model=CustomerPaginationResponse)
def get_customers(
    current_user: str = Depends(get_current_user),
    page: int = 1,
    page_size: int = 20,
    partner: str | None = None,
    state: str | None = None,
    city: str | None = None,
    gender: str | None = None,
    churn: bool | None = None,
    risk_category: str | None = None,
    age_min: int | None = None, 
    age_max: int | None = None,
    search_id: int | None = None,
    db: Session = Depends(get_db)
):
    query = (
    db.query(
        customer.customer_id,
        telecom_partner.partner_name.label("telecom_partner"),
        customer.gender,
        customer.age,
        location.state,
        location.city,
        customer.pincode,
        customer.date_of_registration,
        customer.num_dependents,
        customer.estimated_salary,
        customer_usage.calls_made,
        customer_usage.sms_sent,
        customer_usage.data_used,
        customer.churn,
        customer_risk.risk_category,
    ).join(telecom_partner, customer.partner_id == telecom_partner.partner_id
    ).join(location,customer.pincode == location.pincode
    ).join(customer_usage, customer.customer_id == customer_usage.customer_id
    ).outerjoin(customer_risk, customer.customer_id == customer_risk.customer_id,).order_by(customer.customer_id.asc()
    ))
    if partner:
        query = query.filter(telecom_partner.partner_name == partner)
    if state:
        query = query.filter(location.state == state)
    if city:
        query = query.filter(location.city == city)
    if gender:
        query = query.filter(customer.gender == gender)
    if churn is not None:
        query = query.filter(customer.churn == churn)
    if age_min is not None:
        query = query.filter(customer.age >= age_min)
    if age_max is not None:
        query = query.filter(customer.age <= age_max)
    if search_id is not None:
        query = query.filter(customer.customer_id == search_id)
    if risk_category:
        query = query.filter(customer_risk.risk_category == risk_category)

    total = query.count()
    offset = (page - 1) * page_size
    results = query.offset(offset).limit(page_size).all()
    total_pages = math.ceil(total / page_size)

    customers = [
        CustomerResponse(**row._mapping)
        for row in results
    ]
    return CustomerPaginationResponse(
        total = total,
        page = page,
        page_size=page_size,
        total_pages = total_pages,
        customers = customers
    )

# @router.get("/count")
# def count_get(
#     page: int = 1,
#     page_size: int = 20,
#     partner: str | None = None,
#     state: str | None = None,
#     city: str | None = None,
#     gender: str | None = None,
#     churn: bool | None = None,
#     age_min: int | None = None,
#     age_max: int | None = None,
#     search_id: int | None = None,
#     db: Session = Depends(get_db)
# ):
#     query = (
#     db.query(customer)
#     .join(
#         telecom_partner,
#         customer.partner_id == telecom_partner.partner_id
#     )
#     .join(
#         location,
#         customer.pincode == location.pincode
#     )
#     .join(
#         customer_usage,
#         customer.customer_id == customer_usage.customer_id
#     )
# )

#     return query.count()

