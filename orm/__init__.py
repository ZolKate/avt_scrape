import os
from contextlib import contextmanager

from loguru import logger
from sqlalchemy import create_engine, orm
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session


DATABASE_FILENAME = 'avito.db'
Base = declarative_base()

class Database:
    _engine = create_engine(f'sqlite:///{os.path.join(os.getcwd(), DATABASE_FILENAME)}', echo=False)
    _session_factory = orm.scoped_session(
        orm.sessionmaker(autocommit=False, autoflush=False, bind=_engine),
    )

    @staticmethod
    def create_database():
        Base.metadata.create_all(Database._engine)

    @staticmethod
    @contextmanager
    def session(old_session: Session = None):
        if old_session is None:
            session: Session = Database._session_factory()
        else:
            session: Session = old_session

        try:
            yield session
        except Exception:
            logger.exception("Session rollback because of exception")
            session.rollback()
            raise
        finally:
            session.commit()
            session.close()

from .models.avito_item import AvitoItems