from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Tuple

ACCEPTED_DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y")


class ValidationStrategy(ABC):
    """Base class for validation strategies"""
    
    @abstractmethod
    def validate(self, record: Dict[str, str]) -> List[str]:
        """Return list of errors. Empty list = valid."""
        pass


class OrderIdStrategy(ValidationStrategy):
    """Validates order_id field"""
    
    def validate(self, record: Dict[str, str]) -> List[str]:
        if not record.get("order_id"):
            return ["order_id missing"]
        return []


class CustomerNameStrategy(ValidationStrategy):
    """Validates customer_name field"""
    
    def validate(self, record: Dict[str, str]) -> List[str]:
        errors = []
        name = (record.get("customer_name") or "").strip()
        if not name:
            errors.append("customer_name missing")
        elif any(char.isdigit() for char in name):
            errors.append("customer_name has digits")
        elif len(name) > 50:
            errors.append("customer_name too long")
        return errors


class TotalAmountStrategy(ValidationStrategy):
    """Validates total_amount field"""
    
    def validate(self, record: Dict[str, str]) -> List[str]:
        errors = []
        total_amount = record.get("total_amount")
        try:
            amount = float(total_amount)
            if amount <= 0:
                errors.append("total_amount must be > 0")
        except (TypeError, ValueError):
            errors.append("total_amount not numeric")
        return errors


class OrderDateStrategy(ValidationStrategy):
    """Validates order_date field and normalizes format"""
    
    def validate(self, record: Dict[str, str]) -> List[str]:
        date_value = record.get("order_date", "")
        for fmt in ACCEPTED_DATE_FORMATS:
            try:
                parsed = datetime.strptime(date_value.strip(), fmt)
                record["order_date"] = parsed.date().isoformat()
                return []
            except (ValueError, AttributeError):
                continue
        return ["order_date invalid format"]


class StatusStrategy(ValidationStrategy):
    """Validates status field"""
    
    def validate(self, record: Dict[str, str]) -> List[str]:
        status = (record.get("status") or "").strip()
        if not status:
            return ["status missing"]
        return []


class OrderValidator:
    """Validates order using multiple strategies (Strategy pattern)"""
    
    def __init__(self):
        self.strategies = [
            OrderIdStrategy(),
            CustomerNameStrategy(),
            TotalAmountStrategy(),
            OrderDateStrategy(),
            StatusStrategy(),
        ]
    
    def validate(self, record: Dict[str, str]) -> Tuple[bool, List[str]]:
        """Validate record using all strategies"""
        errors = []
        for strategy in self.strategies:
            errors.extend(strategy.validate(record))
        return len(errors) == 0, errors


def validate_order(record: Dict[str, str]) -> Tuple[bool, List[str]]:
    """Legacy function for backward compatibility"""
    validator = OrderValidator()
    return validator.validate(record)

