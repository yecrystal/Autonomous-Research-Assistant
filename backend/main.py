from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from backend.api import research, projects, users
from backend.db.postgres import init_db
from backend.config import POSTGRES_URL

app = FastAPI(title="Research Assistant API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(research.router, prefix="/api/research", tags=["Research"])
app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])

@app.on_event("startup")
async def startup_event():
    """
    Startup event to initialize the database connection.
    """
    init_db(POSTGRES_URL)

@app.get("/")
async def root():
    """
    Root endpoint to check if the API is running.
    """
    return {"message": "Research Assistant API is running."}

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)