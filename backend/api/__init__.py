from fastapi import APIRouter

from .auth import router as auth_router
from .research import router as research_router
from .projects import router as projects_router
from .users import router as users_router

# Main API router
router = APIRouter()

# Include sub-routers
router.include_router(auth_router)
router.include_router(research_router)
router.include_router(projects_router)
router.include_router(users_router)

