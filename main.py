from fastapi import FastAPI
from routes import auth, customer, analytics
app = FastAPI()

app.include_router(auth.router)
app.include_router(customer.router)
app.include_router(analytics.router)
