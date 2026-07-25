from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import admin, agent, auth, cashier, client, notifications, public
from app.core.config import get_settings

settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="API REST du système de file d'attente PA GEN KANPE",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for route in (
    auth.router,
    public.router,
    client.router,
    agent.router,
    cashier.router,
    admin.router,
    notifications.router,
):
    app.include_router(route, prefix="/api/v1")


@app.get("/health", tags=["Santé"])
def health():
    return {"status": "ok", "service": settings.app_name}
