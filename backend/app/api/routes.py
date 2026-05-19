from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.models.models import HCP, Interaction
from app.models.schemas import HCPCreate, HCPOut, InteractionCreate, InteractionOut, InteractionUpdate

router = APIRouter()

# --- HCP Routes ---
@router.get("/hcps", response_model=List[HCPOut])
def list_hcps(db: Session = Depends(get_db)):
    return db.query(HCP).all()

@router.get("/hcps/{hcp_id}", response_model=HCPOut)
def get_hcp(hcp_id: int, db: Session = Depends(get_db)):
    hcp = db.query(HCP).filter(HCP.id == hcp_id).first()
    if not hcp:
        raise HTTPException(status_code=404, detail="HCP not found")
    return hcp

@router.post("/hcps", response_model=HCPOut)
def create_hcp(hcp: HCPCreate, db: Session = Depends(get_db)):
    db_hcp = HCP(**hcp.model_dump())
    db.add(db_hcp)
    db.commit()
    db.refresh(db_hcp)
    return db_hcp

# --- Interaction Routes ---
@router.get("/interactions", response_model=List[InteractionOut])
def list_interactions(hcp_id: int = None, db: Session = Depends(get_db)):
    query = db.query(Interaction)
    if hcp_id:
        query = query.filter(Interaction.hcp_id == hcp_id)
    return query.order_by(Interaction.date.desc()).all()

@router.get("/interactions/{interaction_id}", response_model=InteractionOut)
def get_interaction(interaction_id: int, db: Session = Depends(get_db)):
    interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return interaction

@router.post("/interactions", response_model=InteractionOut)
def create_interaction(interaction: InteractionCreate, db: Session = Depends(get_db)):
    db_interaction = Interaction(**interaction.model_dump())
    db.add(db_interaction)
    db.commit()
    db.refresh(db_interaction)
    return db_interaction

@router.patch("/interactions/{interaction_id}", response_model=InteractionOut)
def update_interaction(interaction_id: int, update: InteractionUpdate, db: Session = Depends(get_db)):
    db_interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
    if not db_interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    for field, value in update.model_dump(exclude_none=True).items():
        setattr(db_interaction, field, value)
    db.commit()
    db.refresh(db_interaction)
    return db_interaction

@router.delete("/interactions/{interaction_id}")
def delete_interaction(interaction_id: int, db: Session = Depends(get_db)):
    db_interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
    if not db_interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    db.delete(db_interaction)
    db.commit()
    return {"message": "Deleted successfully"}
