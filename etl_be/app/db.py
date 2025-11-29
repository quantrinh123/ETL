from __future__ import annotations

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Integer,
    Numeric,
    String,
    Text,
    create_engine,
    text,
)
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import get_settings

Base = declarative_base()
settings = get_settings()


class OrdersClean(Base):
    __tablename__ = "orders_clean"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String(50), unique=True, nullable=False)
    source = Column(String(20))
    order_date = Column(Date, nullable=False)
    customer_id = Column(String(50))
    customer_name = Column(String(100), nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)
    status = Column(String(50))
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))


class OrdersError(Base):
    __tablename__ = "orders_error"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String(50), unique=True, nullable=False)
    source = Column(String(20))
    order_date = Column(Text)
    customer_id = Column(Text)
    customer_name = Column(Text)
    total_amount = Column(Text)
    status = Column(Text)
    error_reason = Column(Text)
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))


class Orders(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String(50), unique=True, nullable=False)
    source = Column(String(20))
    order_date = Column(Text)
    customer_id = Column(Text)
    customer_name = Column(Text)
    total_amount = Column(Text)
    status = Column(Text)
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))


def get_engine(settings_override=None):
    s = settings_override or settings
    url = (
        f"postgresql+psycopg2://{s.postgres_user}:{s.postgres_password}"
        f"@{s.postgres_host}:{s.postgres_port}/{s.postgres_db}"
    )
    return create_engine(url, pool_pre_ping=True)


def get_session_factory(engine=None):
    engine = engine or get_engine()
    return sessionmaker(bind=engine, expire_on_commit=False)


def create_tables(engine=None) -> None:
    engine = engine or get_engine()
    Base.metadata.create_all(engine)


def upsert_clean(session, record: dict) -> None:
    stmt = insert(OrdersClean).values(**record)
    update_set = {
        "source": stmt.excluded.source,
        "order_date": stmt.excluded.order_date,
        "customer_id": stmt.excluded.customer_id,
        "customer_name": stmt.excluded.customer_name,
        "total_amount": stmt.excluded.total_amount,
        "status": stmt.excluded.status,
    }
    session.execute(stmt.on_conflict_do_update(index_elements=[OrdersClean.order_id], set_=update_set))


def upsert_error(session, record: dict) -> None:
    stmt = insert(OrdersError).values(**record)
    update_set = {
        "source": stmt.excluded.source,
        "order_date": stmt.excluded.order_date,
        "customer_id": stmt.excluded.customer_id,
        "customer_name": stmt.excluded.customer_name,
        "total_amount": stmt.excluded.total_amount,
        "status": stmt.excluded.status,
        "error_reason": stmt.excluded.error_reason,
    }
    session.execute(stmt.on_conflict_do_update(index_elements=[OrdersError.order_id], set_=update_set))


def upsert_order(session, record: dict) -> None:
    stmt = insert(Orders).values(**record)
    update_set = {
        "source": stmt.excluded.source,
        "order_date": stmt.excluded.order_date,
        "customer_id": stmt.excluded.customer_id,
        "customer_name": stmt.excluded.customer_name,
        "total_amount": stmt.excluded.total_amount,
        "status": stmt.excluded.status,
    }
    session.execute(stmt.on_conflict_do_update(index_elements=[Orders.order_id], set_=update_set))
