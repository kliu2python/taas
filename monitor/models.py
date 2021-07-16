from contextlib import contextmanager

import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.ext import declarative
from sqlalchemy.orm import sessionmaker

from monitor.constants import SYS_CONFIG

Session = sessionmaker()
engine = create_engine(
    SYS_CONFIG.db, pool_size=30, max_overflow=0, pool_recycle=300
)
Session.configure(bind=engine)
Base = declarative.declarative_base()


def get_session():
    return Session()


class SessionMixIn:
    @staticmethod
    @contextmanager
    def get_once_session():
        session = get_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    @classmethod
    def add(cls, session, data):
        if not session:
            session = Session()
        session.add(cls(**data))
        return session

    @classmethod
    def add_once(cls, data):
        with cls.get_once_session() as session:
            cls.add(session, data)

    @classmethod
    def query(cls, session, query_filter=None):
        result = session.query(cls)
        if query_filter is not None:
            result = result.filter(query_filter)
        return result

    @classmethod
    def query_once(cls, query_filter=None):
        with cls.get_once_session() as session:
            result = cls.query(session, query_filter)
        return result


class DbBaseMixIn:
    @declarative.declared_attr
    def __tablename__(self):
        return self.__name__.lower()


class LogEntry(Base, DbBaseMixIn, SessionMixIn):
    id = sa.Column("id", sa.String(length=36), nullable=False, primary_key=True)
    create_at = sa.Column("create_at", sa.DateTime(), nullable=False)
    repeats = sa.Column("repeats", sa.Numeric(), nullable=False)
    alert_type = sa.Column("alert_type", sa.String(length=15), nullable=False)
    value = sa.Column("value", sa.Numeric(), nullable=True)
    operation = sa.Column("operation", sa.String(length=10), nullable=True)

    __table_args__ = (
        sa.Index("idx_logentry_id", "id", ),
        sa.UniqueConstraint(id, name='unq_logentry_id'),
    )


class Image(Base, DbBaseMixIn, SessionMixIn):
    id = sa.Column(
        "id", sa.String(length=36), nullable=False, primary_key=True
    )
    img_data = sa.Column("img_data", sa.Text(length=16777216), nullable=True)
    img_url = sa.Column("img_url", sa.String(255), nullable=True)

    __table_args__ = (
        sa.Index("idx_image_id", "id", ),
        sa.UniqueConstraint(id, name='unq_image_id'),
    )


class Message(Base, DbBaseMixIn, SessionMixIn):
    id = sa.Column(
        "id", sa.String(length=36), nullable=False, primary_key=True
    )
    session_id = sa.Column(
        sa.ForeignKey("logentry.id", ondelete="CASCADE"), nullable=False
    )
    create_at = sa.Column("create_at", sa.DateTime(), nullable=False)
    message = sa.Column("message", sa.Text(length=16777216), nullable=True)
    attachment_id = sa.Column(
        "attachment_id", sa.String(length=36), nullable=True
    )

    __table_args__ = (
        sa.Index("idx_message_id", "id", ),
        sa.UniqueConstraint(id, name='unq_message_id'),
    )


def close(session):
    try:
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
