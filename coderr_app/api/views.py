from django.db.models import Min, Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, viewsets, status
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from django.contrib.auth.models import User
from rest_framework.response import Response
from rest_framework.views import APIView

from coderr_app.models import Offer, OfferDetail, Order, Review
from coderr_app.api.permissions import IsBusinessUser, IsOfferOwner, IsCustomerUser, IsOrderBusinessUser
from coderr_app.api.permissions import IsReviewOwner
from coderr_app.api.serializers import ReviewSerializer
from rest_framework.exceptions import NotAuthenticated, PermissionDenied
from coderr_app.api.serializers import (
    OfferDetailOfferSerializer,
    OfferDetailSerializer,
    OfferListSerializer,
    OfferWriteSerializer,
    OrderSerializer,
    OrderCreateSerializer,
    ReviewSerializer,
)

from rest_framework.pagination import PageNumberPagination


class OfferPagination(PageNumberPagination):
    """Pagination for offers with page_size parameter."""

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100

class OfferViewSet(viewsets.ModelViewSet):
    """ViewSet for CRUD operations on offers."""

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
        """Chooses serializer depending on the action."""
        if self.action == "list":
            return OfferListSerializer
        if self.action == "retrieve":
            return OfferDetailOfferSerializer
        return OfferWriteSerializer

    def get_queryset(self):
        """Builds queryset with filters and ordering."""
        queryset = Offer.objects.all().select_related("user").prefetch_related("details")
        queryset = queryset.annotate(min_price=Min("details__price"), min_delivery_time=Min("details__delivery_time_in_days"))
        queryset = self._apply_filters(queryset)
        return self._apply_ordering(queryset)

    def _apply_filters(self, queryset):
        """Applies filters from query parameters."""
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
        """Applies ordering to the queryset."""
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


class OrderViewSet(viewsets.ModelViewSet):
    """ViewSet for orders."""

    queryset = Order.objects.all().select_related("customer_user", "business_user")
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_permissions(self):
        """Sets permissions depending on the action.
        """
        if self.action == "create":
            permission_classes = [IsAuthenticated, IsCustomerUser]
        elif self.action == "partial_update":
            permission_classes = [IsAuthenticated, IsOrderBusinessUser]
        elif self.action == "destroy":
            permission_classes = [IsAuthenticated, IsAdminUser]
        else:
            permission_classes = [IsAuthenticated]
        return [perm() for perm in permission_classes]

    def get_serializer_class(self):
        """Chooses serializer depending on the action.
        """
        if self.action == "create":
            return OrderCreateSerializer
        return OrderSerializer

    def get_queryset(self):
        """Returns orders for the current user.
        - For destroy (DELETE) and staff: all orders.
        - For all others: only orders where the user is customer or business user.
        """
        user = self.request.user
        if not user or not user.is_authenticated:
            return Order.objects.none()

        base_qs = Order.objects.select_related("customer_user", "business_user")

        if self.action == "destroy" and user.is_staff:
            return base_qs

        return base_qs.filter(Q(customer_user=user) | Q(business_user=user))

    def create(self, request, *args, **kwargs):
        """Creates an order from an offer detail.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        offer_detail_id = serializer.validated_data["offer_detail_id"]

        try:
            offer_detail = OfferDetail.objects.select_related("offer__user").get(id=offer_detail_id)
        except OfferDetail.DoesNotExist:
            return Response({"detail": "Offer detail not found."}, status=status.HTTP_404_NOT_FOUND)

        customer_user = request.user
        business_user = offer_detail.offer.user

        order = Order.objects.create(
            customer_user=customer_user,
            business_user=business_user,
            title=offer_detail.title,
            revisions=offer_detail.revisions,
            delivery_time_in_days=offer_detail.delivery_time_in_days,
            price=offer_detail.price,
            features=offer_detail.features,
            offer_type=offer_detail.offer_type,
        )

        response_serializer = OrderCreateSerializer(order, context={"request": request})
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        """Updates only the status of an order.
        """
        order = self.get_object()
        new_status = request.data.get("status")
        allowed_status = {Order.STATUS_IN_PROGRESS, Order.STATUS_COMPLETED, Order.STATUS_CANCELLED}
        if new_status not in allowed_status:
            return Response({"detail": "Invalid status value."}, status=status.HTTP_400_BAD_REQUEST)

        order.status = new_status
        order.save()
        data = OrderSerializer(order).data
        return Response(data, status=status.HTTP_200_OK)
    

    def destroy(self, request, *args, **kwargs):
        """Deletes an order.
        - 204: Order successfully deleted, no content.
        """
        order = self.get_object()
        order.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class OrderCountView(APIView):
    """Count of in-progress orders for a business user."""

    permission_classes = [IsAuthenticated]

    def get(self, request, business_user_id: int):
        """Returns order_count for status in_progress."""
        business_user = get_object_or_404(User, pk=business_user_id)
        profile = getattr(business_user, "profile", None)
        if not profile or profile.type != "business":
            return Response({"detail": "Business user not found."}, status=status.HTTP_404_NOT_FOUND)
        count = Order.objects.filter(business_user_id=business_user_id, status=Order.STATUS_IN_PROGRESS).count()
        return Response({"order_count": count}, status=status.HTTP_200_OK)

class CompletedOrderCountView(APIView):
    """Count of completed orders for a business user."""

    permission_classes = [IsAuthenticated]

    def get(self, request, business_user_id: int):
        """Returns completed_order_count for status completed."""
        business_user = get_object_or_404(User, pk=business_user_id)
        profile = getattr(business_user, "profile", None)

        if not profile or profile.type != "business":
            return Response({"detail": "Business user not found."}, status=status.HTTP_404_NOT_FOUND)
        count = Order.objects.filter(business_user_id=business_user_id, status=Order.STATUS_COMPLETED).count()
        return Response({"completed_order_count": count}, status=status.HTTP_200_OK)


class ReviewViewSet(viewsets.ModelViewSet):
    """ViewSet for reviews. """

    queryset = Review.objects.all().select_related("business_user", "reviewer")
    serializer_class = ReviewSerializer
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """Sets permissions depending on the action."""

        if self.action in ["partial_update", "destroy"]:
            return [IsAuthenticated(), IsReviewOwner()]
        return [IsAuthenticated()]

    def get_queryset(self):
        """Filters reviews based on query parameters."""

        queryset = Review.objects.all().select_related("business_user", "reviewer")
        params = self.request.query_params
        business_user_id = params.get("business_user_id")
        reviewer_id = params.get("reviewer_id")
        if business_user_id:
            queryset = queryset.filter(business_user_id=business_user_id)
        if reviewer_id:
            queryset = queryset.filter(reviewer_id=reviewer_id)
        return self._apply_ordering(queryset)

    def _apply_ordering(self, queryset):
        """Orders by updated_at or rating."""

        ordering = self.request.query_params.get("ordering")
        allowed = ["updated_at", "-updated_at", "rating", "-rating"]
        if ordering in allowed:
            return queryset.order_by(ordering)
        return queryset

    def _ensure_customer_profile(self, request) -> None:
        """Ensures that the user has a customer profile."""

        user = request.user
        if not user or not user.is_authenticated:
            raise NotAuthenticated()
        profile = getattr(user, "profile", None)
        if not profile or profile.type != "customer":
            raise NotAuthenticated("User must have a customer profile.")

    def create(self, request, *args, **kwargs):
        """Creates a review with proper status codes."""

        self._ensure_customer_profile(request)
        business_user_id = request.data.get("business_user")
        if business_user_id is None:
            return Response({"detail": "business_user is required."}, status=status.HTTP_400_BAD_REQUEST)

        if Review.objects.filter(business_user_id=business_user_id, reviewer=request.user).exists():
            raise PermissionDenied("You can only create one review per business user.")

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        review = serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        """Updates rating/description of a review."""

        review = self.get_object()
        data = {"rating": request.data.get("rating"), "description": request.data.get("description")}
        serializer = self.get_serializer(review, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        review = serializer.save()
        return Response(self.get_serializer(review).data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        """Deletes a review (only owner)."""
        
        review = self.get_object()
        review.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
