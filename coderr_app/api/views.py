from django.db.models import Min, Q
from rest_framework import generics
from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated

from coderr_app.models import Offer, OfferDetail
from coderr_app.api.permissions import IsBusinessUser, IsOfferOwner
from coderr_app.api.serializers import (
    OfferDetailOfferSerializer,
    OfferDetailSerializer,
    OfferListSerializer,
    OfferWriteSerializer,
)
from rest_framework.pagination import PageNumberPagination


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
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_permissions(self):
        """[DE] Setzt Permissions abhängig von der Aktion. [EN] Sets permissions depending on the action."""
        if self.action == "list":
            permission_classes = [AllowAny]
        elif self.action == "create":
            permission_classes = [IsBusinessUser]
        elif self.action in ["update","partial_update", "destroy"]:
            permission_classes = [IsAuthenticated, IsOfferOwner]
        elif self.action == "retrieve":
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated]
        return [perm() for perm in permission_classes]

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


class OfferDetailView(generics.RetrieveAPIView):
    """Detail view for a single offer detail."""

    queryset = OfferDetail.objects.all()
    serializer_class = OfferDetailSerializer
    permission_classes = [IsAuthenticated]

