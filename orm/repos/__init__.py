from functools import lru_cache
from typing import Generic, Iterable, Optional, Type, TypeVar, List

from sqlalchemy import Column
from sqlalchemy.orm import Query, Session

from orm import Database

T = TypeVar("T")

class Service(Generic[T]):
    def __init__(self, session: Session = None) -> None:
        self.__session__ = session or Database._session_factory()

    @property
    def session(self) -> Session:
        return self.__session__

    @property
    @lru_cache(maxsize=None)
    def model(self) -> Type[T]:
        for base in type(self).__orig_bases__:
            if hasattr(base, "__args__"):
                return base.__args__[0]

    @property
    def query(self) -> Query:
        return self.session.query(self.model)
    
    def get_all(self, order_by: Optional[Column] = None) -> Iterable[T]:
        query = self.query
        if order_by is not None:
            query = query.order_by(order_by)
        return query.all()

    def get_by_id(self, id: int) -> Optional[T]:
        return self.query.filter(self.model.id == id).first()
    
    def create(self, item: T, flush: bool = True) -> T:
        self.session.add(item)
        if flush:
            self.session.flush((item,))

        return item
    
    def create_all(self, items: List[T], flush: bool = True) -> T:
        self.session.add_all(items)
        if flush:
            self.session.flush()

        return items

    def update(self, item: T, flush: bool = True) -> T:
        item = self.session.merge(item)
        if flush:
            self.session.flush((item,))

        return item