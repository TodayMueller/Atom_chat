from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect, HTTPException, status
from app.routers import auth, messages, moderator
from app.dependencies import get_current_user, get_db
from sqlalchemy.orm import Session
from app.models import init_db
from app.websocket import websocket_endpoint  

app = FastAPI()

init_db()

# Роутинг для авторизации, сообщений и модерации
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(messages.router, prefix="/messages", tags=["Messages"])
app.include_router(moderator.router, prefix="/moderator", tags=["Moderator"])

app.add_api_websocket_route("/ws/{channel_id}", websocket_endpoint)