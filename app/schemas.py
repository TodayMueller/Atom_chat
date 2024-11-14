from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class User(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    is_moderator: bool

class MessageCreate(BaseModel):
    text: str
    channel_id: int

class Message(BaseModel):
    id: int
    text: str
    sender_id: int
    channel_id: int
    timestamp: datetime

class ChannelCreate(BaseModel):
    name: str

class Channel(BaseModel):
    id: int
    name: str
    members: List[int] = []

    class Config:
        orm_mode = True