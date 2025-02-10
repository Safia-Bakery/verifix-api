from sqlalchemy.orm import Session
from verifix.models.model import Exports



def createExport(db:Session,export_id):
    query = Exports(export_id=export_id)
    db.add(query)
    db.commit()
    return query


def getIsSended(db:Session):
    query = db.query(Exports).filter(Exports.is_sended==False).first()
    return query


def updateIsSended(db:Session,export_id):
    query = db.query(Exports).filter(Exports.export_id==export_id).first()
    if query:
        query.is_sended = True
        db.commit()
    return query
