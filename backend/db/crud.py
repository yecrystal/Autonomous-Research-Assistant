import logging
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Union

from sqlalchemy import select, update, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .postgresql import get_db, Base
from .mongodb import insert_one, find_one, find_many, update_one, delete_one
from ..models.pydantic_models import (
    User, 
    UserInDB, 
    UserUpdate,
    Project,
    ProjectCreate,
    ProjectUpdate,
    ResearchRequest,
    ResearchStatus,
    ResearchResult
)
from ..models.sql_models import (
    UserModel,
    ProjectModel,
    ResearchProjectLink, 
    ApiKeyModel
)
from ..core.security import get_password_hash

logger = logging.getLogger(__name__)

# User CRUD operations
async def get_user(
    user_id: Optional[str] = None, 
    username: Optional[str] = None, 
    email: Optional[str] = None
) -> Optional[User]:
    """ 
    Get a user by ID, username, or email.

    Args:
        user_id: The user ID
        username: The username
        email: The email address

    Returns:
        Optional[User]: The user if found, None otherwise
    """
    async for db in get_db():
        try:
            query = select(UserModel)

            if user_id:
                query = query.where(UserModel.id == user_id)
            elif username:
                query = query.where(UserModel.username == username)
            elif email:
                query = query.where(UserModel.email == email)
            else:
                return None
            
            result = await db.execute(query)
            user_model = result.scalar_one_none()

            if user_model:
                return User.from_orm(user_model)
            
            return None
        except Exception as e:
            logger.error(f"Error retrieving user: {str(e)}")
            return None
        
async def get_users(skip: int = 0, limit: int = 100) -> List[User]:
    """
    Get a list of users.

    Args:
        skip: Number of users to skip
        limit: Maximum number of users to return

    Return:
        List[User]: List of users
    """
    async for db in get_db():
        try:
            query = select(UserModel).offset(skip).limit(limit)
            result = await db.execute(query)
            user_models = result.scalars().all()

            return [User.from_orm(user) for user in user_models]
        except Exception as e:
            logger.error(f"Error retrieving users: {str(e)}")
            return []

async def create_user(user_data: UserInDB) -> User:
    """
    Create a new user.

    Args: 
        user_data: The user data

    Returns:
        User: The created user
    """
    async for db in get_db():
        try:
            # Create UUID for user
            user_id = str(uuid.uuid4())

            # Create user model
            user_model = UserModel(
                id=user_id,
                username=user_data.username,
                email=user_data.email,
                hashed_password=user_data.hashed_password,
                full_name=user_data.full_name,
                is_active=True,
                is_admin=user_data.is_admin
            )

            db.add(user_model)
            await db.commit()
            await db.refresh(user_model)

            return User.from_orm(user_model)
        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating user: {str(e)}")
            raise

async def update_user(user_id: str, user_update: UserUpdate) -> Optional[User]:
    """
    Update a user.

    Args:
        user_id: The ID of the user to update
        user_update: The update data

    Returns:
        Optional[User]: The updated user if successful, None otherwise
    """
    async for db in get_db():
        try:
            # Prepare update data
            update_data = user_update.dict(exclude_unset=True)

            # Remove password field if present (use hash_password)
            if "password" in update_data:
                del update_data("password")
            
            # Update user
            query = update(UserModel).where(UserModel.id == user_id). values(**update_data)
            await db.execute(query)
            await db.commit()

            # Return updated user
            return await get_user(user_id=user_id)
        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating user: {str(e)}")
            return None

async def delete_user(user_id: str) -> bool:
    """
    Delete a user.

    Args: 
        user_id: The ID of the user to delete

    Returns:
        bool: True if user was deleted, False otherwise
    """
    async for db in get_db():
        try:
            # Delete user
            query = delete(UserModel).where(UserModel.id == user_id)
            result = await db.execute(query)
            await db.commit()

            return result.rowcount > 0
        except Exception as e:
            await db.rollback()
            logger.error(f"Error deleting user: {str(e)}")
            return False
        
# Project CRUD Operations
async def create_project(project_data: ProjectCreate, user_id: str) -> Project:
    """
    Create a new project.

    Args:
        project_data: The project data
        user_id: The ID of the user creating the project

    Returns:
        Project: The created project
    """
    async for db in get_db():
        try:
            # CReate UUID for project
            project_id = str(uuid.uuid4())

            # Create project model
            project_model = ProjectModel(
                id=project_id,
                name=project_data.name,
                description=project_data.description,
                user_id=user_id,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

            db.add(project_model)
            await db.commit()
            await db.refresh(project_model)

        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating project: {str(e)}")
            raise

async def get_project(project_id: str) -> Optional[Project]:
    """
    Get a project by ID.

    Args: 
        project_id: The project ID

    Returns:
        Optional[Project]: The project if found, None otherwise
    """
    async for db in get_db():
        try:
            query = select(ProjectModel).where(ProjectModel.id == project_id)
            result = await db.execute(query)
            project_model = result.scalar_one_or_none()

            if project_model:
                return Project.from_orm(project_model)
        
            return None
        except Exception as e:
            logger.error(f"Error retrieving project: {str(e)}")
            return None
    
async def get_user_projects(user_id: str, skip: int = 0, limit: int = 100) -> List[Project]:
    """
    Get projects for a user.

    Args:
        user_id: The user ID
        skip: Number of projects to skip
        limit: Maximum number of projects to return

    Returns:
        List[Project]: List of projects
    """
    async for db in get_db():
        try:
            query = (
                select(ProjectModel)
                .where(ProjectModel.user_id == user_id)
                .order_by(ProjectModel.updated_at.desc())
                .offset(skip)
                .limit(limit)
            )
            result = await db.execute(query)
            project_models = result.scalars().all()

            return [Project.from_orm(project) for project in project_models]
        except Exception as e:
            logger.error(f"Error retrieving user projects: {str(e)}")
            return []
        
async def update_project(project_id: str, project_update: ProjectUpdate) -> Optional[Project]:
    """
    Update a project.

    Args:
        project_id: The ID of the project to update
        project_update: The update data

    Returns: 
        Optional[Project]: The updated project if successful, None otherwise
    """
    async for db in get_db():
        try:
            # Prepare update data
            update_data = project_update.dict(exclude_unset=True)
            update_data["updated_at"] = datetime.now()

            # Update project
            query = update(ProjectModel).where(ProjectModel.id == project_id).values(**update_data)
            await db.execute(query)
            await db.commit()

            # Return updated project
            return await get_project(project_id=project_id)
        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating project: {str(e)}")
            return None

async def delete_project(project_id: str) -> bool:
    """
    Delete a project.
    
    Args:
        project_id: The ID of the project to delete
        
    Returns:
        bool: True if project was deleted, False otherwise
    """
    async for db in get_db():
        try:
            # Delete project
            query = delete(ProjectModel).where(ProjectModel.id == project_id)
            result = await db.execute(query)
            await db.commit()
            
            return result.rowcount > 0
        except Exception as e:
            await db.rollback()
            logger.error(f"Error deleting project: {str(e)}")
            return False
        
# Research CRUD operations
async def create_research_request(research_data: ResearchRequest):
    """
    Create a new research request in MongoDB.

    Args:
        research_data: The research request data
        project_id: Optional project ID to link the research to

    Retruns:
        str: the ID of the created research request
    """
    try:
        # Prepare research data
        research_dict = research_data.dict()
        research_dict["id"] = str(uuid.uuid4())
        research_dict["status"] = ResearchStatus.PENDING
        research_dict["created_at"] = datetime.now()
        research_dict["updated_at"] = datetime.now()
        
        # Insert into MongoDB
        from ..db.mongodb import insert_one
        result = await insert_one("research_requests", research_dict)
        research_id = str(result.inserted_id)
        
        # If project_id is provided, create a link in SQL
        if project_id:
            async for db in get_db():
                link = ResearchProjectLink(
                    research_id=research_id,
                    project_id=project_id,
                    created_at=datetime.now()
                )
                db.add(link)
                await db.commit()
        
        return research_id
    except Exception as e:
        logger.error(f"Error creating research request: {str(e)}")
        raise

async def get_research_request(research_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a research request by ID.
    
    Args:
        research_id: The research request ID
        
    Returns:
        Optional[Dict[str, Any]]: The research request if found, None otherwise
    """
    try:
        from ..db.mongodb import find_one
        result = await find_one("research_requests", {"id": research_id})
        return result
    except Exception as e:
        logger.error(f"Error retrieving research request: {str(e)}")
        return None

async def update_research_status(research_id: str, status: ResearchStatus) -> bool:
    """
    Update the status of a research request.
    
    Args:
        research_id: The ID of the research request
        status: The new status
        
    Returns:
        bool: True if update was successful, False otherwise
    """
    try:
        from ..db.mongodb import update_one
        result = await update_one(
            "research_requests",
            {"id": research_id},
            {"$set": {"status": status, "updated_at": datetime.now()}}
        )
        return result.modified_count > 0
    except Exception as e:
        logger.error(f"Error updating research status: {str(e)}")
        return False

async def store_research_result(research_id: str, result_data: ResearchResult) -> bool:
    """
    Store the result of a research request.
    
    Args:
        research_id: The ID of the research request
        result_data: The research result data
        
    Returns:
        bool: True if storing was successful, False otherwise
    """
    try:
        from ..db.mongodb import update_one
        result_dict = result_data.dict()
        result_dict["created_at"] = datetime.now()
        
        # Update research request with results and change status to COMPLETED
        result = await update_one(
            "research_requests",
            {"id": research_id},
            {
                "$set": {
                    "result": result_dict,
                    "status": ResearchStatus.COMPLETED,
                    "updated_at": datetime.now()
                }
            }
        )
        return result.modified_count > 0
    except Exception as e:
        logger.error(f"Error storing research result: {str(e)}")
        return False

async def index_research_content(research_id: str, content: str, metadata: Dict[str, Any]) -> bool:
    """
    Index research content in the vector store for semantic search.
    
    Args:
        research_id: The ID of the research request
        content: The text content to index
        metadata: Additional metadata to store with the vector
        
    Returns:
        bool: True if indexing was successful, False otherwise
    """
    try:
        from ..db.vector_store import add_texts
        
        # Ensure research_id is in metadata
        metadata["research_id"] = research_id
        
        # Add document to vector store
        result = await add_texts([content], [metadata])
        
        return bool(result)
    except Exception as e:
        logger.error(f"Error indexing research content: {str(e)}")
        return False

async def search_research_content(query: str, filter_metadata: Optional[Dict[str, Any]] = None, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Search for research content using semantic search.
    
    Args:
        query: The search query
        filter_metadata: Optional metadata to filter results
        limit: Maximum number of results to return
        
    Returns:
        List[Dict[str, Any]]: List of search results
    """
    try:
        from ..db.vector_store import search_texts
        
        # Perform semantic search
        results = await search_texts(query, filter_metadata, limit)
        
        return results
    except Exception as e:
        logger.error(f"Error searching research content: {str(e)}")
        return []

async def get_project_research(project_id: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Get all research requests for a project.
    
    Args:
        project_id: The project ID
        skip: Number of research requests to skip
        limit: Maximum number of research requests to return
        
    Returns:
        List[Dict[str, Any]]: List of research requests
    """
    try:
        # First get the research IDs linked to the project
        research_ids = []
        async for db in get_db():
            query = select(ResearchProjectLink.research_id).where(
                ResearchProjectLink.project_id == project_id
            )
            result = await db.execute(query)
            research_ids = [row[0] for row in result]
        
        if not research_ids:
            return []
        
        # Then get the research requests from MongoDB
        from ..db.mongodb import find_many
        research_requests = await find_many(
            "research_requests",
            {"id": {"$in": research_ids}},
            skip=skip,
            limit=limit,
            sort=[("created_at", -1)]  # Sort by created_at descending
        )
        
        return list(research_requests)
    except Exception as e:
        logger.error(f"Error retrieving project research: {str(e)}")
        return []

# API Key CRUD operations
async def create_api_key(user_id: str, name: str) -> Optional[str]:
    """
    Create a new API key for a user.
    
    Args:
        user_id: The user ID
        name: A name for the API key
        
    Returns:
        Optional[str]: The created API key if successful, None otherwise
    """
    async for db in get_db():
        try:
            # Generate API key
            api_key = f"sk_{str(uuid.uuid4()).replace('-', '')}"
            
            # Create API key model
            api_key_model = ApiKeyModel(
                key=api_key,
                name=name,
                user_id=user_id,
                created_at=datetime.now()
            )
            
            db.add(api_key_model)
            await db.commit()
            
            return api_key
        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating API key: {str(e)}")
            return None

async def get_user_api_keys(user_id: str) -> List[Dict[str, Any]]:
    """
    Get all API keys for a user.
    
    Args:
        user_id: The user ID
        
    Returns:
        List[Dict[str, Any]]: List of API keys
    """
    async for db in get_db():
        try:
            query = select(ApiKeyModel).where(ApiKeyModel.user_id == user_id)
            result = await db.execute(query)
            api_keys = result.scalars().all()
            
            return [
                {
                    "key": key.key,
                    "name": key.name,
                    "created_at": key.created_at
                }
                for key in api_keys
            ]
        except Exception as e:
            logger.error(f"Error retrieving user API keys: {str(e)}")
            return []

async def verify_api_key(api_key: str) -> Optional[str]:
    """
    Verify an API key and return the associated user ID.
    
    Args:
        api_key: The API key to verify
        
    Returns:
        Optional[str]: The user ID if the API key is valid, None otherwise
    """
    async for db in get_db():
        try:
            query = select(ApiKeyModel).where(ApiKeyModel.key == api_key)
            result = await db.execute(query)
            api_key_model = result.scalar_one_or_none()
            
            if api_key_model:
                return api_key_model.user_id
            
            return None
        except Exception as e:
            logger.error(f"Error verifying API key: {str(e)}")
            return None

async def delete_api_key(api_key: str) -> bool:
    """
    Delete an API key.
    
    Args:
        api_key: The API key to delete
        
    Returns:
        bool: True if API key was deleted, False otherwise
    """
    async for db in get_db():
        try:
            query = delete(ApiKeyModel).where(ApiKeyModel.key == api_key)
            result = await db.execute(query)
            await db.commit()
            
            return result.rowcount > 0
        except Exception as e:
            await db.rollback()
            logger.error(f"Error deleting API key: {str(e)}")
            return False