
from sqlalchemy import Column, String, Float, Integer, DateTime, Index
from sqlalchemy.orm import Session
from database.database import Base
from datetime import datetime, timezone
import uuid
import time
import random
def generate_uuid7():
    timestamp_ms = int(time.time() * 1000)
    uuid_int = (timestamp_ms << 80) | (random.getrandbits(80) & ((1 << 80) - 1))
    return str(uuid.UUID(int=uuid_int))

class Profile(Base):
    __tablename__ = "profiles"
    id = Column(String(36), primary_key=True, default=generate_uuid7())
    name = Column(String(100), unique=True, index=True, nullable=False)
    gender = Column(String(10), nullable=False)
    gender_probability = Column(Float, nullable=False)
    age = Column(Integer, nullable=False)
    age_group = Column(String(10), nullable=False)
    country_id = Column(String(3), nullable=False)
    country_name = Column(String(100), nullable=False)
    country_probability = Column(Float, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
        # Composite indexes for better query performance
    __table_args__ = (
        Index('idx_gender_age', 'gender', 'age'),
        Index('idx_country_age', 'country_id', 'age'),
        Index('idx_age_group_country', 'age_group', 'country_id'),
        Index('idx_gender_prob', 'gender_probability'),
        Index('idx_country_prob', 'country_probability'),
        Index('idx_created_at', 'created_at'),
    )

def get_profile_count(db: Session) -> int:
    """Get total profile count"""
    return db.query(Profile).count()