from __future__ import annotations

import logging
from datetime import date
from typing import Dict

import pika
from sqlalchemy.dialects.postgresql import insert

from .config import get_settings
from .db import (
    OrdersClean,
    OrdersError,
    create_tables,
    get_engine,
    get_session_factory,
    upsert_order,
)
from .logging_conf import configure_logging
from .transform import clean_and_fix_errors, normalize_order
from .utils import json_loads
from .validation import validate_order

LOGGER = logging.getLogger("consumer.orders")

def handle_message(body: bytes, settings, SessionLocal) -> None:
    message: Dict[str, object] = json_loads(body)
    source = str(message.get("source", "unknown"))
    data = dict(message.get("data", {}))

    canonical = normalize_order(source, data)
    raw_record = canonical.copy()
    
    # Tự động sửa lỗi nếu có thể (Nếu chỉnh sửa được thì thực hiện)
    canonical, was_fixed = clean_and_fix_errors(canonical)
    if was_fixed:
        LOGGER.info("Auto-fixed errors in order %s from source %s", canonical.get("order_id"), source)
    
    is_valid, errors = validate_order(canonical)

    session = SessionLocal()
    try:
        upsert_order(session, raw_record)
        if is_valid:
            stmt = insert(OrdersClean).values(
                order_id=canonical["order_id"],
                source=canonical["source"],
                order_date=date.fromisoformat(canonical["order_date"]) if canonical["order_date"] else None,
                customer_id=canonical["customer_id"],
                customer_name=canonical["customer_name"],
                total_amount=float(canonical["total_amount"]),
                status=canonical["status"],
            )
            session.execute(
                stmt.on_conflict_do_update(
                    index_elements=[OrdersClean.order_id],
                    set_={
                        "source": stmt.excluded.source,
                        "order_date": stmt.excluded.order_date,
                        "customer_id": stmt.excluded.customer_id,
                        "customer_name": stmt.excluded.customer_name,
                        "total_amount": stmt.excluded.total_amount,
                        "status": stmt.excluded.status,
                    },
                )
            )
            LOGGER.info("Accepted %s order %s -> stored in orders_clean", source, canonical["order_id"])
        else:
            error_reason = "; ".join(errors)
            stmt = insert(OrdersError).values(
                order_id=canonical["order_id"],
                source=canonical["source"],
                order_date=canonical["order_date"],
                customer_id=canonical["customer_id"],
                customer_name=canonical["customer_name"],
                total_amount=canonical["total_amount"],
                status=canonical["status"],
                error_reason=error_reason,
            )
            session.execute(
                stmt.on_conflict_do_update(
                    index_elements=[OrdersError.order_id],
                    set_={
                        "source": stmt.excluded.source,
                        "order_date": stmt.excluded.order_date,
                        "customer_id": stmt.excluded.customer_id,
                        "customer_name": stmt.excluded.customer_name,
                        "total_amount": stmt.excluded.total_amount,
                        "status": stmt.excluded.status,
                        "error_reason": stmt.excluded.error_reason,
                    },
                )
            )
            LOGGER.warning("Rejected %s order %s -> %s", source, canonical["order_id"], error_reason)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def main() -> None:
    settings = get_settings()
    configure_logging()

    engine = get_engine(settings)
    create_tables(engine)
    SessionLocal = get_session_factory(engine)

    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=settings.rabbitmq_host,
            port=settings.rabbitmq_port,
            credentials=pika.PlainCredentials(settings.rabbitmq_user, settings.rabbitmq_password),
        )
    )
    channel = connection.channel()
    channel.queue_declare(queue=settings.rabbitmq_queue, durable=True)

    def callback(ch, method, properties, body):
        try:
            handle_message(body, settings, SessionLocal)
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception:
            LOGGER.exception("Failed to handle message, requeueing")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    channel.basic_qos(prefetch_count=10)
    channel.basic_consume(queue=settings.rabbitmq_queue, on_message_callback=callback)
    LOGGER.info("Consumer started. Waiting for messages...")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        LOGGER.info("Consumer stopped.")
        channel.stop_consuming()
    finally:
        connection.close()
        engine.dispose()


if __name__ == "__main__":
    main()

