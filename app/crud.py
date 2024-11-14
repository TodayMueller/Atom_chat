from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi import HTTPException
from . import models, schemas

def get_user_by_id(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hashed_password = pwd_context.hash(user.password)

    db_user = models.User(username=user.username, email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_message(db: Session, message: schemas.MessageCreate, sender_id: int, channel_id: int):
    channel = db.query(models.Channel).filter(models.Channel.id == channel_id).first()
    if not channel:
        raise ValueError("Channel does not exist")
    
    db_message = models.Message(content=message.text, user_id=sender_id, channel_id=channel_id)
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

def create_channel(db: Session, channel_data: schemas.ChannelCreate) -> models.Channel:
    channel = models.Channel(name=channel_data.name)
    db.add(channel)
    db.commit()
    db.refresh(channel)
    return channel

def delete_channel(db: Session, channel_id: int):
    channel = db.query(models.Channel).filter(models.Channel.id == channel_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    db.delete(channel)
    db.commit()

def add_user_to_channel(db: Session, user_id: int, channel_id: int):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    channel = db.query(models.Channel).filter(models.Channel.id == channel_id).first()
    if not user or not channel:
        raise HTTPException(status_code=404, detail="User or Channel not found")
    if user not in channel.members:
        channel.members.append(user)
        db.commit()

def remove_user_from_channel(db: Session, user_id: int, channel_id: int):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    channel = db.query(models.Channel).filter(models.Channel.id == channel_id).first()
    if not user or not channel:
        raise HTTPException(status_code=404, detail="User or Channel not found")
    if user in channel.members:
        channel.members.remove(user)
        db.commit()