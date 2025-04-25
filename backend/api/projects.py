from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ..models.pydantic_models import Project, ProjectCreate, ProjectUpdate, ResearchResult, User
from ..db.crud import create_project, get_project, update_project, delete_project, get_user_projects, add_research_to_project, remove_research_from_project, get_project_researches
from .auth import get_current_active_user

router = APIRouter(
    prefix="/projects",
    tags=["Projects"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=Project)
async def create_new_project(
    project: ProjectCreate,
    current_user: User = Depends(get_current_active_user),
):
    """
    Create a new project.
    """
    return await create_project(project, current_user.id)

@router.get("/", response_model=List[Project])
async def list_projects(
    skip: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_active_user)
):
    """
    List all projects owned by the current user.
    """
    return await get_user_projects(current_user.id, skip=skip, limit=limit)

@router.get("/{project_id}", response_model=Project)
async def get_project_by_id(
    project_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a project by its ID.
    """
    project = await get_project(project_id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found."
        )
    
    # CHeck project ownership
    if project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this project."
        )
    
    return project

@router.put("/{project_id}", response_model=Project)
async def update_project_by_id(
    project_id: str,
    project_update: ProjectUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """
    Update a project's details.
    """
    existing_project = await get_project(project_id)
   
    if not existing_project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found."
        )
    
    # Check project ownership
    if existing_project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to update this project."
        )
    
    updated_project = await update_project(project_id, project_update)
    return updated_project

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project_by_id(
    project_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a project.
    """
    existing_project = await get_project(project_id)

    if not existing_project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found."
        )
    
    # Check project ownership
    if existing_project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this project."
        )
    
    await delete_project(project_id)

@router.get("/{project_id}/researches", response_model=List[ResearchResult])
async def get_project_research_tasks(
    project_id: str,
    skip: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all research tasks associated with a project.
    """
    existing_project = await get_project(project_id)

    if not existing_project:
        raise HTTPException(
            status_Code=status.HTTP_404_NOT_FOUND,
            detail="Project not found."
    )

    # Check project ownership
    if existing_project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this project."
        )
    
    researches = await get_project_researches(project_id, skip=skip, limit=limit)
    return researches

@router.post("/{project_id}/researches/{research_id}", status_code=status.HTTP_200_OK)
async def add_research_to_project(
    project_id:str,
    research_id:str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Add a research task to a project.
    """
    # Verify that the project exists and belongs to the user
    project = await get_project(project_id)
    if not project or project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or you do not have permission to access it."
        )

    success = await add_research_to_project(project_id, research_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Research already in project or could not be added."
        )

    return {"Status": "Research added to project successfully."}

@router.delete("/{project_id}/researches/{research_id}", status_code=status.HTTP_200_OK)
async def remove_research_from_project(
    project_id:str,
    research_id:str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Remove a research task from a project.
    """
    # Verify project exists and belongs to user
    project = await get_project(project_id)
    if not project or project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or not authorized"
        )
    
    success = await remove_research_from_project(project_id, research_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Research not in project or could not be removed"
        )
    
    return {"status": "Research removed from project successfully"}