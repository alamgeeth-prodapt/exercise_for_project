"""
Tools definition and execution engine for the Telecom Churn Assistant.
Provides Claude with structured tool schemas and executes queries against the
database and ML prediction pipelines.
"""

from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, case
import os
from joblib import load
from datetime import date

from database import customer, telecom_partner, location, customer_usage, customer_risk
from feature_engineering.build_features import build_features_for_db

# Load trained logistic regression model safely
MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "feature_engineering", "log_reg.joblib")
_ml_model = None

def get_model():
    global _ml_model
    if _ml_model is None:
        _ml_model = load(MODEL_PATH)
    return _ml_model


# ==============================================================================
# ANTHROPIC TOOL SCHEMAS
# ==============================================================================
ANTHROPIC_TOOLS = [
    {
        "name": "get_churn_analytics",
        "description": "Retrieve comprehensive telecom churn metrics, including overall platform churn rate, partner-by-partner churn percentages, and identification of the highest and lowest churn risk telecom partners.",
        "input_schema": {
            "type": "object",
            "properties": {
                "partner": {
                    "type": "string",
                    "description": "Optional specific telecom partner name to filter on ('Airtel', 'BSNL', 'Reliance Jio', 'Vodafone'). Leave empty to compare all operators."
                }
            }
        }
    },
    {
        "name": "get_customer_distribution",
        "description": "Retrieve total subscriber count across the network and market share distribution across all telecom partners (Airtel, BSNL, Reliance Jio, Vodafone).",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "get_demographics_distribution",
        "description": "Retrieve demographic breakdowns of subscribers, including age bracket distribution (18-25, 26-35, 36-45, 46-55, 56-65, 66+) and gender distribution per telecom operator.",
        "input_schema": {
            "type": "object",
            "properties": {
                "dimension": {
                    "type": "string",
                    "enum": ["all", "age", "gender"],
                    "description": "Whether to return 'age' distribution, 'gender' distribution, or 'all' (default)."
                }
            }
        }
    },
    {
        "name": "get_risk_distribution",
        "description": "Retrieve the platform-wide distribution of customers across behavioral risk buckets ('Low Risk', 'Medium Risk', 'High Risk').",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "search_customers",
        "description": "Filter and search subscribers by telecom partner, geographic location (state/city), gender, churn status, risk category, or age range. Returns matching subscriber records with usage metrics.",
        "input_schema": {
            "type": "object",
            "properties": {
                "partner": {
                    "type": "string",
                    "description": "Filter by operator: 'Airtel', 'BSNL', 'Reliance Jio', or 'Vodafone'"
                },
                "state": {
                    "type": "string",
                    "description": "Filter by Indian state name (e.g. 'Maharashtra', 'Tamil Nadu', 'Delhi')"
                },
                "city": {
                    "type": "string",
                    "description": "Filter by city name"
                },
                "gender": {
                    "type": "string",
                    "enum": ["M", "F"],
                    "description": "Filter by gender ('M' or 'F')"
                },
                "churn": {
                    "type": "boolean",
                    "description": "true for churned customers, false for retained active customers"
                },
                "risk_category": {
                    "type": "string",
                    "enum": ["Low Risk", "Medium Risk", "High Risk"],
                    "description": "Filter by risk tier"
                },
                "age_min": {
                    "type": "integer",
                    "description": "Minimum subscriber age"
                },
                "age_max": {
                    "type": "integer",
                    "description": "Maximum subscriber age"
                },
                "search_id": {
                    "type": "integer",
                    "description": "Search by exact customer_id"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum records to return (default 10, max 25)"
                }
            }
        }
    },
    {
        "name": "get_customer_profile",
        "description": "Retrieve the complete 360-degree profile for a specific subscriber ID, including personal demographics, registration date, number of dependents, salary, monthly usage (calls, SMS, data in MB), risk score, and current churn status.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "integer",
                    "description": "The unique numerical identifier of the subscriber"
                }
            },
            "required": ["customer_id"]
        }
    },
    {
        "name": "predict_customer_churn",
        "description": "Execute the machine learning prediction model on a specific active subscriber from the database. Calculates their exact churn probability percentage, prediction outcome (Retain or Churn), and contextual usage comparison.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "integer",
                    "description": "The unique subscriber ID to evaluate"
                }
            },
            "required": ["customer_id"]
        }
    },
    {
        "name": "simulate_custom_prediction",
        "description": "Simulate and test 'what-if' churn prediction scenarios for hypothetical subscriber profiles or plan modifications. Useful for answering questions like 'What happens if we increase data usage to 30 GB?' or evaluating new subscriber risk profiles.",
        "input_schema": {
            "type": "object",
            "properties": {
                "telecom_partner": {
                    "type": "string",
                    "enum": ["Airtel", "BSNL", "Reliance Jio", "Vodafone"],
                    "description": "Telecom operator"
                },
                "gender": {
                    "type": "string",
                    "enum": ["M", "F"],
                    "description": "Subscriber gender"
                },
                "age": {
                    "type": "integer",
                    "description": "Subscriber age in years"
                },
                "state": {
                    "type": "string",
                    "description": "State name (e.g. 'Tamil Nadu', 'Maharashtra')"
                },
                "city": {
                    "type": "string",
                    "description": "City name (e.g. 'Chennai', 'Mumbai')"
                },
                "num_dependents": {
                    "type": "integer",
                    "description": "Number of family dependents (0-5+)"
                },
                "estimated_salary": {
                    "type": "number",
                    "description": "Estimated monthly/annual salary"
                },
                "calls_made": {
                    "type": "integer",
                    "description": "Number of voice calls made"
                },
                "sms_sent": {
                    "type": "integer",
                    "description": "Number of SMS messages sent"
                },
                "data_used": {
                    "type": "number",
                    "description": "Data consumed in Megabytes (MB)"
                },
                "date_of_registration": {
                    "type": "string",
                    "description": "Date of registration in 'YYYY-MM-DD' format (defaults to current date if omitted)"
                }
            },
            "required": ["telecom_partner", "gender", "age", "state", "city", "estimated_salary", "calls_made", "sms_sent", "data_used"]
        }
    }
]


# ==============================================================================
# TOOL EXECUTION FUNCTIONS
# ==============================================================================

def execute_get_churn_analytics(db: Session, partner: Optional[str] = None) -> Dict[str, Any]:
    query = (
        db.query(
            telecom_partner.partner_name,
            customer.churn,
            func.count(customer.customer_id).label("customer_count")
        )
        .join(customer, customer.partner_id == telecom_partner.partner_id)
        .group_by(telecom_partner.partner_name, customer.churn)
    )

    if partner:
        query = query.filter(telecom_partner.partner_name == partner)

    rows = query.all()
    partners_data: Dict[str, Dict[str, int]] = {}

    total_all = 0
    churned_all = 0

    for row in rows:
        p_name = row.partner_name
        is_churn = row.churn
        count = row.customer_count

        if p_name not in partners_data:
            partners_data[p_name] = {"total": 0, "churned": 0}

        partners_data[p_name]["total"] += count
        total_all += count

        if is_churn:
            partners_data[p_name]["churned"] += count
            churned_all += count

    partner_summaries = []
    riskiest = None
    safest = None

    for p_name, data in partners_data.items():
        churn_rate = (data["churned"] / data["total"] * 100) if data["total"] > 0 else 0.0
        summary = {
            "telecom_partner": p_name,
            "total_customers": data["total"],
            "churned_customers": data["churned"],
            "retained_customers": data["total"] - data["churned"],
            "churn_rate_pct": round(churn_rate, 2)
        }
        partner_summaries.append(summary)

        if riskiest is None or churn_rate > riskiest["churn_rate_pct"]:
            riskiest = summary
        if safest is None or churn_rate < safest["churn_rate_pct"]:
            safest = summary

    overall_rate = (churned_all / total_all * 100) if total_all > 0 else 0.0

    return {
        "overall_churn_rate_pct": round(overall_rate, 2),
        "total_subscribers": total_all,
        "total_churned_subscribers": churned_all,
        "total_retained_subscribers": total_all - churned_all,
        "highest_churn_partner": riskiest,
        "lowest_churn_partner": safest,
        "partner_breakdown": partner_summaries
    }


def execute_get_customer_distribution(db: Session) -> Dict[str, Any]:
    rows = (
        db.query(
            telecom_partner.partner_name,
            func.count(customer.customer_id).label("customer_count")
        )
        .join(customer, customer.partner_id == telecom_partner.partner_id)
        .group_by(telecom_partner.partner_name)
        .all()
    )

    total = sum(r.customer_count for r in rows)
    distribution = {}

    for r in rows:
        share = round((r.customer_count / total * 100), 2) if total > 0 else 0.0
        distribution[r.partner_name] = {
            "customer_count": r.customer_count,
            "market_share_pct": share
        }

    return {
        "total_customers": total,
        "partner_distribution": distribution
    }


def execute_get_demographics_distribution(db: Session, dimension: str = "all") -> Dict[str, Any]:
    res: Dict[str, Any] = {}

    if dimension in ["all", "age"]:
        age_result = db.query(
            func.sum(case((customer.age.between(18, 25), 1), else_=0)).label("18-25"),
            func.sum(case((customer.age.between(26, 35), 1), else_=0)).label("26-35"),
            func.sum(case((customer.age.between(36, 45), 1), else_=0)).label("36-45"),
            func.sum(case((customer.age.between(46, 55), 1), else_=0)).label("46-55"),
            func.sum(case((customer.age.between(56, 65), 1), else_=0)).label("56-65"),
            func.sum(case((customer.age >= 66, 1), else_=0)).label("66+")
        ).first()

        res["age_distribution"] = [
            {"bracket": "18–25", "count": int(age_result[0] or 0)},
            {"bracket": "26–35", "count": int(age_result[1] or 0)},
            {"bracket": "36–45", "count": int(age_result[2] or 0)},
            {"bracket": "46–55", "count": int(age_result[3] or 0)},
            {"bracket": "56–65", "count": int(age_result[4] or 0)},
            {"bracket": "66+", "count": int(age_result[5] or 0)}
        ]

    if dimension in ["all", "gender"]:
        gender_rows = (
            db.query(
                telecom_partner.partner_name,
                func.sum(case((customer.gender == "M", 1), else_=0)).label("male_count"),
                func.sum(case((customer.gender == "F", 1), else_=0)).label("female_count")
            )
            .join(telecom_partner, customer.partner_id == telecom_partner.partner_id)
            .group_by(telecom_partner.partner_name)
            .all()
        )

        res["gender_by_partner"] = [
            {
                "partner": row.partner_name,
                "male": int(row.male_count or 0),
                "female": int(row.female_count or 0),
                "total": int((row.male_count or 0) + (row.female_count or 0))
            }
            for row in gender_rows
        ]

    return res


def execute_get_risk_distribution(db: Session) -> Dict[str, Any]:
    rows = (
        db.query(
            customer_risk.risk_category,
            func.count(customer.customer_id).label("count")
        )
        .join(customer, customer.customer_id == customer_risk.customer_id)
        .group_by(customer_risk.risk_category)
        .all()
    )

    total = sum(r.count for r in rows)
    breakdown = []

    for r in rows:
        pct = round((r.count / total * 100), 2) if total > 0 else 0.0
        breakdown.append({
            "risk_category": r.risk_category,
            "count": r.count,
            "share_pct": pct
        })

    return {
        "total_risk_evaluated": total,
        "risk_breakdown": breakdown
    }


def execute_search_customers(
    db: Session,
    partner: Optional[str] = None,
    state: Optional[str] = None,
    city: Optional[str] = None,
    gender: Optional[str] = None,
    churn: Optional[bool] = None,
    risk_category: Optional[str] = None,
    age_min: Optional[int] = None,
    age_max: Optional[int] = None,
    search_id: Optional[int] = None,
    limit: int = 10
) -> Dict[str, Any]:
    limit = max(1, min(limit or 10, 25))

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
            customer_risk.risk_category
        )
        .join(telecom_partner, customer.partner_id == telecom_partner.partner_id)
        .join(location, customer.pincode == location.pincode)
        .join(customer_usage, customer.customer_id == customer_usage.customer_id)
        .outerjoin(customer_risk, customer.customer_id == customer_risk.customer_id)
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
    if risk_category:
        query = query.filter(customer_risk.risk_category == risk_category)
    if age_min is not None:
        query = query.filter(customer.age >= age_min)
    if age_max is not None:
        query = query.filter(customer.age <= age_max)
    if search_id is not None:
        query = query.filter(customer.customer_id == search_id)

    total_count = query.count()
    results = query.order_by(customer.customer_id.asc()).limit(limit).all()

    formatted = [
        {
            "customer_id": r.customer_id,
            "telecom_partner": r.telecom_partner,
            "gender": r.gender,
            "age": r.age,
            "state": r.state,
            "city": r.city,
            "calls_made": r.calls_made,
            "sms_sent": r.sms_sent,
            "data_used_mb": float(r.data_used) if r.data_used is not None else 0.0,
            "estimated_salary": float(r.estimated_salary) if r.estimated_salary is not None else 0.0,
            "num_dependents": r.num_dependents,
            "risk_category": r.risk_category or "Unassessed",
            "churn": r.churn
        }
        for r in results
    ]

    return {
        "matching_count": total_count,
        "returned_count": len(formatted),
        "customers": formatted
    }


def execute_get_customer_profile(db: Session, customer_id: int) -> Dict[str, Any]:
    row = (
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
            customer_risk.risk_score,
            customer_risk.risk_category
        )
        .join(telecom_partner, customer.partner_id == telecom_partner.partner_id)
        .join(location, customer.pincode == location.pincode)
        .join(customer_usage, customer.customer_id == customer_usage.customer_id)
        .outerjoin(customer_risk, customer.customer_id == customer_risk.customer_id)
        .filter(customer.customer_id == customer_id)
        .first()
    )

    if not row:
        return {"error": f"Customer with ID {customer_id} not found."}

    return {
        "customer_id": row.customer_id,
        "telecom_partner": row.telecom_partner,
        "gender": row.gender,
        "age": row.age,
        "state": row.state,
        "city": row.city,
        "pincode": row.pincode,
        "date_of_registration": str(row.date_of_registration),
        "num_dependents": row.num_dependents,
        "estimated_salary": float(row.estimated_salary) if row.estimated_salary is not None else 0.0,
        "calls_made": row.calls_made,
        "sms_sent": row.sms_sent,
        "data_used_mb": float(row.data_used) if row.data_used is not None else 0.0,
        "data_used_gb": round(float(row.data_used or 0) / 1024.0, 2),
        "churn": row.churn,
        "risk_score": row.risk_score,
        "risk_category": row.risk_category or "Unassessed"
    }


def execute_predict_customer_churn(db: Session, customer_id: int) -> Dict[str, Any]:
    # 1. Fetch customer
    row = (
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
            customer_usage.data_used,
            customer.churn
        )
        .join(telecom_partner, telecom_partner.partner_id == customer.partner_id)
        .join(location, location.pincode == customer.pincode)
        .join(customer_usage, customer_usage.customer_id == customer.customer_id)
        .filter(customer.customer_id == customer_id)
        .first()
    )

    if not row:
        return {"error": f"Customer ID {customer_id} not found."}

    # If already churned
    if row.churn:
        return {
            "customer_id": customer_id,
            "status": "Already Churned",
            "already_churned": True,
            "message": f"Customer #{customer_id} has already churned and terminated service with {row.telecom_partner}."
        }

    # 2. Run feature engineering and ML model
    model = get_model()
    features = build_features_for_db(row._mapping)

    pred = int(model.predict(features)[0])
    prob = float(model.predict_proba(features)[0][1])

    return {
        "customer_id": customer_id,
        "telecom_partner": row.telecom_partner,
        "already_churned": False,
        "prediction": pred,
        "prediction_label": "Likely to Churn" if pred == 1 else "Likely to Stay",
        "churn_probability": round(prob, 4),
        "churn_probability_pct": round(prob * 100, 2),
        "usage_summary": {
            "calls_made": row.calls_made,
            "sms_sent": row.sms_sent,
            "data_used_mb": float(row.data_used or 0),
            "data_used_gb": round(float(row.data_used or 0) / 1024.0, 2)
        }
    }


def execute_simulate_custom_prediction(data: Dict[str, Any]) -> Dict[str, Any]:
    # Ensure required fields and defaults
    payload = dict(data)
    if "date_of_registration" not in payload or not payload["date_of_registration"]:
        payload["date_of_registration"] = date.today().isoformat()

    model = get_model()
    features = build_features_for_db(payload)

    pred = int(model.predict(features)[0])
    prob = float(model.predict_proba(features)[0][1])

    return {
        "simulation_parameters": {
            "telecom_partner": payload.get("telecom_partner"),
            "age": payload.get("age"),
            "gender": payload.get("gender"),
            "calls_made": payload.get("calls_made"),
            "sms_sent": payload.get("sms_sent"),
            "data_used_mb": payload.get("data_used"),
            "data_used_gb": round(float(payload.get("data_used") or 0) / 1024.0, 2),
            "estimated_salary": payload.get("estimated_salary")
        },
        "prediction": pred,
        "prediction_label": "Likely to Churn" if pred == 1 else "Likely to Stay",
        "churn_probability": round(prob, 4),
        "churn_probability_pct": round(prob * 100, 2),
        "risk_level": "High" if prob >= 0.65 else ("Moderate" if prob >= 0.40 else "Low")
    }


# ==============================================================================
# DISPATCHER
# ==============================================================================
def execute_tool(tool_name: str, tool_input: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """
    Dispatcher to invoke the appropriate tool by name with arguments.
    """
    try:
        if tool_name == "get_churn_analytics":
            return execute_get_churn_analytics(db, partner=tool_input.get("partner"))
        elif tool_name == "get_customer_distribution":
            return execute_get_customer_distribution(db)
        elif tool_name == "get_demographics_distribution":
            return execute_get_demographics_distribution(db, dimension=tool_input.get("dimension", "all"))
        elif tool_name == "get_risk_distribution":
            return execute_get_risk_distribution(db)
        elif tool_name == "search_customers":
            return execute_search_customers(db, **tool_input)
        elif tool_name == "get_customer_profile":
            return execute_get_customer_profile(db, customer_id=tool_input.get("customer_id"))
        elif tool_name == "predict_customer_churn":
            return execute_predict_customer_churn(db, customer_id=tool_input.get("customer_id"))
        elif tool_name == "simulate_custom_prediction":
            return execute_simulate_custom_prediction(tool_input)
        else:
            return {"error": f"Unknown tool: {tool_name}"}
    except Exception as e:
        return {"error": f"Error executing tool '{tool_name}': {str(e)}"}
