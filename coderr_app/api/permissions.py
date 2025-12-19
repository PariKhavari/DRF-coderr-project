from rest_framework import exceptions
from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsBusinessUser(BasePermission):
    """Allows access only for business users."""

    message = "Only business users can perform this action."

    def has_permission(self, request, view) -> bool:
        """[DE] Prüft, ob der Benutzer ein Business-Profil hat. [EN] Checks whether the user has a business profile."""
        user = request.user
        if not user or not user.is_authenticated:
            raise exceptions.NotAuthenticated()
        profile = getattr(user, "profile", None)
        if not profile or profile.type != "business":
            raise exceptions.PermissionDenied(self.message)
        return True


class IsOfferOwner(BasePermission):
    """Allows changes only for the offer creator."""

    message = "You are not the owner of this offer."

    def has_object_permission(self, request, view, obj) -> bool:
        """Checks whether the user is the owner of the offer."""
        user = request.user
        if not user or not user.is_authenticated:
            raise exceptions.NotAuthenticated()
        if obj.user != user:
            raise exceptions.PermissionDenied(self.message)
        return True


class IsCustomerUser(BasePermission):
    """Allows actions only for customer profiles."""

    message = "Only customer users can perform this action."

    def has_permission(self, request, view) -> bool:
        """[DE] Prüft, ob der Benutzer ein Customer-Profil hat. [EN] Checks whether the user has a customer profile."""
        user = request.user
        if not user or not user.is_authenticated:
            raise exceptions.NotAuthenticated()
        profile = getattr(user, "profile", None)
        if not profile or profile.type != "customer":
            raise exceptions.PermissionDenied(self.message)
        return True


class IsOrderBusinessUser(BasePermission):
    """llows status updates only for the order's business user."""

    message = "You are not allowed to update this order."

    def has_object_permission(self, request, view, obj) -> bool:
        """Checks whether user is the business user of this order."""
        user = request.user
        if not user or not user.is_authenticated:
            raise exceptions.NotAuthenticated()
        profile = getattr(user, "profile", None)
        if not profile or profile.type != "business":
            raise exceptions.PermissionDenied("Only business users can update orders.")
        if obj.business_user != user:
            raise exceptions.PermissionDenied(self.message)
        return True
    

class IsReviewOwnerOrReadOnly(BasePermission):
    """Allows changes only for the review creator."""

    message = "You are not allowed to modify this review."

    def has_object_permission(self, request, view, obj) -> bool:
        """Checks whether the user is the reviewer."""

        if request.method in SAFE_METHODS:
            return True

        return getattr(obj, "reviewer", None) == request.user
