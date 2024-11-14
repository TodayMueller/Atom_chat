from .database import SessionLocal
from .models import User, Channel  # Импортируем модели User и Channel
from fastapi.security import OAuth2PasswordBearer
import jwt
from datetime import datetime
from app.config import SECRET_KEY, ALGORITHM  # Импортируем конфигурацию из config.py
from fastapi import WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_db():
    db = SessionLocal()
    try:
        yield db 
    finally:
        db.close()

# Функция для получения текущего пользователя по токену
def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")  
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    return user

# Получаем текущего пользователя через WebSocket
async def get_current_user_ws(websocket: WebSocket, db: Session = Depends(get_db), token: Optional[str] = None):
    if not token:
        await websocket.close(code=1008)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing token"
        )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            await websocket.close(code=1008)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except jwt.PyJWTError:
        await websocket.close(code=1008)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        await websocket.close(code=1008)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return user

# Проверка на модератора
def get_current_moderator(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):

    user = get_current_user(db, token)
    
    if not user.is_moderator:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action"
        )
    
    return user

# Проверка доступа к каналу
def check_user_in_channel(db: Session, user: User, channel_id: int) -> Channel:
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Channel not found"
        )
    
    if not user.is_moderator and channel_id not in [ch.id for ch in user.channels]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this channel"
        )
    
    if user.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this channel"
        )
    
    return channel
