from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.agent_routes import router as agent_router
from app.api.routes import router as api_router
from app.db.database import engine
from app.models.models import Base


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="HCP CRM Module",
    description="LangGraph-powered CRM for Healthcare Professionals",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")
app.include_router(agent_router, prefix="/api")


@app.get("/")
def root():
    return {"message": "CRM HCP Module API is running"}
