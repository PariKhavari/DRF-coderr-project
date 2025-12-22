from django.db.models import Min, Q, Avg
from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from rest_framework import generics, viewsets, status
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from django.contrib.auth.models import User
from rest_framework.response import Response
from rest_framework.views import APIView


from coderr_app.models import Offer, OfferDetail, Order, Review
from coderr_app.api.permissions import IsBusinessUser, IsOfferOwner, IsCustomerUser, IsOrderBusinessUser,IsReviewOwnerOrReadOnly
from coderr_app.api.serializers import ReviewCreateSerializer, ReviewSerializer
from auth_app.models import UserProfile
from rest_framework.exceptions import PermissionDenied
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
        """Sets permissions depending on the action."""
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
        """Returns filtered offers and validates filter types.
        """
        queryset = (Offer.objects.annotate(min_price=Min("details__price"),min_delivery_time=Min("details__delivery_time_in_days"),)
            .select_related("user")
            .prefetch_related("details")
        )

        params = self.request.query_params

        min_price = params.get("min_price")
        if min_price is not None:
            try:
                min_price_value = float(min_price)
            except ValueError:
                raise ValidationError(
                    {
                        "min_price": (
                            "min_price must be a float value."
                        )
                    }
                )
            queryset = queryset.filter(min_price__gte=min_price_value)

        max_delivery_time = params.get("max_delivery_time")
        if max_delivery_time is not None:
            try:
                max_delivery_value = int(max_delivery_time)
            except ValueError:
                raise ValidationError(
                    {
                        "max_delivery_time": (
                            "max_delivery_time must be an integer."
                        )
                    }
                )
            queryset = queryset.filter(min_delivery_time__lte=max_delivery_value)

        creator_id = params.get("creator_id")
        if creator_id is not None:
            queryset = queryset.filter(user_id=creator_id)

        search_query = params.get("search")
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query)
                | Q(description__icontains=search_query)
            )

        ordering = params.get("ordering")
        if ordering in ("updated_at", "-updated_at", "min_price", "-min_price"):
            queryset = queryset.order_by(ordering)

        return queryset

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
        if user.is_staff:
            return Order.objects.select_related("customer_user", "business_user")

        """Normal users: only orders where they are customer OR business user."""
        return Order.objects.select_related("customer_user", "business_user").filter(
            Q(customer_user=user) | Q(business_user=user)
        )
    
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
        order = get_object_or_404(
            Order.objects.select_related("customer_user", "business_user"),
            pk=kwargs.get("pk"),
        )

        user = request.user

        if not user or not user.is_authenticated:
            return Response(
                {"detail": "Authentication credentials were not provided."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if order.business_user != user:
            return Response(
                {
                    "detail": (
                        "Only the business user of this order can update the status."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        new_status = request.data.get("status")
        allowed_status = {
            Order.STATUS_IN_PROGRESS,
            Order.STATUS_COMPLETED,
            Order.STATUS_CANCELLED,
        }

        if new_status not in allowed_status:
            return Response(
                {"detail": "Invalid status value."},
                status=status.HTTP_400_BAD_REQUEST,
            )

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
    """ViewSet for reviews
    """

    queryset = Review.objects.select_related("business_user", "reviewer")
    permission_classes = [IsAuthenticated,IsReviewOwnerOrReadOnly]

    def get_serializer_class(self):
        """Use create serializer for POST, normal serializer otherwise.
        """
        if self.action == "create":
            return ReviewCreateSerializer
        return ReviewSerializer

    def perform_create(self, serializer) -> None:
        """Ensures that a user can only create one review per business profile.
        - If a review already exists → 403 Forbidden.
        - Otherwise the review is created via the serializer.
        """
        user = self.request.user
        business_user_id = serializer.validated_data["business_user"]

        already_exists = Review.objects.filter(
            business_user_id=business_user_id,
            reviewer=user,
        ).exists()

        if already_exists:
            raise PermissionDenied(
                "You can only create one review per business profile."
            )

        serializer.save()

class BaseInfoView(APIView):
    """Returns aggregated base information about the platform.
    """

    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        """Returns statistics about reviews, business profiles and offers.
        """
        review_count = Review.objects.count()
        average = Review.objects.aggregate(value=Avg("rating"))["value"]
        average_rating = round(average, 1) if average is not None else 0.0
        business_profile_count = UserProfile.objects.filter(type="business").count()
        offer_count = Offer.objects.count()

        data = {
            "review_count": review_count,
            "average_rating": average_rating,
            "business_profile_count": business_profile_count,
            "offer_count": offer_count,
        }
        return Response(data)
