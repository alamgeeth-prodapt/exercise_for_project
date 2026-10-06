from joblib import load
model = load("feature_engineering\\log_reg.joblib")
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from routes.auth import get_current_user
from database import customer, location, telecom_partner, customer_usage, get_db
from feature_engineering.build_features import build_features_for_db
from schemas import CustomPredictionRequest

router = APIRouter(
    prefix="/prediction",
    tags=["Prediction"],
    dependencies=[Depends(get_current_user)]
)

@router.post("/custom")
def custom_prediction(
    data: CustomPredictionRequest,
    user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    proc = build_features_for_db(data.model_dump())

    pred = int(model.predict(proc)[0])
    prob = float(model.predict_proba(proc)[0][1])

    return {
        "prediction" : pred,
        "probability" : prob
    }

@router.post("/{customer_id}")
def predict(
    customer_id: int,
    user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    query2 = (
        db.query(customer.customer_id, customer.churn).filter(customer.customer_id == customer_id).first()
    )

    if query2 is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    if query2.churn:
        raise HTTPException(
            status_code=400,
            detail="already churned"
        )

    
    query = (
        db.query(
            customer.customer_id,
            customer.age,
            customer.gender,
            customer.num_dependents,
            customer.estimated_salary,
            customer.date_of_registration,
            telecom_partner.partner_name.label("telecom_partner"),
            location.state,
            location.city,
            customer_usage.calls_made,
            customer_usage.sms_sent,
            customer_usage.data_used
        )
        .join(telecom_partner,
              telecom_partner.partner_id == customer.partner_id)
        .join(location,
              location.pincode == customer.pincode)
       .join(customer_usage,
              customer_usage.customer_id == customer.customer_id)
        .filter(customer.customer_id == customer_id).first()
    )

    res = build_features_for_db(query._mapping)

    pred = int(model.predict(res)[0])
    prob = float(model.predict_proba(res)[0][1])

    return {
        "customer_id" : customer_id,
        "prediction" : pred,
        "probability" : prob
    }
