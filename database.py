from sqlalchemy import (
    DECIMAL,
    Boolean,
    Column,
    Date,
    ForeignKey,
    Integer,
    String,
    create_engine,
)
from sqlalchemy.orm import declarative_base, relationship
import os
from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker,Session

load_dotenv()
Base = declarative_base()


class telecom_partner(Base):
    __tablename__ = "telecom_partner"

    partner_id = Column(Integer, primary_key=True)
    partner_name = Column(String(50), nullable=False, unique=True)

    customers = relationship("customer", back_populates="partner")


class location(Base):
    __tablename__ = "location"
    pincode = Column(String(10), primary_key=True)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)

    customers = relationship("customer", back_populates="location")


class customer(Base):
    __tablename__ = "customer"

    customer_id = Column(Integer, primary_key=True)
    partner_id = Column(
        Integer, ForeignKey("telecom_partner.partner_id"), nullable=False
    )
    pincode = Column(String(10), ForeignKey("location.pincode"), nullable=False)

    gender = Column(String(10))
    age = Column(Integer)
    date_of_registration = Column(Date)
    num_dependents = Column(Integer)
    estimated_salary = Column(DECIMAL(12, 2))
    churn = Column(Boolean)

    partner = relationship("telecom_partner", back_populates="customers")
    location = relationship("location", back_populates="customers")
    usage = relationship("customer_usage", back_populates="customer", uselist=False)


class customer_usage(Base):
    __tablename__ = "customer_usage"

    customer_id = Column(
        Integer, ForeignKey("customer.customer_id"), primary_key=True, nullable=False
    )
    calls_made = Column(Integer)
    sms_sent = Column(Integer)
    data_used = Column(DECIMAL(10, 2))

    customer = relationship("customer", back_populates="usage")

class admin(Base):
    __tablename__ = "admin"

    username = Column(String(255), primary_key=True)
    password = Column(String(255), nullable=False)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set.")

engine = create_engine(DATABASE_URL)

Base.metadata.create_all(bind=engine)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
