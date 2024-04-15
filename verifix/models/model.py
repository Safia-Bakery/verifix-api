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
from users.models.user_model import Base



class Divisions(Base):
    __tablename__="divisions"
    id=Column(BIGINT,primary_key=True,index=True)
    name=Column(String,nullable=True)
    parent_id=Column(BIGINT,nullable=True)
    opened_date=Column(String,nullable=True)
    closed_date=Column(String,nullable=True)
    code = Column(String,nullable=True)
    state = Column(String,default=0)
    limit = Column(Integer,nullable=True)
    created_at = Column(DateTime,server_default=func.now())