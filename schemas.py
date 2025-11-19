"""
Database Schemas for SimpleCRM Pro

Each Pydantic model represents a collection in MongoDB.
Collection name is the lowercase of the class name.
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime

# Users (basic auth placeholder)
class User(BaseModel):
    email: EmailStr
    password_hash: str
    name: Optional[str] = None
    is_active: bool = True

# Companies
class Company(BaseModel):
    company_name: str
    address: Optional[str] = None
    website: Optional[str] = None
    notes: Optional[str] = None

# Contacts
class Contact(BaseModel):
    first_name: str
    last_name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    company_id: Optional[str] = Field(None, description="Reference to company _id as string")
    tags: List[str] = []
    source: Optional[str] = None
    notes: Optional[str] = None
    funnel_stage: Literal[
        "New",
        "Contacted",
        "Qualified",
        "Proposal Sent",
        "Negotiation",
        "Won",
        "Lost",
    ] = "New"

# Deals
class Deal(BaseModel):
    deal_name: str
    value: float
    stage: Literal[
        "New",
        "Contacted",
        "Proposal Sent",
        "Negotiation",
        "Won",
        "Lost",
    ] = "New"
    contact_id: Optional[str] = None
    company_id: Optional[str] = None
    deadline: Optional[str] = None
    notes: Optional[str] = None

# Activities/Timeline items
class Activity(BaseModel):
    entity_type: Literal["contact", "deal", "company"]
    entity_id: str
    type: Literal["deal_update", "email_sent", "status_change", "note"]
    message: str
    meta: dict = {}

# Email Campaigns
class EmailCampaign(BaseModel):
    subject: str
    html: str
    segment: Literal["all_contacts", "by_tag", "by_company", "funnel_stage"]
    tag: Optional[str] = None
    company_id: Optional[str] = None
    funnel_stage: Optional[str] = None
    scheduled_at: Optional[datetime] = None

