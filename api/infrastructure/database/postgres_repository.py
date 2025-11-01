import os
import psycopg2
from sqlalchemy import create_engine, Column, String, Integer, Text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from typing import List

from ...domain.models import ChatHistory
from ...domain.ports import IChatRepository

# SQLAlchemy setup
DATABASE_URL = os.environ.get("supabase_POSTGRES_URL")
if not DATABASE_URL:
    raise ValueError("supabase_POSTGRES_URL must be set in environment variables")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define the table model
class ChatHistoryORM(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    human_message = Column(Text)
    ai_message = Column(Text)

# Create the table in the database if it doesn't exist
Base.metadata.create_all(bind=engine)

class PostgresChatRepository(IChatRepository):
    def __init__(self):
        self.db_session = SessionLocal()

    def add(self, chat_history: ChatHistory) -> None:
        try:
            db_chat = ChatHistoryORM(**chat_history.model_dump())
            self.db_session.add(db_chat)
            self.db_session.commit()
        except Exception as e:
            self.db_session.rollback()
            raise e
        finally:
            self.db_session.close()

    def get_by_session_id(self, session_id: str) -> List[ChatHistory]:
        try:
            db_chats = self.db_session.query(ChatHistoryORM).filter(ChatHistoryORM.session_id == session_id).all()
            return [ChatHistory.model_validate(chat) for chat in db_chats]
        finally:
            self.db_session.close()
