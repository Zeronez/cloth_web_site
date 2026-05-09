from rest_framework.permissions import BasePermission


class IsObjectOwner(BasePermission):
    """Require retrieved objects to belong to the authenticated request user."""

    message = "Object does not belong to the authenticated user."

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        owner_field = getattr(view, "owner_field", "user")
        owner = obj
        for part in owner_field.split("__"):
            owner = getattr(owner, part, None)
            if owner is None:
                return False

        return getattr(owner, "pk", owner) == request.user.pk
