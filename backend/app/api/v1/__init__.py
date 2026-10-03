from fastapi import APIRouter

from backend.app.api.v1 import admin, auth, complaints, users

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(complaints.router)
api_router.include_router(admin.categories)
api_router.include_router(admin.sla)
api_router.include_router(admin.notifications)
api_router.include_router(admin.reports)
