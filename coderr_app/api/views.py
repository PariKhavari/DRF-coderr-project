"""[DE] API-Views für Offers und OfferDetails. [EN] API views for offers and offer details."""

from django.db.models import Min, Q

from rest_framework import status, viewsets, generics
from rest_framework.exceptions import NotAuthenticated, PermissionDenied
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from coderr_app.models import Offer, OfferDetail
from coderr_app.api.serializers import (
    OfferDetailOfferSerializer,
    OfferDetailSerializer,
    OfferListSerializer,
    OfferWriteSerializer,
)


class OfferPagination(PageNumberPagination):
    """[DE] Paginierung für Offers mit page_size-Parameter. [EN] Pagination for offers with page_size parameter."""

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class OfferViewSet(viewsets.ModelViewSet):
    """[DE] ViewSet für CRUD-Operationen auf Offers. [EN] ViewSet for CRUD operations on offers."""

    queryset = Offer.objects.all().select_related("user").prefetch_related("details")
    serializer_class = OfferWriteSerializer
    pagination_class = OfferPagination
    permission_classes = [AllowAny]

    def _ensure_authenticated(self, request) -> None:
        """[DE] Wirft 401, wenn der Benutzer nicht eingeloggt ist. [EN] Raises 401 if the user is not authenticated."""
        user = request.user
        if not user or not user.is_authenticated:
            raise NotAuthenticated()

    def _ensure_business_user(self, request) -> None:
        """[DE] Wirft 403, wenn der Benutzer kein Business-Profil hat. [EN] Raises 403 if user is not a business profile."""
        profile = getattr(request.user, "profile", None)
        if not profile or profile.type != "business":
            raise PermissionDenied("Only business users can perform this action.")

    def _ensure_offer_owner(self, request, offer: Offer) -> None:
        """[DE] Wirft 403, wenn der Benutzer nicht Owner ist. [EN] Raises 403 if user is not the owner."""
        if offer.user != request.user:
            raise PermissionDenied("You are not the owner of this offer.")

    def get_serializer_class(self):
        """[DE] Wählt Serializer je nach Aktion. [EN] Chooses serializer depending on the action."""
        if self.action == "list":
            return OfferListSerializer
        if self.action == "retrieve":
            return OfferDetailOfferSerializer
        return OfferWriteSerializer

    def get_queryset(self):
        """[DE] Baut Queryset mit Filtern und Sortierung. [EN] Builds queryset with filters and ordering."""
        queryset = Offer.objects.all().select_related("user").prefetch_related("details")
        queryset = queryset.annotate(min_price=Min("details__price"), min_delivery_time=Min("details__delivery_time_in_days"))
        queryset = self._apply_filters(queryset)
        return self._apply_ordering(queryset)

    def _apply_filters(self, queryset):
        """[DE] Wendet Filter aus Query-Parametern an. [EN] Applies filters from query parameters."""
        params = self.request.query_params
        creator_id = params.get("creator_id")
        if creator_id:
            queryset = queryset.filter(user_id=creator_id)
        min_price = params.get("min_price")
        if min_price:
            queryset = queryset.filter(min_price__gte=min_price)
        max_delivery = params.get("max_delivery_time")
        if max_delivery:
            queryset = queryset.filter(min_delivery_time__lte=max_delivery)
        search = params.get("search")
        if search:
            queryset = queryset.filter(Q(title__icontains=search) | Q(description__icontains=search))
        return queryset

    def _apply_ordering(self, queryset):
        """[DE] Wendet Sortierung auf das Queryset an. [EN] Applies ordering to the queryset."""
        ordering = self.request.query_params.get("ordering")
        allowed = ["updated_at", "-updated_at", "min_price", "-min_price"]
        if ordering in allowed:
            return queryset.order_by(ordering)
        return queryset

    def retrieve(self, request, *args, **kwargs):
        """[DE] Detailansicht eines Offers, nur für authentifizierte User (401). [EN] Offer detail view, only for authenticated users (401)."""
        self._ensure_authenticated(request)
        return super().retrieve(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """[DE] Erstellen eines Offers, nur Business-User (401/403). [EN] Create offer, only business users (401/403)."""
        self._ensure_authenticated(request)
        self._ensure_business_user(request)
        return super().create(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        """[DE] Aktualisiert ein Offer, nur Owner (401/403). [EN] Partially updates an offer, only owner (401/403)."""
        self._ensure_authenticated(request)
        offer = self.get_object()
        self._ensure_offer_owner(request, offer)
        serializer = self.get_serializer(offer, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """[DE] Löscht ein Offer, nur Owner (401/403). [EN] Deletes an offer, only owner (401/403)."""
        self._ensure_authenticated(request)
        offer = self.get_object()
        self._ensure_offer_owner(request, offer)
        self.perform_destroy(offer)
        return Response(status=status.HTTP_204_NO_CONTENT)


class OfferDetailView(generics.RetrieveAPIView):
    """[DE] Detailansicht für ein OfferDetail. [EN] Detail view for a single offer detail."""

    queryset = OfferDetail.objects.all()
    serializer_class = OfferDetailSerializer
    permission_classes = [AllowAny]

    def retrieve(self, request, *args, **kwargs):
        """Erlaubt Zugriff nur für authentifizierte Benutzer (401). [EN] Allows access only for authenticated users (401)."""
        user = request.user
        if not user or not user.is_authenticated:
            raise NotAuthenticated()
        return super().retrieve(request, *args, **kwargs)



