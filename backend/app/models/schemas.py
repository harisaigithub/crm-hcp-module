from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.models import InteractionType, SentimentType

# HCP Schemas
class HCPBase(BaseModel):
    name: str
    specialty: Optional[str] = None
    hospital: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    territory: Optional[str] = None

class HCPCreate(HCPBase):
    pass

class HCPOut(HCPBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

# Interaction Schemas
class InteractionBase(BaseModel):
    hcp_id: int
    interaction_type: InteractionType = InteractionType.visit
    notes: Optional[str] = None
    products_discussed: Optional[str] = None
    logged_by: Optional[str] = None
    followup_date: Optional[datetime] = None
    followup_notes: Optional[str] = None

class InteractionCreate(InteractionBase):
    pass

class InteractionUpdate(BaseModel):
    interaction_type: Optional[InteractionType] = None
    notes: Optional[str] = None
    products_discussed: Optional[str] = None
    followup_date: Optional[datetime] = None
    followup_notes: Optional[str] = None
    sentiment: Optional[SentimentType] = None

class InteractionOut(InteractionBase):
    id: int
    summary: Optional[str] = None
    sentiment: Optional[SentimentType] = None
    date: datetime
    created_at: datetime
    updated_at: Optional[datetime] = None
    class Config:
        from_attributes = True

# Chat Schema
class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = "default"
