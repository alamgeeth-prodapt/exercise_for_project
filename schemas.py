from pydantic import BaseModel
# Customer
# ├── CustomerBase
# ├── CustomerCreate
# ├── CustomerUpdate
# └── CustomerResponse

# CustomerUsage
# ├── UsageBase
# ├── UsageCreate
# ├── UsageUpdate
# └── UsageResponse

# Partner
# ├── PartnerResponse

# Location
# ├── LocationResponse
class CustomerBase(BaseModel):
    __tablename__ = "customer"
