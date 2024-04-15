from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Float,
    DateTime,
    Boolean,
    BIGINT,
    Table,
    Time,
    JSON,
    VARCHAR,
    Date,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from datetime import datetime
import pytz
import uuid
from database import Base

timezonetash = pytz.timezone("Asia/Tashkent")




# this is models of userss
class Users(Base):  
    __tablename__ = "users"
    id = Column(BIGINT, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    name = Column(String,nullable=True)
    phone_number = Column(String,nullable=True)
    status = Column(Integer,default=0)
    created_at = Column(DateTime(timezone=True), default=func.now())

