from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db


def make_crud_router(prefix, tag, model, create_schema, update_schema, out_schema):
    """Standard list/get/create/patch/delete router for a single table."""
    router = APIRouter(prefix=prefix, tags=[tag])

    def get_or_404(db: Session, item_id: int):
        obj = db.get(model, item_id)
        if not obj:
            raise HTTPException(404, f"{tag} {item_id} not found")
        return obj

    def commit(db: Session):
        try:
            db.commit()
        except IntegrityError as e:  # e.g. bad foreign key
            db.rollback()
            raise HTTPException(422, "Integrity error: check referenced ids") from e

    @router.get("", response_model=list[out_schema])
    def list_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
        stmt = select(model).order_by(model.id.desc()).offset(skip).limit(min(limit, 500))
        return db.scalars(stmt).all()

    @router.get("/{item_id}", response_model=out_schema)
    def get_item(item_id: int, db: Session = Depends(get_db)):
        return get_or_404(db, item_id)

    @router.post("", response_model=out_schema, status_code=201)
    def create_item(body: create_schema, db: Session = Depends(get_db)):
        obj = model(**{k: v for k, v in body.model_dump().items() if v is not None})
        db.add(obj)
        commit(db)
        db.refresh(obj)
        return obj

    @router.patch("/{item_id}", response_model=out_schema)
    def update_item(item_id: int, body: update_schema, db: Session = Depends(get_db)):
        obj = get_or_404(db, item_id)
        for k, v in body.model_dump(exclude_unset=True).items():
            setattr(obj, k, v)
        if model.__name__ == "Task" and "status" in body.model_fields_set:
            obj.completed_at = datetime.now(timezone.utc) if obj.status == "done" else None
        commit(db)
        db.refresh(obj)
        return obj

    @router.delete("/{item_id}", status_code=204)
    def delete_item(item_id: int, db: Session = Depends(get_db)):
        db.delete(get_or_404(db, item_id))
        commit(db)

    return router
