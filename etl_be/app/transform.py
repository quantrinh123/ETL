from __future__ import annotations

import re
from typing import Dict, Tuple

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


def clean_customer_name(name: str) -> str | None:
    """
    Clean and fix customer name according to rules:
    - Remove digits
    - Remove special characters (keep spaces and Vietnamese characters)
    - Capitalize first letter of each word
    - Trim whitespace
    - Limit to 50 characters
    Returns None if cannot be fixed.
    """
    if not name:
        return None
    
    # Remove digits
    cleaned = re.sub(r'\d', '', name)
    
    # Remove special characters but keep Vietnamese characters, spaces, and hyphens
    # Allow Vietnamese unicode range: \u00C0-\u1EF9
    cleaned = re.sub(r'[^\w\s\u00C0-\u1EF9-]', '', cleaned, flags=re.UNICODE)
    
    # Normalize whitespace
    cleaned = ' '.join(cleaned.split())
    
    # Capitalize first letter of each word
    # Handle Vietnamese names properly
    words = cleaned.split()
    capitalized_words = []
    for word in words:
        if word:
            # Capitalize first character, keep rest lowercase
            capitalized_words.append(word[0].upper() + word[1:].lower())
    cleaned = ' '.join(capitalized_words)
    
    # Trim and limit length
    cleaned = cleaned.strip()
    if len(cleaned) > 50:
        cleaned = cleaned[:50].rstrip()
    
    # Return None if empty after cleaning
    if not cleaned:
        return None
    
    return cleaned


def clean_total_amount(amount: str) -> str | None:
    """
    Clean and convert total_amount to valid numeric string.
    Removes currency symbols, commas, spaces.
    Returns None if cannot be converted.
    """
    if not amount:
        return None
    
    # Remove currency symbols, commas, spaces
    cleaned = re.sub(r'[^\d.]', '', str(amount))
    
    # Try to convert to float
    try:
        value = float(cleaned)
        if value <= 0:
            return None
        return str(value)
    except (ValueError, TypeError):
        return None


def clean_order_date(date_str: str) -> str | None:
    """
    Clean order_date by removing extra whitespace.
    Actual format validation is done in validation.py
    """
    if not date_str:
        return None
    return date_str.strip()


def clean_status(status: str) -> str | None:
    """
    Clean status field by trimming and capitalizing.
    """
    if not status:
        return None
    return status.strip().upper()


def clean_and_fix_errors(record: Dict[str, str]) -> Tuple[Dict[str, str], bool]:
    """
    Tự động sửa lỗi nếu có thể (Nếu chỉnh sửa được thì thực hiện).
    
    Args:
        record: Dictionary chứa dữ liệu order cần clean
        
    Returns:
        Tuple[cleaned_record, was_fixed]: 
        - cleaned_record: Record đã được clean/fix
        - was_fixed: True nếu có thay đổi, False nếu không
    """
    cleaned = record.copy()
    was_fixed = False
    
    # Clean customer_name
    if "customer_name" in cleaned:
        original = cleaned["customer_name"]
        fixed = clean_customer_name(original)
        if fixed is not None and fixed != original:
            cleaned["customer_name"] = fixed
            was_fixed = True
        elif fixed is not None:
            cleaned["customer_name"] = fixed
    
    # Clean total_amount
    if "total_amount" in cleaned:
        original = cleaned["total_amount"]
        fixed = clean_total_amount(original)
        if fixed is not None and fixed != original:
            cleaned["total_amount"] = fixed
            was_fixed = True
        elif fixed is not None:
            cleaned["total_amount"] = fixed
    
    # Clean order_date
    if "order_date" in cleaned:
        original = cleaned["order_date"]
        fixed = clean_order_date(original)
        if fixed is not None and fixed != original:
            cleaned["order_date"] = fixed
            was_fixed = True
        elif fixed is not None:
            cleaned["order_date"] = fixed
    
    # Clean status
    if "status" in cleaned:
        original = cleaned["status"]
        fixed = clean_status(original)
        if fixed is not None and fixed != original:
            cleaned["status"] = fixed
            was_fixed = True
        elif fixed is not None:
            cleaned["status"] = fixed
    
    # Clean order_id - remove extra whitespace
    if "order_id" in cleaned and cleaned["order_id"]:
        original = cleaned["order_id"]
        fixed = original.strip()
        if fixed != original:
            cleaned["order_id"] = fixed
            was_fixed = True
    
    return cleaned, was_fixed

