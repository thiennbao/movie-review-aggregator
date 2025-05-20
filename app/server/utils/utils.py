from datetime import date, datetime

def serialize_date(obj):
    """Convert date or datetime objects to ISO 8601 strings."""
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    return obj