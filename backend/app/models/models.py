from sqlalchemy import Column, String, DateTime, JSON, Boolean, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.models.database import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    avatar = Column(String, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    settings = Column(JSON, default=dict)

    devices = relationship("Device", back_populates="user")
    conversations = relationship("Conversation", back_populates="user")


class Device(Base):
    __tablename__ = "devices"
    __table_args__ = {"extend_existing": True}

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
    last_heartbeat = Column(DateTime, nullable=True)
    battery = Column(Integer, default=100)
    signal = Column(String, default="strong")
    os_version = Column(String, default="")
    app_version = Column(String, default="")
    extra_data = Column("metadata", JSON, default=dict)

    user = relationship("User", back_populates="devices")


class Conversation(Base):
    __tablename__ = "conversations"
    __table_args__ = {"extend_existing": True}

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    ended_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = {"extend_existing": True}

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
    __table_args__ = {"extend_existing": True}

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    alias = Column(JSON, default=list)
    category = Column(String, nullable=False)
    handler = Column(String, nullable=False)
    requires_auth = Column(Boolean, default=False)
    enabled = Column(Boolean, default=True)


class WearableDeviceDB(Base):
    __tablename__ = "wearable_devices"
    __table_args__ = {"extend_existing": True}

    id = Column(String, primary_key=True)
    user_id = Column(String, default="default")
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    platform = Column(String, nullable=False)
    is_online = Column(Boolean, default=False)
    battery = Column(Integer, default=100)
    firmware_version = Column(String, default="")
    last_sync = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    health_metrics = relationship("HealthMetricDB", back_populates="device", cascade="all, delete-orphan")


class HealthMetricDB(Base):
    __tablename__ = "health_metrics"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String, ForeignKey("wearable_devices.id"), nullable=False)
    metric = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String, default="")
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    device = relationship("WearableDeviceDB", back_populates="health_metrics")
