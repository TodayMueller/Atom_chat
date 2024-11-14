from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.dependencies import get_current_user, get_db, check_user_in_channel
from app.models import Message, User
from typing import List, Dict

router = APIRouter()

@router.get("/{channel_id}/", response_model=List[Dict], tags=["Messages"])
async def get_messages(
    channel_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    channel = check_user_in_channel(db, current_user, channel_id)
    
    messages = db.query(Message).filter(Message.channel_id == channel_id).all()
    return [{"sender_id": message.user_id, "content": message.content} for message in messages]
