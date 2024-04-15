from sqlalchemy.orm import Session
from typing import Optional
import bcrypt

import pytz
from sqlalchemy.sql import func
from datetime import datetime,timedelta
from sqlalchemy import or_, and_, Date, cast
from uuid import UUID
from verifix.schemas import schema
from verifix.models.model import Divisions



def update_division(db:Session,form_data:schema.DivisionUpdate):
    query = db.query(Divisions).filter(Divisions.id == form_data.id).first()
    if form_data.limit is not None:
        query.limit = form_data.limit
    if form_data.name is not None:
        query.name = form_data.name
    db.commit()
    db.refresh(query)
    return query


def get_divisions(db: Session,name:Optional[str]=None,id:Optional[int]=None):
    query = db.query(Divisions)
    if name is not None:
        query = query.filter(Divisions.name.ilike(f"%{name}%"))
    if id is not None:
        query = query.filter(Divisions.id == id)
    return query.all()

def division_create(db:Session,id,name,code,state,parent_id):
    db_division = Divisions(
        id=id,
        name=name,
        code=code,
        state=state,
        parent_id=parent_id,
    )
    try:
        db.add(db_division)
        db.commit()
        db.refresh(db_division)
        return db_division
    except Exception as e:
        db.rollback()
        return True

