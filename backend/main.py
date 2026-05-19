from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.database import engine
from app.models.models import Base
from app.api.routes import router as api_router
from app.api.agent_routes import router as agent_router

# Create all tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI-First CRM – HCP Module",
    description="LangGraph-powered CRM for Healthcare Professionals",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")
app.include_router(agent_router, prefix="/api")

@app.get("/")
def root():
    return {"message": "CRM HCP Module API is running 🚀"}
