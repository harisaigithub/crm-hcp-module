from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum

class InteractionType(str, enum.Enum):
    visit = "visit"
    call = "call"
    email = "email"
    conference = "conference"
    other = "other"

class SentimentType(str, enum.Enum):
    positive = "positive"
    neutral = "neutral"
    negative = "negative"

class HCP(Base):
    __tablename__ = "hcps"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    specialty = Column(String(100))
    hospital = Column(String(200))
    email = Column(String(150), unique=True)
    phone = Column(String(20))
    territory = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    interactions = relationship("Interaction", back_populates="hcp")

class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True)
    hcp_id = Column(Integer, ForeignKey("hcps.id"), nullable=False)
    interaction_type = Column(Enum(InteractionType), default=InteractionType.visit)
    date = Column(DateTime(timezone=True), server_default=func.now())
    notes = Column(Text)
    summary = Column(Text)
    products_discussed = Column(String(500))
    sentiment = Column(Enum(SentimentType), default=SentimentType.neutral)
    followup_date = Column(DateTime(timezone=True), nullable=True)
    followup_notes = Column(Text, nullable=True)
    logged_by = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    hcp = relationship("HCP", back_populates="interactions")
