from sqlalchemy import (
    DECIMAL,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import declarative_base, relationship
import os
from datetime import datetime
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
    risk = relationship("customer_risk",back_populates="customer", uselist=False)

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

class customer_risk(Base):
    __tablename__ = "customer_risk"

    customer_id = Column(Integer, ForeignKey("customer.customer_id"),primary_key=True, nullable=False)
    risk_score = Column(Integer, nullable=False)
    risk_category = Column(String(255), nullable=False)

    customer = relationship("customer", back_populates="risk")


class AssistantConversation(Base):
    __tablename__ = "assistant_conversation"

    conversation_id = Column(String(64), primary_key=True)
    username = Column(String(255), ForeignKey("admin.username"), nullable=False)
    title = Column(String(255), nullable=False, default="New Conversation")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    messages = relationship(
        "AssistantMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="AssistantMessage.created_at.asc()"
    )


class AssistantMessage(Base):
    __tablename__ = "assistant_message"

    message_id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(String(64), ForeignKey("assistant_conversation.conversation_id"), nullable=False)
    role = Column(String(20), nullable=False)  # "user", "assistant"
    content = Column(Text, nullable=False)
    tool_calls = Column(Text, nullable=True)  # JSON string of tool calls summary
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("AssistantConversation", back_populates="messages")


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
