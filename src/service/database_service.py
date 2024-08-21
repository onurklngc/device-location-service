import logging
import os
import time

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from src.model import Base

logger = logging.getLogger(__name__)


class DatabaseService:
    def __init__(self, database_url=None):
        if database_url:
            engine = create_engine(database_url)
            self.session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            Base.metadata.create_all(bind=engine)

    def get_db(self):
        db: Session = self.session_local()
        try:
            yield db
        finally:
            if hasattr(db, "close"):
                db.close()


def connect_to_db(database_url) -> DatabaseService:
    while True:
        try:
            logger.info("Trying to connect to DB.")
            database_service = DatabaseService(database_url=database_url)
            logger.info("Connected to DB.")
            break
        except Exception as e:
            logger.error(f"Couldn't connect to DB({database_url}): {e}, will try again shortly after.")
            time.sleep(2)
    return database_service


if __name__ == '__main__':
    current_database_url = os.getenv("DATABASE_URL")
    db_service = DatabaseService(database_url=current_database_url)
    db_service.get_db()
