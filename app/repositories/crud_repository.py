from __future__ import annotations
from typing import Any, Type
from sqlalchemy.orm import Session
from app.interfaces.icrud import ICrud

class CrudRepository(ICrud):
    def __init__(self, db: Session, model: Type[Any]):
        self.db = db
        self.model = model

    def create(self, entity: Any) -> Any:
        self.db.add(entity)
        return entity

    def get_by_id(self, entity_id: int) -> Any | None:
        return self.db.get(self.model, entity_id)

    def update(self, entity: Any) -> Any:
        return self.db.merge(entity)

    def delete(self, entity: Any) -> None:
        self.db.delete(entity)