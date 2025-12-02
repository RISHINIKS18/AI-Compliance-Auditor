from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.routes import router as auth_router
from app.policies.routes import router as policies_router
from app.embeddings.routes import router as embeddings_router
from app.rules.routes import router as rules_router
from app.audits.routes import router as audits_router
from app.remediation.routes import router as remediation_router

app = FastAPI(title="AI Compliance Auditor API", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(policies_router)
app.include_router(embeddings_router)
app.include_router(rules_router)
app.include_router(audits_router)
app.include_router(remediation_router)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/")
async def root():
    return {"message": "AI Compliance Auditor API"}
