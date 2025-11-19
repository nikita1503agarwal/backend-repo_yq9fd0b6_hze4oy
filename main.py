import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Contact, Company, Deal, Activity, EmailCampaign

app = FastAPI(title="SimpleCRM Pro API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helpers
class ObjectIdStr(str):
    pass

def to_str_id(doc: dict):
    if not doc:
        return doc
    doc["id"] = str(doc.get("_id"))
    doc.pop("_id", None)
    return doc

# Root & health
@app.get("/")
def read_root():
    return {"message": "SimpleCRM Pro backend is running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:20]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:120]}"

    return response

# Basic CRUD patterns using MongoDB

# Create
@app.post("/contacts", response_model=dict)
def create_contact(contact: Contact):
    new_id = create_document("contact", contact)
    return {"id": new_id}

@app.post("/companies", response_model=dict)
def create_company(company: Company):
    new_id = create_document("company", company)
    return {"id": new_id}

@app.post("/deals", response_model=dict)
def create_deal(deal: Deal):
    new_id = create_document("deal", deal)
    return {"id": new_id}

@app.post("/activities", response_model=dict)
def create_activity(activity: Activity):
    new_id = create_document("activity", activity)
    return {"id": new_id}

@app.post("/email/campaigns", response_model=dict)
def create_campaign(campaign: EmailCampaign):
    new_id = create_document("emailcampaign", campaign)
    return {"id": new_id}

# List endpoints with simple filters
@app.get("/contacts", response_model=List[dict])
def list_contacts(tag: Optional[str] = None, company_id: Optional[str] = None, stage: Optional[str] = None):
    q = {}
    if tag:
        q["tags"] = tag
    if company_id:
        q["company_id"] = company_id
    if stage:
        q["funnel_stage"] = stage
    docs = get_documents("contact", q)
    return [to_str_id(d) for d in docs]

@app.get("/companies", response_model=List[dict])
def list_companies():
    docs = get_documents("company")
    return [to_str_id(d) for d in docs]

@app.get("/deals", response_model=List[dict])
def list_deals(stage: Optional[str] = None):
    q = {"stage": stage} if stage else {}
    docs = get_documents("deal", q)
    return [to_str_id(d) for d in docs]

@app.get("/activities", response_model=List[dict])
def list_activities(entity_type: Optional[str] = None, entity_id: Optional[str] = None):
    q = {}
    if entity_type:
        q["entity_type"] = entity_type
    if entity_id:
        q["entity_id"] = entity_id
    docs = get_documents("activity", q, limit=200)
    return [to_str_id(d) for d in docs]

# Simple stats (counts & pipeline value)
@app.get("/stats/summary", response_model=dict)
def stats_summary():
    try:
        total_contacts = db.contact.count_documents({}) if db else 0
        active_deals = db.deal.count_documents({"stage": {"$nin": ["Lost"]}}) if db else 0
        pipeline_value = 0.0
        for d in db.deal.find({"stage": {"$nin": ["Won", "Lost"]}}):
            pipeline_value += float(d.get("value", 0) or 0)
        won_count = db.deal.count_documents({"stage": "Won"}) if db else 0
        created_last_30_days = db.contact.count_documents({}) if db else 0
        return {
            "total_contacts": total_contacts,
            "active_deals": active_deals,
            "pipeline_value": pipeline_value,
            "won_deals": won_count,
            "created_last_30_days": created_last_30_days,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Email sending stub (provider-agnostic)
class SendEmailPayload(BaseModel):
    to: List[str]
    subject: str
    html: str
    provider: Optional[str] = None  # Mailgun, Resend, SendGrid

@app.post("/email/send", response_model=dict)
def send_email(payload: SendEmailPayload):
    # In this environment we won't invoke real providers.
    # We log an activity for each recipient and return a mock result.
    for addr in payload.to:
        create_document(
            "activity",
            {
                "entity_type": "contact",
                "entity_id": addr,
                "type": "email_sent",
                "message": f"Email sent: {payload.subject}",
                "meta": {"provider": payload.provider or "mock"},
            },
        )
    return {"status": "queued", "provider": payload.provider or "mock", "sent": len(payload.to)}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
