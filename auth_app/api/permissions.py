from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsProfileOwnerOrReadOnly(BasePermission):
    """Allows edits only for the profile owner."""

    def has_object_permission(self, request, view, obj) -> bool:
        """Checks access to the profile object."""

        if request.method in SAFE_METHODS:
            return True
        return obj.user == request.user
