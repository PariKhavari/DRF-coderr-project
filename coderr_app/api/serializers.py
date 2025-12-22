from django.contrib.auth.models import User
from django.urls import reverse
from django.db.models import Min
from rest_framework import serializers
from coderr_app.models import Offer, OfferDetail, Order, Review
from auth_app.models import UserProfile


class OfferDetailSerializer(serializers.ModelSerializer):
    """Full representation of an offer detail."""

    class Meta:
        """Meta for OfferDetailSerializer."""

        model = OfferDetail
        fields = ["id", "title", "revisions",
                  "delivery_time_in_days", "price", "features", "offer_type"]

class OfferWriteSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating an offer including details."""

    details = OfferDetailSerializer(many=True)

    class Meta:
        """Meta for OfferWriteSerializer."""

        model = Offer
        fields = ["id", "title", "image", "description", "details"]

    def validate_details(self, value: list) -> list:
        """Validates details: on create exactly 3, on patch arbitrary subset."""
      
        if self.instance is None:
            if len(value) != 3:
                raise serializers.ValidationError(
                    "An offer must contain exactly three details.")
            types = {item.get("offer_type") for item in value}
            required = {OfferDetail.TYPE_BASIC,OfferDetail.TYPE_STANDARD, OfferDetail.TYPE_PREMIUM}
            if types != required:
                raise serializers.ValidationError(
                    "Details must include basic, standard and premium types.")
            return value

        if len(value) == 0:
            raise serializers.ValidationError(
                "At least one detail must be provided for update.")
        for item in value:
            if not item.get("offer_type"):
                raise serializers.ValidationError(
                    "Each detail must include offer_type for update.")
        return value

    def create(self, validated_data: dict) -> Offer:
        """Creates an offer and its details."""

        details_data = validated_data.pop("details")
        user = self._get_user()
        offer = Offer.objects.create(user=user, **validated_data)
        self._create_details(offer, details_data)
        return offer

    def update(self, instance: Offer, validated_data: dict) -> Offer:
        """Updates offer and optionally its details (partial update)."""

        details_data = validated_data.pop("details", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if details_data is not None:
            self._update_details(instance, details_data)
        return instance

    def _get_user(self) -> User:
        """Gets the current user from context."""

        request = self.context.get("request")
        return request.user

    def _create_details(self, offer: Offer, details_data: list) -> None:
        """Creates offer details for an offer."""

        for detail_data in details_data:
            OfferDetail.objects.create(offer=offer, **detail_data)

    def _update_details(self, offer: Offer, details_data: list) -> None:
        """Updates existing offer details by type (IDs stay the same)."""

        for detail_data in details_data:
            offer_type = detail_data.get("offer_type")
            if offer_type is None:
                raise serializers.ValidationError(
                    {"offer_type": "offer_type is required."})
            try:
                detail = offer.details.get(offer_type=offer_type)
            except OfferDetail.DoesNotExist:
                raise serializers.ValidationError(
                    {"detail": f"No detail with offer_type '{offer_type}' exists."})
            for field in ["title", "revisions", "delivery_time_in_days", "price", "features"]:
                if field in detail_data:
                    setattr(detail, field, detail_data[field])
            detail.save()

    def to_representation(self, instance: Offer) -> dict:
        """Returns offer with all details, regardless of partial update."""

        data = super().to_representation(instance)
        data["details"] = OfferDetailSerializer(
            instance.details.all(), many=True).data
        return data

class OfferListSerializer(serializers.ModelSerializer):
    """Serializer for the offers list."""

    user = serializers.IntegerField(source="user.id", read_only=True)
    details = serializers.SerializerMethodField()
    min_price = serializers.SerializerMethodField()
    min_delivery_time = serializers.SerializerMethodField()
    user_details = serializers.SerializerMethodField()

    class Meta:
        """Meta for OfferListSerializer."""

        model = Offer
        fields = ["id", "user", "title", "image", "description", "created_at",
                  "updated_at", "details", "min_price", "min_delivery_time", "user_details"]

    def get_details(self, obj: Offer) -> list:
        """Builds link list to offer details."""

        request = self.context.get("request")
        results = []
        for detail in obj.details.all():
            url = reverse("offer-detail-item", args=[detail.id])
            if request is not None:
                url = request.build_absolute_uri(url)
            results.append({"id": detail.id, "url": url})
        return results

    def get_min_price(self, obj: Offer):
        """Returns minimal price of details."""
        return obj.details.aggregate(value=Min("price"))["value"]

    def get_min_delivery_time(self, obj: Offer):
        """Returns minimal delivery time of details."""
        return obj.details.aggregate(value=Min("delivery_time_in_days"))["value"]

    def get_user_details(self, obj: Offer) -> dict:
        """Returns basic data of the creator."""
        user = obj.user
        return {"first_name": user.first_name, "last_name": user.last_name, "username": user.username}

class OfferDetailOfferSerializer(serializers.ModelSerializer):
    """Serializer for single-offer detail view."""

    user = serializers.IntegerField(source="user.id", read_only=True)
    details = serializers.SerializerMethodField()
    min_price = serializers.SerializerMethodField()
    min_delivery_time = serializers.SerializerMethodField()

    class Meta:
        """[DE] Meta für OfferDetailOfferSerializer. [EN] Meta for OfferDetailOfferSerializer."""

        model = Offer
        fields = ["id", "user", "title", "image", "description", "created_at",
                  "updated_at", "details", "min_price", "min_delivery_time"]

    def get_details(self, obj: Offer) -> list:
        """[DE] Baut Link-Liste für Details. [EN] Builds link list for details."""
        request = self.context.get("request")
        results = []
        for detail in obj.details.all():
            url = reverse("offer-detail-item", args=[detail.id])
            if request is not None:
                url = request.build_absolute_uri(url)
            results.append({"id": detail.id, "url": url})
        return results

    def get_min_price(self, obj: Offer):
        """Minimal detail price."""
        return obj.details.aggregate(value=Min("price"))["value"]

    def get_min_delivery_time(self, obj: Offer):
        """Minimal delivery time."""
        return obj.details.aggregate(value=Min("delivery_time_in_days"))["value"]



class OrderSerializer(serializers.ModelSerializer):
    """Serializer for representing an order."""

    customer_user = serializers.IntegerField(
        source="customer_user.id", read_only=True)
    business_user = serializers.IntegerField(
        source="business_user.id", read_only=True)

    class Meta:
        model = Order
        fields = ["id", "customer_user", "business_user", "title", "revisions", "delivery_time_in_days",
                  "price", "features", "offer_type", "status", "created_at", "updated_at"]
        read_only_fields = ["id", "customer_user", "business_user", "title", "revisions",
                "delivery_time_in_days", "price", "features", "offer_type", "created_at", "updated_at"]

class OrderCreateSerializer(serializers.Serializer):
    """Serializer for creating an order via offer_detail_id.
    """

    offer_detail_id = serializers.IntegerField()

    def to_representation(self, instance: Order) -> dict:
        """Response without updated_at field for POST.
        """
        data = OrderSerializer(instance).data
        data.pop("updated_at", None)
        return data


class ReviewSerializer(serializers.ModelSerializer):
    """Serializer for representing a review.
    """

    business_user = serializers.IntegerField(
        source="business_user.id",
        read_only=True,
    )
    reviewer = serializers.IntegerField(
        source="reviewer.id",
        read_only=True,
    )

    class Meta:
        model = Review
        fields = [
            "id",
            "business_user",
            "reviewer",
            "rating",
            "description",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "business_user",
            "reviewer",
            "created_at",
            "updated_at",
        ]


class ReviewCreateSerializer(serializers.Serializer):
    """Serializer for creating a review.
    """

    business_user = serializers.IntegerField()
    rating = serializers.IntegerField(min_value=1, max_value=5)
    description = serializers.CharField(allow_blank=True)

    def validate_business_user(self, value: int) -> int:
        """Checks if the business user exists and has a business profile.
        """
        user = User.objects.filter(id=value).first()
        if user is None:
            raise serializers.ValidationError(
                "The specified business user does not exist."
            )

        profile = UserProfile.objects.filter(user=user).first()
        if profile is None or profile.type != "business":
            raise serializers.ValidationError(
                "The specified user does not have a business profile."
            )

        return value

    def validate(self, attrs: dict) -> dict:
        """Validates:
        - the logged-in user has a customer profile
        - there is no existing review from this customer for this business user
        """
        request = self.context.get("request")
        user = getattr(request, "user", None)

        if user is None or not user.is_authenticated:
            raise serializers.ValidationError(
                "You must be authenticated to create a review."
            )

        profile = UserProfile.objects.filter(user=user).first()
        if profile is None or profile.type != "customer":
            raise serializers.ValidationError(
                "Only users with a customer profile can create reviews."
            )

        return attrs

    def create(self, validated_data: dict) -> Review:
        """Creates the review instance.
        """
        request = self.context["request"]
        reviewer = request.user
        business_user = User.objects.get(id=validated_data["business_user"])

        return Review.objects.create(
            business_user=business_user,
            reviewer=reviewer,
            rating=validated_data["rating"],
            description=validated_data.get("description", ""),
                )
        return review

    def to_representation(self, instance: Review) -> dict:
        """Always use the normal ReviewSerializer for the response representation.
        """
        return ReviewSerializer(instance).data
