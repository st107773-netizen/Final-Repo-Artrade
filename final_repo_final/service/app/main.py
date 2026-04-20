from fastapi import FastAPI
from app.routers.sla import router as sla_router

app = FastAPI(title="SLA Service", version="0.1.0")
app.include_router(sla_router)

@app.get("/health")
def health():
    return {"status": "ok"}
