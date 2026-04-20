class StockValidationError(ValueError):
    pass


def available_to_sell(variant):
    stock_quantity = getattr(variant, "stock_quantity", 0)
    reserved_quantity = getattr(variant, "reserved_quantity", 0)
    return max(stock_quantity - reserved_quantity, 0)


def ensure_can_fulfill(variant, requested_quantity):
    if requested_quantity <= 0:
        raise StockValidationError("Requested quantity must be positive.")
    if not getattr(variant, "is_active", True):
        raise StockValidationError("Variant is not active.")
    if requested_quantity > available_to_sell(variant):
        raise StockValidationError("Insufficient stock.")
    return None
