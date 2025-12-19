from rest_framework import exceptions
from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsProfileOwnerOrReadOnly(BasePermission):
    """Only the owner may modify a profile, everyone may read.
    """

    message = "You can only edit your own profile."

    def has_object_permission(self, request, view, obj) -> bool:
        """Object-level permission.
        - SAFE_METHODS (GET, HEAD, OPTIONS): always allowed
        - other methods (PATCH, PUT, DELETE): only for profile owner
        """
        if request.method in SAFE_METHODS:
            return True

        return getattr(obj, "user", None) == request.user