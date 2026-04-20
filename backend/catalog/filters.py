import django_filters

from catalog.models import Product


class ProductFilter(django_filters.FilterSet):
    category = django_filters.CharFilter(field_name="category__slug")
    franchise = django_filters.CharFilter(field_name="franchise__slug")
    min_price = django_filters.NumberFilter(field_name="base_price", lookup_expr="gte")
    max_price = django_filters.NumberFilter(field_name="base_price", lookup_expr="lte")
    size = django_filters.CharFilter(field_name="variants__size")
    color = django_filters.CharFilter(
        field_name="variants__color", lookup_expr="iexact"
    )
    in_stock = django_filters.BooleanFilter(method="filter_in_stock")

    class Meta:
        model = Product
        fields = (
            "category",
            "franchise",
            "min_price",
            "max_price",
            "size",
            "color",
            "in_stock",
        )

    def filter_in_stock(self, queryset, name, value):
        if value:
            return queryset.filter(
                variants__is_active=True, variants__stock_quantity__gt=0
            ).distinct()
        return queryset
