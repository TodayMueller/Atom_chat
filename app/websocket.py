from fastapi import WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session
from .dependencies import get_current_user_ws, check_user_in_channel, get_db
from .models import User
from . import crud, schemas
from fastapi.security import OAuth2PasswordBearer
from typing import Optional

# Управления WebSocket-соединениями
class ConnectionManager:
    def __init__(self):
        # Храним активные подключения: {channel_id: {user_id: WebSocket}}
        self.active_connections = {}

    async def connect(self, websocket: WebSocket, user: User, channel_id: int):
        # Принимаем WebSocket соединение
        await websocket.accept()
        if channel_id not in self.active_connections:
            self.active_connections[channel_id] = {}
        self.active_connections[channel_id][user.id] = websocket

    def disconnect(self, user_id: int, channel_id: int):
        # Удаляем соединение из активных
        if channel_id in self.active_connections:
            self.active_connections[channel_id].pop(user_id, None)
            if not self.active_connections[channel_id]:  # Если канал пуст, удаляем его из активных
                del self.active_connections[channel_id]

    async def broadcast(self, channel_id: int, message: str):
        # Отправляем сообщение всем подключенным пользователям канала
        connections = self.active_connections.get(channel_id, {}).values()
        for connection in connections:
            await connection.send_text(message)

manager = ConnectionManager()

async def websocket_endpoint(
    websocket: WebSocket,
    channel_id: int,
    db: Session = Depends(get_db),
    token: Optional[str] = None
):
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")
    
    user = await get_current_user_ws(websocket, db=db, token=token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

    try:
        check_user_in_channel(db, user, channel_id)
    except HTTPException:
        await websocket.close(code=1008)
        return

    await manager.connect(websocket, user, channel_id)

    try:
        while True:
            data = await websocket.receive_text()
            message = crud.create_message(
                db=db,
                message=schemas.MessageCreate(text=data, channel_id=channel_id),
                sender_id=user.id,
                channel_id=channel_id
            )
            await manager.broadcast(channel_id, f"{user.username}: {data}")
    except WebSocketDisconnect:
        manager.disconnect(user.id, channel_id)