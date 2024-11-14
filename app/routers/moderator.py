from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, crud, schemas
from app.dependencies import get_db, get_current_moderator

router = APIRouter()

@router.post("/block_user/{user_id}")
async def block_user(user_id: int, db: Session = Depends(get_db), moderator=Depends(get_current_moderator)):
    # Получаем пользователя по ID
    user = crud.get_user_by_id(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Проверка, что нельзя заблокировать другого модератора
    if user.is_moderator:
        raise HTTPException(status_code=403, detail="Cannot block another moderator")
    
    user.is_blocked = True
    db.commit()
    return {"message": "User blocked successfully"}

@router.post("/unblock_user/{user_id}")
async def unblock_user(user_id: int, db: Session = Depends(get_db), moderator=Depends(get_current_moderator)):
    # Получаем пользователя по ID
    user = crud.get_user_by_id(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Проверка, что пользователь заблокирован
    if not user.is_blocked:
        raise HTTPException(status_code=400, detail="User is not blocked")
    
    user.is_blocked = False
    db.commit()
    return {"message": "User unblocked successfully"}

@router.post("/create_channel", response_model=schemas.Channel)
async def create_channel(channel_data: schemas.ChannelCreate, db: Session = Depends(get_db), moderator=Depends(get_current_moderator)):
    channel = crud.create_channel(db, channel_data)
    return channel

@router.delete("/delete_channel/{channel_id}")
async def delete_channel(channel_id: int, db: Session = Depends(get_db), moderator=Depends(get_current_moderator)):
    crud.delete_channel(db, channel_id)
    return {"message": "Channel deleted successfully"}

@router.post("/add_user_to_channel")
async def add_user_to_channel(user_id: int, channel_id: int, db: Session = Depends(get_db), moderator=Depends(get_current_moderator)):
    crud.add_user_to_channel(db, user_id, channel_id)
    return {"message": "User added to channel successfully"}

@router.delete("/remove_user_from_channel")
async def remove_user_from_channel(user_id: int, channel_id: int, db: Session = Depends(get_db), moderator=Depends(get_current_moderator)):
    crud.remove_user_from_channel(db, user_id, channel_id)
    return {"message": "User removed from channel successfully"}