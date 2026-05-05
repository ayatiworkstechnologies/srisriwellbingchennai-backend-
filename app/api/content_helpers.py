from fastapi import HTTPException, Response, status
from sqlalchemy.orm import Session


def as_active_flag(value: bool) -> str:
    return "true" if value else "false"


def delete_entity(model, entity_id: int, label: str, db: Session):
    item = db.query(model).filter(model.id == entity_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{label} not found")
    db.delete(item)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def list_entities(model, db: Session):
    return db.query(model).order_by(model.sort_order.asc(), model.id.asc()).all()


def list_active_entities(model, db: Session):
    return db.query(model).filter(model.is_active == "true").order_by(model.sort_order.asc(), model.id.asc()).all()


def create_entity(model, payload, db: Session, **extra_fields):
    values = payload.model_dump()
    values.update(extra_fields)
    item = model(**values)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def update_entity(item, payload, db: Session, **extra_fields):
    values = payload.model_dump()
    values.update(extra_fields)
    for field_name, field_value in values.items():
        setattr(item, field_name, field_value)
    db.commit()
    db.refresh(item)
    return item


def get_entity_or_404(model, entity_id: int, label: str, db: Session):
    item = db.query(model).filter(model.id == entity_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{label} not found")
    return item
