from __future__ import annotations

from typing import Dict

CANONICAL_COLUMNS = [
    "order_id",
    "source",
    "order_date",
    "customer_id",
    "customer_name",
    "total_amount",
    "status",
]


def normalize_order(source: str, row: Dict[str, str]) -> Dict[str, str]:
    """Map CSV-specific column names into the canonical schema."""
    return {
        "order_id": row.get("order_id") or row.get("id") or row.get("orderId") or "",
        "source": source,
        "order_date": row.get("order_date") or row.get("date") or "",
        "customer_id": row.get("customer_id") or row.get("cust_id") or "",
        "customer_name": row.get("customer_name") or row.get("name") or "",
        "total_amount": row.get("total_amount") or row.get("amount") or row.get("total") or "0",
        "status": row.get("status") or row.get("order_status") or "PENDING",
    }

