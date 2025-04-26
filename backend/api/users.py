from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ..models.pydantic_models import User, UserUpdate, UserInDB
from ..db.crud import get_user, update_user, delete_user, get_users
from ..core.security import get_password_hash
from .auth import get_current_active_user

router = APIRouter(
    prefix="/users",
    tags=["Users"],
    responses={404: {"description": "Not found"}},
)

@router.get("/me", response_model=[User])
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """
    Get information about the currently authenticated user.
    """
    return current_user

@router.put("/me", response_model=User)
async def update_user_me(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
):
    """
    Update the currently authenticated user's information.
    """
    if user_update.password:
        hashed_password = get_password_hash(user_update.password)
        user_update.hashed_password = hashed_password
    
    updated_user = await update_user(current_user.id, user_update)
    return updated_user
    
@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_me(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """
    Update the current user's profile information.
    """
    # If updating the password, hash it first
    if user_update.password:
        hashed_password = get_password_hash(user_update.password)
        user_update.hashed_password = hashed_password

    updated_user = await update_user(current_user.id, user_update)
    return updated_user

@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_me(
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete the currently authenticated user.
    """
    await delete_user(current_user.id)

# Admin routes - these should be protected with additional permission checks
@router.get("/", response_model=List[User])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a list of all users. Admin only.
    """
    # Make sure the current user is an admin
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource."
        )
    
    users = await get_users(skip=skip, limit=limit)
    return users

@router.get("/{user_id}", response_model=User)
async def read_user(
    user_id: str,
    current_user: USer = Depends(get_current_active_user)
):
    """
    Get information about a specific user. Admin only.
    """
    # Make sure the current user is an admin or the user being requested
    if not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource."
        )
    
    user = await get_user(user_id=user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )
    return user

@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """
    Update a specific user's information. Admin only.
    """
    # Make sure the current user is an admin
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource."
        )
    
    # If updating the password, hash it first
    if user_update.password:
        hashed_password = get_password_hash(user_update.password)
        user_update.hashed_password = hashed_password

    updated_user = await update_user(user_id, user_update)
    if updated_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )
    return updated_user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a specific user. Admin only.
    """
    # Make sure the current user is an admin
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource."
        )
    
    deleted = await delete_user(user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )