from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any

class ICrud(ABC):
    """
    Contrato CRUD para *repositories*.
    Regras:
    - Não comita/rollback.
    - Não faz regra de negócio (isso é service).
    - Não retorna JSON.
    """

    @abstractmethod
    def create(self, entity: Any) -> Any: ...

    @abstractmethod
    def get_by_id(self, entity_id: int) -> Any | None: ...

    @abstractmethod
    def update(self, entity: Any) -> Any: ...

    @abstractmethod
    def delete(self, entity: Any) -> None: ...