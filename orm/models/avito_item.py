import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.sql import func

from .. import Base

class AbsAvitoBase(Base):
    __abstract__ = True

    def to_dict(self):
        return { 
            field.name: getattr(self, field.name) for field in self.__table__.c
        }


class AvitoItemStatus(enum.Enum):
    ACTIVE = 'active'
    CLOSE = 'close'

class AvitoItems(AbsAvitoBase):
    __tablename__ = "avito_items"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, default="")
    price = Column(Integer)
    address = Column(String, nullable=False, default="")
    descriptrion = Column(String, nullable=False, default="")
    publication_date = Column(DateTime(timezone=True))
    watch_count = Column(Integer)
    url = Column(String, nullable=False, default="")
    status = Column(Enum(AvitoItemStatus), default=AvitoItemStatus.ACTIVE)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
