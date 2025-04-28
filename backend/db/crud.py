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