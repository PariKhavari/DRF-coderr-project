from django.contrib import admin
from coderr_app.models import Offer, OfferDetail, Order, Review

class OfferDetailInline(admin.TabularInline):
    """Inline view for OfferDetail inside the Offer admin.
    """
    model = OfferDetail
    extra = 0
    readonly_fields = ["offer_type"]


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    """Admin view for Offer."""

    list_display = ["id", "title", "user", "created_at", "updated_at"]
    search_fields = ["title", "description", "user__username"]
    list_filter = ["created_at", "updated_at"]
    readonly_fields = ["created_at", "updated_at"]
    inlines = [OfferDetailInline]


@admin.register(OfferDetail)
class OfferDetailAdmin(admin.ModelAdmin):
    """Admin view for OfferDetail."""

    list_display = ["id", "offer", "title", "price", "delivery_time_in_days", "offer_type"]
    search_fields = ["title", "offer__title"]
    list_filter = ["offer_type", "delivery_time_in_days"]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Admin configuration for orders.
    """

    list_display = [
        "id",
        "title",
        "customer_user",
        "business_user",
        "status",
        "price",
        "created_at",
        "updated_at",
    ]
    list_filter = ["status", "created_at", "updated_at"]
    search_fields = [
        "title",
        "customer_user__username",
        "business_user__username",
    ]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """Admin configuration for reviews.
    """

    list_display = [
        "id",
        "business_user",
        "reviewer",
        "rating",
        "created_at",
        "updated_at",
    ]
    list_filter = ["rating", "created_at", "updated_at"]
    search_fields = [
        "business_user__username",
        "reviewer__username",
        "description",
    ]
    readonly_fields = ["created_at", "updated_at"]