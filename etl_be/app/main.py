from __future__ import annotations

import csv
import io
import logging
from typing import Iterable, Dict, Type, List, Any

import pika
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from .config import get_settings
from .db import create_tables, get_engine, get_session_factory, OrdersClean, OrdersError
from .logging_conf import configure_logging
from .utils import json_dumps

LOGGER = logging.getLogger("api")
app = FastAPI(title="Orders ETL API", version="1.0.0")
settings = get_settings()
engine = None
SessionLocal = None


class OrdersResponse(BaseModel):
    items: List[Dict[str, Any]]
    count: int


def publish_rows(source: str, rows: Iterable[Dict[str, object]]) -> int:
    """Publish rows to RabbitMQ with the given source label."""
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=settings.rabbitmq_host,
            port=settings.rabbitmq_port,
            credentials=pika.PlainCredentials(settings.rabbitmq_user, settings.rabbitmq_password),
        )
    )
    channel = connection.channel()
    channel.queue_declare(queue=settings.rabbitmq_queue, durable=True)

    count = 0
    for row in rows:
        payload = {"source": source, "table": "orders", "data": row}
        channel.basic_publish(
            exchange="",
            routing_key=settings.rabbitmq_queue,
            body=json_dumps(payload),
            properties=pika.BasicProperties(delivery_mode=2),
        )
        count += 1
    connection.close()
    return count


@app.on_event("startup")
async def startup_event() -> None:
    configure_logging()
    global engine
    engine = get_engine(settings)
    global SessionLocal
    SessionLocal = get_session_factory(engine)
    if settings.migrate_on_start:
        await run_in_threadpool(create_tables, engine)
        LOGGER.info("Tables ensured on startup")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


def validate_source(source: str) -> str:
    normalized = source.lower()
    if normalized not in {"online", "offline"}:
        raise HTTPException(status_code=400, detail="source must be 'online' or 'offline'")
    return normalized


@app.post("/upload/{source}")
async def upload_csv(source: str, file: UploadFile = File(...)) -> dict[str, int]:
    normalized = validate_source(source)
    content = await file.read()
    try:
        text_stream = io.StringIO(content.decode("utf-8"))
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="Upload must be UTF-8 encoded CSV") from exc

    reader = csv.DictReader(text_stream)
    rows = list(reader)
    if not rows:
        raise HTTPException(status_code=400, detail="CSV file is empty")

    count = await run_in_threadpool(publish_rows, normalized, rows)
    return {"published": count}


def _row_to_dict(row: Any, is_clean: bool) -> Dict[str, Any]:
    base = {
        "order_id": row.order_id,
        "source": row.source,
        "order_date": row.order_date.isoformat() if is_clean and row.order_date else row.order_date,
        "customer_id": row.customer_id,
        "customer_name": row.customer_name,
        "total_amount": float(row.total_amount) if is_clean and row.total_amount is not None else row.total_amount,
        "status": row.status,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }
    if not is_clean:
        base["error_reason"] = row.error_reason
    return base


def _fetch_rows(model: Type, limit: int, is_clean: bool) -> List[Dict[str, Any]]:
    session = SessionLocal()
    try:
        rows = session.query(model).order_by(model.id.desc()).limit(limit).all()
        return [_row_to_dict(r, is_clean=is_clean) for r in rows]
    finally:
        session.close()


@app.get("/orders/clean", response_model=OrdersResponse)
async def get_orders_clean(limit: int = 100) -> OrdersResponse:
    items = await run_in_threadpool(_fetch_rows, OrdersClean, limit, True)
    return OrdersResponse(items=items, count=len(items))


@app.get("/orders/error", response_model=OrdersResponse)
async def get_orders_error(limit: int = 100) -> OrdersResponse:
    items = await run_in_threadpool(_fetch_rows, OrdersError, limit, False)
    return OrdersResponse(items=items, count=len(items))
