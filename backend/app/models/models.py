from sqlalchemy import Column, String, DateTime, JSON, Boolean, Integer, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.models.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    avatar = Column(String, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    settings = Column(JSON, default=dict)

    devices = relationship("Device", back_populates="user")
    conversations = relationship("Conversation", back_populates="user")


class Device(Base):
    __tablename__ = "devices"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    platform = Column(String, nullable=False)
    ip = Column(String, default="")
    tailscale_ip = Column(String, default="")
    capabilities = Column(JSON, default=list)
    status = Column(String, default="offline")
    last_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    battery = Column(Integer, default=100)
    signal = Column(String, default="strong")

    user = relationship("User", back_populates="devices")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    ended_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")


class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    role = Column(String, nullable=False)
    content = Column(String, nullable=False)
    type = Column(String, default="text")
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    meta = Column("metadata", JSON, default=dict)

    conversation = relationship("Conversation", back_populates="messages")


class Command(Base):
    __tablename__ = "commands"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    alias = Column(JSON, default=list)
    category = Column(String, nullable=False)
    handler = Column(String, nullable=False)
    requires_auth = Column(Boolean, default=False)
    enabled = Column(Boolean, default=True)
