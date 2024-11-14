from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship, declarative_base, Session, sessionmaker
from .database import Base, engine
from passlib.context import CryptContext

Base = declarative_base()

# Ассоциативная таблица для связи пользователей и каналов (многие ко многим)
user_channels = Table(
    "user_channels",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("channel_id", Integer, ForeignKey("channels.id"), primary_key=True),
)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_moderator = Column(Boolean, default=False)
    is_blocked = Column(Boolean, default=False)
    channels = relationship("Channel", secondary=user_channels, back_populates="members")

class Channel(Base):
    __tablename__ = "channels"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    members = relationship("User", secondary=user_channels, back_populates="channels")
    messages = relationship("Message", back_populates="channel")

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    channel_id = Column(Integer, ForeignKey("channels.id"))
    content = Column(String)
    user = relationship("User")
    channel = relationship("Channel", back_populates="messages")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Создание тестовых данных, если бд пустая.
def create_test_data():
    with Session(engine) as session:
        if not session.query(User).first():
            # Создаем пользователей
            user1 = User(username="user1", email="user1@example.com", hashed_password=pwd_context.hash("password"), is_moderator=False)
            user2 = User(username="moderator", email="moderator@example.com", hashed_password=pwd_context.hash("password"), is_moderator=True)
            user3 = User(username="user2", email="user2@example.com", hashed_password=pwd_context.hash("password"), is_moderator=False)
            
            # Создаем каналы и добавляем пользователей (у модератора доступ ко всем)
            channel1 = Channel(name="Channel 1")
            channel1.members = [user1, user3]
            hannel1 = Channel(name="Channel 2")
            channel1.members = [user3]
            
            # Добавляем сообщения
            message1 = Message(user=user1, channel=channel1, content="Hello from user1")
            message2 = Message(user=user2, channel=channel1, content="Hello from moderator")
            session.add_all([user1, user2, channel1, message1, message2])
            session.commit()

# Инициализация
def init_db():
    Base.metadata.create_all(bind=engine)
    create_test_data()
