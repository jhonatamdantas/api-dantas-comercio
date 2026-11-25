from decimal import Decimal


def money(value) -> Decimal:
    return Decimal(str(value))


def sale_payload(*items, client_id=None, payment_method="pix") -> dict:
    payload = {
        "payment_method": payment_method,
        "items": [{"product_id": pid, "quantity": qty} for pid, qty in items],
    }
    if client_id is not None:
        payload["client_id"] = client_id
    return payload