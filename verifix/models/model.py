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
    status = Column(Integer,default=1)
    division_workers=relationship("DivisionWorkers",back_populates="division")



class DivisionWorkers(Base):
    __tablename__="division_workers"
    id=Column(BIGINT,primary_key=True,index=True)
    division_id=Column(BIGINT,ForeignKey("divisions.id"))
    phone_number=Column(String,nullable=True)
    name=Column(String,nullable=True)
    employee_id=Column(BIGINT,nullable=True)
    created_at=Column(DateTime,server_default=func.now())
    status=Column(Integer,default=1)
    schedule_id = Column(BIGINT,ForeignKey("schedules.id"))
    schedule=relationship("Schedules",back_populates="employee")
    division=relationship("Divisions",back_populates="division_workers")
    timesheet=relationship("Timesheets",back_populates="employee")



class Schedules(Base):
    __tablename__="schedules"
    id=Column(BIGINT,primary_key=True,index=True)
    name = Column(String,nullable=True)
    code = Column(String,nullable=True)
    created_at=Column(DateTime,server_default=func.now())
    state=Column(String,nullable=True)
    employee = relationship("DivisionWorkers",back_populates="schedule")
    status = Column(Integer,default=1)



class Timesheets(Base):
    __tablename__="timesheets"
    id=Column(BIGINT,primary_key=True,index=True)
    employee_id=Column(BIGINT,ForeignKey('division_workers.id'))
    employee = relationship("DivisionWorkers",back_populates="timesheet")
    input_time=Column(DateTime,nullable=True)
    output_time=Column(DateTime,nullable=True)
    created_at=Column(DateTime,server_default=func.now())
    status=Column(Integer,default=1)


class Exports(Base):
    __tablename__ = 'exports'
    id = Column(BIGINT, primary_key=True, index=True)
    export_id = Column(String)
    is_sended = Column(Boolean,default=False)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())




