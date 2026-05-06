from fastapi import HTTPException, Response, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..legacy import ACTIVE_FLAG_TRUE, to_active_flag


def as_active_flag(value: bool) -> str:
    return to_active_flag(value)


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
    return db.query(model).filter(model.is_active == ACTIVE_FLAG_TRUE).order_by(model.sort_order.asc(), model.id.asc()).all()


def list_active_entities_by_category(model, category: str | None, db: Session):
    query = db.query(model).filter(model.is_active == ACTIVE_FLAG_TRUE)
    if category:
        query = query.filter(func.lower(model.category) == category.strip().lower())
    return query.order_by(model.sort_order.asc(), model.id.asc()).all()


def list_active_categories(model, db: Session):
    return (
        db.query(model.category, func.count(model.id))
        .filter(model.is_active == ACTIVE_FLAG_TRUE)
        .group_by(model.category)
        .order_by(func.lower(model.category).asc())
        .all()
    )


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
