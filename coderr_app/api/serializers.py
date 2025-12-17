"""[DE] Serializer für Offers und OfferDetails. [EN] Serializers for offers and offer details."""

from django.contrib.auth.models import User

from django.urls import reverse
from django.db.models import Min
from django.db.models import QuerySet
from django.db.models import Q

from rest_framework import serializers

from coderr_app.models import Offer, OfferDetail, Order


class OfferDetailSerializer(serializers.ModelSerializer):
    """[DE] Vollständige Darstellung eines OfferDetail. [EN] Full representation of an offer detail."""

    class Meta:
        """[DE] Meta für OfferDetailSerializer. [EN] Meta for OfferDetailSerializer."""

        model = OfferDetail
        fields = ["id", "title", "revisions",
                  "delivery_time_in_days", "price", "features", "offer_type"]


class OfferWriteSerializer(serializers.ModelSerializer):
    """[DE] Serializer für das Erstellen/Aktualisieren eines Offers inkl. Details. [EN] Serializer for creating/updating an offer including details."""

    details = OfferDetailSerializer(many=True)

    class Meta:
        """[DE] Meta für OfferWriteSerializer. [EN] Meta for OfferWriteSerializer."""

        model = Offer
        fields = ["id", "title", "image", "description", "details"]

    def validate_details(self, value: list) -> list:
        """[DE] Validiert Details: beim Erstellen genau 3, beim Patch beliebige Teilmenge. [EN] Validates details: on create exactly 3, on patch arbitrary subset."""
        # Create-Fall: self.instance ist None
        if self.instance is None:
            if len(value) != 3:
                raise serializers.ValidationError(
                    "An offer must contain exactly three details.")
            types = {item.get("offer_type") for item in value}
            required = {OfferDetail.TYPE_BASIC,
                        OfferDetail.TYPE_STANDARD, OfferDetail.TYPE_PREMIUM}
            if types != required:
                raise serializers.ValidationError(
                    "Details must include basic, standard and premium types.")
            return value

        # Update/PATCH-Fall: self.instance ist gesetzt
        if len(value) == 0:
            raise serializers.ValidationError(
                "At least one detail must be provided for update.")
        for item in value:
            if not item.get("offer_type"):
                raise serializers.ValidationError(
                    "Each detail must include offer_type for update.")
        return value

    def create(self, validated_data: dict) -> Offer:
        """[DE] Erstellt Offer und seine Details. [EN] Creates an offer and its details."""
        details_data = validated_data.pop("details")
        user = self._get_user()
        offer = Offer.objects.create(user=user, **validated_data)
        self._create_details(offer, details_data)
        return offer

    def update(self, instance: Offer, validated_data: dict) -> Offer:
        """[DE] Aktualisiert Offer und ggf. Details (Teilupdate möglich). [EN] Updates offer and optionally its details (partial update)."""
        details_data = validated_data.pop("details", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if details_data is not None:
            self._update_details(instance, details_data)
        return instance

    def _get_user(self) -> User:
        """[DE] Holt den aktuellen Benutzer aus dem Kontext. [EN] Gets the current user from context."""
        request = self.context.get("request")
        return request.user

    def _create_details(self, offer: Offer, details_data: list) -> None:
        """[DE] Legt die OfferDetails für ein Offer an. [EN] Creates offer details for an offer."""
        for detail_data in details_data:
            OfferDetail.objects.create(offer=offer, **detail_data)

    def _update_details(self, offer: Offer, details_data: list) -> None:
        """[DE] Aktualisiert bestehende OfferDetails anhand ihres Typs (IDs bleiben gleich). [EN] Updates existing offer details by type (IDs stay the same)."""
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
        """[DE] Gibt Offer mit allen Details zurück, egal ob Teilupdate. [EN] Returns offer with all details, regardless of partial update."""
        data = super().to_representation(instance)
        data["details"] = OfferDetailSerializer(
            instance.details.all(), many=True).data
        return data


class OfferListSerializer(serializers.ModelSerializer):
    """[DE] Serializer für die Offers-Liste. [EN] Serializer for the offers list."""

    user = serializers.IntegerField(source="user.id", read_only=True)
    details = serializers.SerializerMethodField()
    min_price = serializers.SerializerMethodField()
    min_delivery_time = serializers.SerializerMethodField()
    user_details = serializers.SerializerMethodField()

    class Meta:
        """[DE] Meta für OfferListSerializer. [EN] Meta for OfferListSerializer."""

        model = Offer
        fields = ["id", "user", "title", "image", "description", "created_at",
                  "updated_at", "details", "min_price", "min_delivery_time", "user_details"]

    def get_details(self, obj: Offer) -> list:
        """[DE] Baut Link-Liste zu OfferDetails. [EN] Builds link list to offer details."""
        request = self.context.get("request")
        results = []
        for detail in obj.details.all():
            url = reverse("offer-detail-item", args=[detail.id])
            if request is not None:
                url = request.build_absolute_uri(url)
            results.append({"id": detail.id, "url": url})
        return results

    def get_min_price(self, obj: Offer):
        """[DE] Liefert minimalen Preis der Details. [EN] Returns minimal price of details."""
        return obj.details.aggregate(value=Min("price"))["value"]

    def get_min_delivery_time(self, obj: Offer):
        """[DE] Liefert minimale Lieferzeit der Details. [EN] Returns minimal delivery time of details."""
        return obj.details.aggregate(value=Min("delivery_time_in_days"))["value"]

    def get_user_details(self, obj: Offer) -> dict:
        """[DE] Liefert Basisdaten des Erstellers. [EN] Returns basic data of the creator."""
        user = obj.user
        return {"first_name": user.first_name, "last_name": user.last_name, "username": user.username}


class OfferDetailOfferSerializer(serializers.ModelSerializer):
    """[DE] Serializer für Offer-Detailsicht. [EN] Serializer for single-offer detail view."""

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
        """[DE] Minimaler Detailpreis. [EN] Minimal detail price."""
        return obj.details.aggregate(value=Min("price"))["value"]

    def get_min_delivery_time(self, obj: Offer):
        """[DE] Minimale Lieferzeit. [EN] Minimal delivery time."""
        return obj.details.aggregate(value=Min("delivery_time_in_days"))["value"]


class OrderSerializer(serializers.ModelSerializer):
    """[DE] Serializer für die Darstellung einer Bestellung. [EN] Serializer for representing an order."""

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
    """[DE] Serializer für das Erstellen einer Bestellung via offer_detail_id.
    [EN] Serializer for creating an order via offer_detail_id.
    """

    offer_detail_id = serializers.IntegerField()

    def to_representation(self, instance: Order) -> dict:
        """[DE] Antwort ohne updated_at-Feld für POST.
        [EN] Response without updated_at field for POST.
        """
        data = OrderSerializer(instance).data
        data.pop("updated_at", None)
        return data
