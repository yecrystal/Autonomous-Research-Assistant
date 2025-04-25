from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, status
from pydantic import BaseModel

from ..models.pydantic_models import ResearchRequest, ResearchResponse, ResearchStatus, ResearchResult, User
from ..core.workflow import start_research_workflow, get_research_status
from ..db.crud import save_research_request, get_research_by_id, get_user_researches
from .auth import get_current_active_user

router = APIRouter(
    prefix="/research",
    tags=["Research"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=ResearchResponse)
async def create_research(
    request: ResearchRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
):
    """
    Start a new research workflow.
    """
    # Save the research request to the database
    research_id = await save_research_request(request, current_user.id)

    # Start the research workflow in the background
    background_tasks.add_task(
        start_research_workflow, 
        research_id=research_id,
        query=request.query,
        depth=request.depth,
        sources_required=request.sources_required,
        user_id=current_user.id
    )

    return ResearchResponse(
        id=research_id,
        status=ResearchStatus.STARTED,
        message="Research workflow started successfully."
    )

@router.get("/{research_id}", response_model=ResearchResult)
async def get_research(
    research_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """
    Get the status and results of a specific research workflow.
    """
    # Check if the research ID is valid
    research = await get_research_by_id(research_id)
    
    if not research:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research not found."
        )
    
    # Check if the research belongs to the current user
    if research.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this research."
        )
    
    # Get the current status of the research workflow
    current_status = await get_research_status(research_id)

    return ResearchResult(
        id=research_id,
        query=research.query,
        status=current_status.status,
        progress=current_status.progress,
        summary=current_status.summary,
        sources=current_status.sources,
        report=current_status.report,
        created_at=research.created_at,
        updated_at=research.updated_at
    )

@router.get("/", response_model=List[ResearchResult])
async def list_researches(
    skip: int = 0,
    limit: int = 10,
    status: Optional[ResearchStatus] = None,
    current_user: User = Depends(get_current_active_user)
):
    """
    List all research tasks for the current user.
    """
    researches = await get_user_researches(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        status=status
    )
    return researches

@router.delete("/{research_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_research(
    research_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a specific research task.
    """
    research = await get_research_by_id(research_id)

    if not research:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research not found."
        )
    
    if research.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this research."
        )
    
    # Delete the research and all associated data
    success = await delete_research_by_id(research_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete research."
        )

@router.post("/{research_id}/status", response_model=ResearchStatus)
async def stop_research(
    research_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Stop an ongoing research task.
    """
    research = await get_research_by_id(research_id)

    if not research:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research task not found."
        )
    
    if research.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to stop this research task."
        )
    
    # Stop the research workflow
    success = await stop_research_workflow(research_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to stop research task."
        )
    
    return ResearchStatus(
        id=research_id,
        status=ResearchStatus.STOPPED,
        message="Research task has been stopped."
    )