from pydantic import BaseModel
from datetime import date


class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str

# class customerRequest(BaseModel):
#     customer_id: int

class CustomerResponse(BaseModel):
    customer_id: int
    telecom_partner: str
    gender: str
    age: int
    state: str
    city: str
    pincode: str
    date_of_registration: date
    num_dependents: int
    estimated_salary: float
    calls_made: int
    sms_sent: int
    data_used: float
    churn: bool

class CustomerPaginationResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    customers: list[CustomerResponse]

class ChurnRateAnalyticsResponse(BaseModel):
    telecom_partner: str
    churn_rate: float

class CustomerDistributionResponse(BaseModel):
    total_customers: int
    partners: dict[str, int]