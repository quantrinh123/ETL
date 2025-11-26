from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict

import pika

from .config import get_settings
from .logging_conf import configure_logging
from .transform import CANONICAL_COLUMNS, normalize_order
from .utils import append_row, json_loads
from .validation import validate_order

LOGGER = logging.getLogger("consumer.orders")

RAW_HEADERS = [
    "order_id",
    "order_date",
    "customer_id",
    "customer_name",
    "total_amount",
    "status",
]
ERROR_HEADERS = CANONICAL_COLUMNS + ["error_reason"]


def staging_path(base: Path, source: str) -> Path:
    return base / f"{source}_orders_raw.csv"


def handle_message(body: bytes, settings) -> None:
    message: Dict[str, object] = json_loads(body)
    source = str(message.get("source", "unknown"))
    data = dict(message.get("data", {}))

    raw_row = {
        "order_id": data.get("order_id") or data.get("id") or "",
        "order_date": data.get("order_date") or data.get("date") or "",
        "customer_id": data.get("customer_id") or data.get("cust_id") or "",
        "customer_name": data.get("customer_name") or data.get("name") or "",
        "total_amount": data.get("total_amount") or data.get("amount") or "",
        "status": data.get("status") or data.get("order_status") or "",
    }

    append_row(staging_path(settings.staging_dir, source), RAW_HEADERS, raw_row)

    canonical = normalize_order(source, data)
    is_valid, errors = validate_order(canonical)

    if is_valid:
        append_row(settings.output_dir / "orders_clean.csv", CANONICAL_COLUMNS, canonical)
        LOGGER.info("Accepted %s order %s", source, canonical["order_id"])
    else:
        error_row = canonical.copy()
        error_row["error_reason"] = "; ".join(errors)
        append_row(settings.output_dir / "orders_error.csv", ERROR_HEADERS, error_row)
        LOGGER.warning("Rejected %s order %s -> %s", source, canonical["order_id"], error_row["error_reason"])


def main() -> None:
    settings = get_settings()
    configure_logging()

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
        handle_message(body, settings)
        ch.basic_ack(delivery_tag=method.delivery_tag)

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


if __name__ == "__main__":
    main()

