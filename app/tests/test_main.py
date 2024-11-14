import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models import User, Channel, Message
from app.dependencies import get_db
from app import crud, schemas
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


# Инициализация клиента
client = TestClient(app)
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:123@db:5432/chat"

# Фикстура для подключения к базе данных
@pytest.fixture(scope="module")
def db_session():
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
    
    # Создание таблиц и тестовых данных
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()

    # Создаем тестовые данные, если база пуста
    if not session.query(User).first():
        test_user = User(username="test_user", email="test_user@example.com", hashed_password="test_password")
        test_moderator = User(username="moderator", email="moderator@example.com", hashed_password="moderator_password", is_moderator=True)
        channel = Channel(name="test_channel", members=[test_user, test_moderator])
        session.add_all([test_user, test_moderator, channel])
        session.commit()
    
    yield session  # Возвращаем сессию для тестов
    session.close()


# Тестирование регистрации пользователя
def test_register(db_session):
    user_data = {"username": "new_user", "email": "new_user@example.com", "password": "new_password"}
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 200
    assert response.json()["username"] == "new_user"


# Тестирование получения токена (логин)
def test_login(db_session):
    login_data = {"username": "test_user", "password": "test_password"}
    response = client.post("/auth/token", data=login_data)
    assert response.status_code == 200
    assert "access_token" in response.json()


# Тестирование получения сообщений
def test_get_messages(db_session):
    response = client.get("/messages/1/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) > 0


# Тестирование блокировки пользователя
def test_block_user(db_session):
    # Получаем токен модератора
    login_data = {"username": "moderator", "password": "moderator_password"}
    response = client.post("/auth/token", data=login_data)
    token = response.json()["access_token"]
    
    # Тестируем блокировку пользователя
    response = client.post(
        "/moderator/block_user/1", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "User blocked successfully"


# Тестирование разблокировки пользователя
def test_unblock_user(db_session):
    # Получаем токен модератора
    login_data = {"username": "moderator", "password": "moderator_password"}
    response = client.post("/auth/token", data=login_data)
    token = response.json()["access_token"]

    # Тестируем разблокировку пользователя
    response = client.post(
        "/moderator/unblock_user/1", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "User unblocked successfully"
