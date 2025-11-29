from app.validation import validate_order


def test_validate_order_success():
    record = {
        "order_id": "ON-1",
        "order_date": "2025-11-01",
        "customer_id": "C1",
        "customer_name": "Le Thi Nga",
        "total_amount": "120.5",
        "status": "PAID",
    }
    valid, errors = validate_order(record.copy())
    assert valid
    assert errors == []
    assert record["order_date"] == "2025-11-01"


def test_validate_order_failure():
    record = {
        "order_id": "",
        "order_date": "12-32-2025",
        "customer_id": "",
        "customer_name": "Pham 123",
        "total_amount": "-10",
        "status": "",
    }
    valid, errors = validate_order(record)
    assert not valid
    assert "order_id missing" in errors
    assert "customer_name has digits" in errors
    assert any("order_date" in err for err in errors)

