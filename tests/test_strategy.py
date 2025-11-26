"""Quick test for Strategy pattern validation"""
from app.validation import OrderValidator

validator = OrderValidator()

# Test case 1: valid order
record1 = {
    'order_id': 'TEST-001',
    'customer_name': 'John Doe',
    'total_amount': '100.50',
    'order_date': '2025-11-26',
    'status': 'pending'
}
is_valid, errors = validator.validate(record1.copy())
print(f'Test 1 (valid): Valid={is_valid}, Errors={errors}')

# Test case 2: invalid customer name (has digits)
record2 = record1.copy()
record2['customer_name'] = 'John123'
is_valid, errors = validator.validate(record2)
print(f'Test 2 (invalid name): Valid={is_valid}, Errors={errors}')

# Test case 3: negative amount
record3 = record1.copy()
record3['total_amount'] = '-50'
is_valid, errors = validator.validate(record3)
print(f'Test 3 (negative amount): Valid={is_valid}, Errors={errors}')

# Test case 4: date format parsing
record4 = record1.copy()
record4['order_date'] = '26/11/2025'
is_valid, errors = validator.validate(record4)
print(f'Test 4 (date format): Valid={is_valid}, Parsed date={record4.get("order_date")}, Errors={errors}')
