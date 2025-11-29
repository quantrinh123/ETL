from __future__ import annotations

import csv
import logging
from pathlib import Path

import pika

from .config import get_settings
from .logging_conf import configure_logging
from .utils import json_dumps

LOGGER = logging.getLogger("producer.online")


def publish_csv(path: Path) -> None:
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

    with path.open(encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            payload = {"source": "online", "table": "orders", "data": row}
            channel.basic_publish(
                exchange="",
                routing_key=settings.rabbitmq_queue,
                body=json_dumps(payload),
                properties=pika.BasicProperties(delivery_mode=2),
            )
            LOGGER.info("Published online order %s", row.get("order_id"))

    connection.close()


if __name__ == "__main__":
    settings = get_settings()
    csv_path = settings.upload_dir / "online_orders.csv"
    publish_csv(csv_path)

