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
async def create_research(user_id: str, project_id: str, research_data: Dict[str, Any]) -> str:
    """
    Create a new research entry in MongoDB.
    
    Args:
        user_id: The ID of the user creating the research
        project_id: The ID of the project this research belongs to
        research_data: The research data
        
    Returns:
        str: The ID of the created research
    """
    from ..db.mongodb import insert_one
    
    try:
        # Generate research ID
        research_id = str(uuid.uuid4())
        
        # Prepare research document
        research = {
            "id": research_id,
            "user_id": user_id,
            "project_id": project_id,
            "title": research_data.get("title", ""),
            "description": research_data.get("description", ""),
            "query": research_data.get("query", ""),
            "status": "pending",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "results": []
        }
        
        # Insert research into MongoDB
        await insert_one("researches", research)
        
        return research_id
    except Exception as e:
        logger.error(f"Error creating research: {str(e)}")
        raise

async def get_research(research_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a research by ID from MongoDB.
    
    Args:
        research_id: The research ID
        
    Returns:
        Optional[Dict[str, Any]]: The research if found, None otherwise
    """
    from ..db.mongodb import find_one
    
    try:
        research = await find_one("researches", {"id": research_id})
        return research
    except Exception as e:
        logger.error(f"Error getting research: {str(e)}")
        return None

async def update_research(research_id: str, update_data: Dict[str, Any]) -> bool:
    """
    Update a research in MongoDB.
    
    Args:
        research_id: The research ID
        update_data: The data to update
        
    Returns:
        bool: True if the update was successful, False otherwise
    """
    from ..db.mongodb import update_one
    
    try:
        # Add updated_at timestamp
        update_data["updated_at"] = datetime.now()
        
        # Update research
        result = await update_one("researches", {"id": research_id}, update_data)
        return result
    except Exception as e:
        logger.error(f"Error updating research: {str(e)}")
        return False

async def get_project_researches(project_id: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Get all researches for a project from MongoDB.
    
    Args:
        project_id: The project ID
        skip: Number of researches to skip
        limit: Maximum number of researches to return
        
    Returns:
        List[Dict[str, Any]]: List of researches
    """
    from ..db.mongodb import find_many
    
    try:
        researches = await find_many(
            "researches",
            {"project_id": project_id},
            skip=skip,
            limit=limit,
            sort=[("created_at", -1)]
        )
        return researches
    except Exception as e:
        logger.error(f"Error getting project researches: {str(e)}")
        return []

async def get_user_researches(user_id: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Get all researches for a user from MongoDB.
    
    Args:
        user_id: The user ID
        skip: Number of researches to skip
        limit: Maximum number of researches to return
        
    Returns:
        List[Dict[str, Any]]: List of researches
    """
    from ..db.mongodb import find_many
    
    try:
        researches = await find_many(
            "researches",
            {"user_id": user_id},
            skip=skip,
            limit=limit,
            sort=[("created_at", -1)]
        )
        return researches
    except Exception as e:
        logger.error(f"Error getting user researches: {str(e)}")
        return []

# Document CRUD operations
async def create_document(research_id: str, document_data: Dict[str, Any]) -> str:
    """
    Create a new document in MongoDB and index it in the vector store.
    
    Args:
        research_id: The ID of the research this document belongs to
        document_data: The document data
        
    Returns:
        str: The ID of the created document
    """
    from ..db.mongodb import insert_one
    from ..db.vector_store import add_documents
    from langchain_core.documents import Document as LangchainDocument
    
    try:
        # Generate document ID
        document_id = str(uuid.uuid4())
        
        # Prepare document
        document = {
            "id": document_id,
            "research_id": research_id,
            "title": document_data.get("title", ""),
            "content": document_data.get("content", ""),
            "url": document_data.get("url", None),
            "metadata": document_data.get("metadata", {}),
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        # Insert document into MongoDB
        await insert_one("documents", document)
        
        # Index document in vector store if it has content
        if document.get("content"):
            # Create Langchain Document for vector store
            langchain_doc = LangchainDocument(
                page_content=document["content"],
                metadata={
                    "id": document_id,
                    "research_id": research_id,
                    "title": document["title"],
                    "url": document["url"],
                    **document["metadata"]
                }
            )
            
            # Add to vector store
            await add_documents([langchain_doc], namespace=f"research_{research_id}")
        
        return document_id
    except Exception as e:
        logger.error(f"Error creating document: {str(e)}")
        raise

async def get_document(document_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a document by ID from MongoDB.
    
    Args:
        document_id: The document ID
        
    Returns:
        Optional[Dict[str, Any]]: The document if found, None otherwise
    """
    from ..db.mongodb import find_one
    
    try:
        document = await find_one("documents", {"id": document_id})
        return document
    except Exception as e:
        logger.error(f"Error getting document: {str(e)}")
        return None

async def get_research_documents(research_id: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Get all documents for a research from MongoDB.
    
    Args:
        research_id: The research ID
        skip: Number of documents to skip
        limit: Maximum number of documents to return
        
    Returns:
        List[Dict[str, Any]]: List of documents
    """
    
    try:
        documents = await find_many(
            "documents",
            {"research_id": research_id},
            skip=skip,
            limit=limit,
            sort=[("created_at", -1)]
        )
        return documents
    except Exception as e:
        logger.error(f"Error getting research documents: {str(e)}")
        return []

async def delete_document(document_id: str) -> bool:
    """
    Delete a document from MongoDB and the vector store.
    
    Args:
        document_id: The document ID
        
    Returns:
        bool: True if the document was deleted, False otherwise
    """
    from ..db.mongodb import delete_one, find_one
    from ..db.vector_store import delete_documents
    
    try:
        # First get the document to retrieve research_id
        document = await find_one("documents", {"id": document_id})
        if not document:
            return False
            
        # Delete from MongoDB
        mongo_result = await delete_one("documents", {"id": document_id})
        
        # Delete from vector store
        vector_result = await delete_documents(ids=[document_id])
        
        return mongo_result and vector_result
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        return False

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

# Search operations using vector store
async def search_documents(query: str, research_id: Optional[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Search for documents using the vector store.
    
    Args:
        query: The search query
        research_id: Optional research ID to limit the search
        limit: Maximum number of results to return
        
    Returns:
        List[Dict[str, Any]]: List of search results
    """
    from ..db.vector_store import similarity_search
    from ..db.mongodb import find_one
    
    try:
        # Define namespace if research_id is provided
        namespace = f"research_{research_id}" if research_id else None
        
        # Perform similarity search
        similar_docs = await similarity_search(
            query=query,
            k=limit,
            namespace=namespace
        )
        
        # Get full documents from MongoDB for each result
        results = []
        for doc in similar_docs:
            doc_id = doc.metadata.get("id")
            if doc_id:
                full_doc = await find_one("documents", {"id": doc_id})
                if full_doc:
                    # Add similarity information
                    full_doc["excerpt"] = doc.page_content
                    full_doc["similarity_score"] = doc.metadata.get("score", 0)
                    results.append(full_doc)
        
        return results
    except Exception as e:
        logger.error(f"Error searching documents: {str(e)}")
        return []