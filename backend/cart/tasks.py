from config.celery import app

from cart.services import cleanup_expired_guest_carts


@app.task(
    bind=True,
    name="cart.cleanup_expired_guest_carts",
    acks_late=True,
    reject_on_worker_lost=True,
)
def cleanup_expired_guest_carts_task(self):
    result = cleanup_expired_guest_carts()
    return {
        "status": "ok",
        "deleted_carts": result["deleted_carts"],
        "deleted_items": result["deleted_items"],
        "cart_ids": result["cart_ids"],
    }
