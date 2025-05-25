import uuid
from typing import List
from fastapi import Depends
from sqlalchemy.orm import Session

from database.database import get_db
from database.models import Chat


def get_chat_repository(db: Session = Depends(get_db)):
    return ChatRepository(db)


class ChatRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_chat(self, title: str = None, session_id: uuid.UUID = None) -> Chat:
        chat = Chat(id=session_id, title=title)
        self.db.add(chat)
        self.db.commit()
        self.db.refresh(chat)
        return chat

    def update_chat(self, chat_id: uuid.UUID, title: str) -> Chat | None:
        """Update the title of a chat."""
        chat = self.db.query(Chat).filter(Chat.id == chat_id).first()
        if not chat:
            return None
        chat.title = title
        self.db.commit()
        self.db.refresh(chat)
        return chat

    def get_chats_by_user(self, limit: int = 50, offset: int = 0) -> List[Chat]:
        """List chats for a user with pagination."""
        return (
            self.db.query(Chat)
            .order_by(Chat.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def count_chats_by_user(self) -> int:
        """Count the total number of chats for a user."""
        return self.db.query(Chat).count()

    def get_chat_by_id(self, chat_id: uuid.UUID) -> Chat | None:
        """Retrieve a specific chat by ID, ensuring it belongs to the user."""
        return self.db.query(Chat).filter(Chat.id == chat_id).first()

    def delete_chat(self, chat_id: uuid.UUID) -> bool:
        """Delete a chat by ID, ensuring it belongs to the user."""
        chat = self.db.query(Chat).filter(Chat.id == chat_id).first()
        if not chat:
            return False
        self.db.delete(chat)
        self.db.commit()
        return True
