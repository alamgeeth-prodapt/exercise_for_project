from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db,customer,telecom_partner, customer_risk
from schemas import ChurnRateAnalyticsResponse,CustomerDistributionResponse, RiskBucket
from sqlalchemy import func, case
from routes.auth import get_current_user
router = APIRouter(prefix="/analytics",tags=["Analytics"], dependencies=[Depends(get_current_user)])


@router.get("/churn-rate", response_model=list[ChurnRateAnalyticsResponse])
def churn_rate(
    current_user: str = Depends(get_current_user),
    db: Session =  Depends(get_db),
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
    current_user: str = Depends(get_current_user),
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

@router.get("/age-distribution") 
def get_age_distribution(db: Session = Depends(get_db)): 
    result = db.query( 
        func.sum( 
            case( 
                (customer.age.between(18, 25), 1), else_=0 ) ).label("18-25"), 

        func.sum( 
            case( 
                (customer.age.between(26, 35), 1), else_=0 ) ).label("26-35"), 

        func.sum( 
            case( 
                (customer.age.between(36, 45), 1), else_=0 ) ).label("36-45"), 

        func.sum( 
            case( 
                (customer.age.between(46, 55), 1), else_=0 ) ).label("46-55"), 

        func.sum( 
            case( 
                (customer.age.between(56, 65), 1), else_=0 ) ).label("56-65"), 

        func.sum( 
            case( 
                (customer.age >= 66, 1), else_=0 ) ).label("66+") ).first() 

    return [ 
        {"label": "18–25", "count": result[0]}, 
        {"label": "26–35", "count": result[1]}, 
        {"label": "36–45", "count": result[2]}, 
        {"label": "46–55", "count": result[3]}, 
        {"label": "56–65", "count": result[4]}, 
        {"label": "66+", "count":   result[5]}, 
        ]

@router.get("/gender-distribution")
def get_gender_distribution(db: Session = Depends(get_db)): 
    results = db.query(telecom_partner.partner_name, 
                func.sum( case( (customer.gender == "M", 1), else_=0 ) ).label("M"), 

                func.sum( case( (customer.gender == "F", 1), else_=0 ) ).label("F") ).join(telecom_partner,customer.partner_id == telecom_partner.partner_id).group_by(telecom_partner.partner_name).all() 

    return [ { "partner": row.partner_name, "M": row.M, "F": row.F } for row in results ]

@router.get("/risk-distribution", response_model=list[RiskBucket])
def get_risk_distribution(db: Session = Depends(get_db)):
    res = (
        db.query(customer_risk.risk_category, func.count(customer.customer_id)).join(customer, customer.customer_id == customer_risk.customer_id).group_by(customer_risk.risk_category).all()
    )

    return [RiskBucket(risk_category=key, count=value) for key, value in res]
