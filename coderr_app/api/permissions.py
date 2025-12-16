"""[DE] Permissions für Offers. [EN] Permissions for offers."""

from rest_framework import exceptions
from rest_framework.permissions import BasePermission


class IsAuthenticated401(BasePermission):
    """[DE] Wie IsAuthenticated, aber mit HTTP 401 bei fehlendem Login. [EN] Like IsAuthenticated, but returns HTTP 401 when not logged in."""

    def has_permission(self, request, view) -> bool:
        """[DE] Löst 401 aus, wenn der Benutzer nicht eingeloggt ist. [EN] Raises 401 if the user is not authenticated."""
        user = request.user
        if not user or not user.is_authenticated:
            raise exceptions.NotAuthenticated()
        return True


class IsBusinessUser(BasePermission):
    """[DE] Erlaubt Zugriff nur für Business-User. [EN] Allows access only for business users."""

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
    """[DE] Erlaubt Änderungen nur für den Ersteller des Offers. [EN] Allows changes only for the offer creator."""

    message = "You are not the owner of this offer."

    def has_object_permission(self, request, view, obj) -> bool:
        """[DE] Prüft, ob der Benutzer der Owner des Angebots ist. [EN] Checks whether the user is the owner of the offer."""
        user = request.user
        if not user or not user.is_authenticated:
            raise exceptions.NotAuthenticated()
        if obj.user != user:
            raise exceptions.PermissionDenied(self.message)
        return True
