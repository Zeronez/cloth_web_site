from django.conf import settings
from django.db import models

from catalog.models import Product


class FavoriteProduct(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="favorite_products",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        related_name="favorited_by",
        on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "product"],
                name="unique_user_favorite_product",
            )
        ]

    def __str__(self):
        return f"{self.user_id} -> {self.product_id}"
