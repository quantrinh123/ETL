from app.transform import CANONICAL_COLUMNS, normalize_order


def test_normalize_order_mapping():
    row = {
        "id": "OF-1",
        "date": "01/11/2025",
        "cust_id": "C-1",
        "name": "Nguyen Van A",
        "total": "200",
        "order_status": "DONE",
    }
    canonical = normalize_order("offline", row)
    assert list(canonical.keys()) == CANONICAL_COLUMNS
    assert canonical["order_id"] == "OF-1"
    assert canonical["customer_id"] == "C-1"
    assert canonical["status"] == "DONE"

