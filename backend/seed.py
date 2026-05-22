"""Run once to create tables and seed sample HCP data."""
import sys

sys.path.append(".")

from app.db.database import SessionLocal, engine
from app.models.models import Base, HCP


Base.metadata.create_all(bind=engine)

sample_hcps = [
    {
        "name": "Dr. Priya Sharma",
        "specialty": "Cardiology",
        "hospital": "Apollo Hospitals",
        "email": "priya.sharma@apollo.com",
        "phone": "+91-9876543210",
        "territory": "Hyderabad Central",
    },
    {
        "name": "Dr. Rajesh Mehta",
        "specialty": "Oncology",
        "hospital": "Tata Memorial Centre",
        "email": "r.mehta@tatamemorial.com",
        "phone": "+91-9812345678",
        "territory": "Mumbai North",
    },
    {
        "name": "Dr. Ananya Iyer",
        "specialty": "Neurology",
        "hospital": "NIMHANS",
        "email": "a.iyer@nimhans.ac.in",
        "phone": "+91-9900112233",
        "territory": "Bangalore South",
    },
    {
        "name": "Dr. Vikram Nair",
        "specialty": "Endocrinology",
        "hospital": "Fortis Healthcare",
        "email": "v.nair@fortis.com",
        "phone": "+91-9988776655",
        "territory": "Hyderabad West",
    },
    {
        "name": "Dr. Sunita Patel",
        "specialty": "Pulmonology",
        "hospital": "Max Super Speciality",
        "email": "s.patel@maxhospital.com",
        "phone": "+91-9871234560",
        "territory": "Delhi NCR",
    },
]


db = SessionLocal()
try:
    for hcp_data in sample_hcps:
        existing = db.query(HCP).filter(HCP.email == hcp_data["email"]).first()
        if not existing:
            db.add(HCP(**hcp_data))
    db.commit()
finally:
    db.close()

print("Seeded 5 sample HCPs successfully.")
