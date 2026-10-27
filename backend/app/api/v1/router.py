from fastapi import APIRouter

from app.api.v1 import announcements, auth, notifications, packages, shipments, stations, stats, users

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(stations.router)
api_router.include_router(packages.router)
api_router.include_router(shipments.router)
api_router.include_router(notifications.router)
api_router.include_router(announcements.router)
api_router.include_router(stats.router)
