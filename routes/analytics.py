from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db,customer,telecom_partner
from schemas import ChurnRateAnalyticsResponse,CustomerDistributionResponse
from sqlalchemy import func
router = APIRouter(prefix="/analytics",tags=["Analytics"])


@router.get("/churn-rate", response_model=list[ChurnRateAnalyticsResponse])
def churn_rate(
    db: Session =  Depends(get_db)
):
    query = db.query(telecom_partner.partner_name,customer.churn,func.count(customer.customer_id).label("customer_count")).join(customer,customer.partner_id==telecom_partner.partner_id).group_by(telecom_partner.partner_name,customer.churn).all()
    rates = {}

    for res in query:
        partner = res.partner_name
        churn = res.churn
        count = res.customer_count

        if partner not in rates:
            rates[partner] = {
                "total": 0,
                "churned": 0
            }

        rates[partner]["total"] += count

        if churn:
            rates[partner]["churned"] += count
    responses = []

    for partner, data in rates.items():
        churn_rate = (data["churned"] / data["total"]) * 100

        responses.append(
            ChurnRateAnalyticsResponse(
                telecom_partner=partner,
                churn_rate=churn_rate
            )
        )
    return responses


@router.get("/distribution", response_model=CustomerDistributionResponse)
def distribution(
    db: Session = Depends(get_db)
):
    query = db.query(telecom_partner.partner_name, func.count(customer.customer_id).label("customer_count")).join(customer,customer.partner_id==telecom_partner.partner_id).group_by(telecom_partner.partner_name).all()

    partners = {}

    for res in query:
        partners[res.partner_name] = res.customer_count

    total_customers = sum(partners.values())

    return CustomerDistributionResponse(
        total_customers=total_customers,
        partners=partners
    )