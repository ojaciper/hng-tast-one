from sqlalchemy import Column, String, Float, Integer, DateTime
from database.database import Base
from datetime import datetime, timezone
import uuid
import time
import random

class Profile(Base):
    __tablename__ = "profiles"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid7()))
    name = Column(String(100), unique=True, index=True, nullable=False)
    gender = Column(String(10), nullable=False)
    gender_probability = Column(Float, nullable=False)
    sample_size = Column(Integer, nullable=False)
    age = Column(Integer, nullable=False)
    age_group = Column(String(10), nullable=False)
    country_id = Column(String(3), nullable=False)
    country_probability = Column(Float, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
