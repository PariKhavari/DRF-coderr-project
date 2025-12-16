"""[DE] Admin-Konfiguration für Offers. [EN] Admin configuration for offers."""

from django.contrib import admin
from coderr_app.models import Offer, OfferDetail


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    """[DE] Admin-Ansicht für Offer. [EN] Admin view for Offer."""

    list_display = ["id", "title", "user", "created_at", "updated_at"]
    search_fields = ["title", "description", "user__username"]
    list_filter = ["created_at", "updated_at"]


@admin.register(OfferDetail)
class OfferDetailAdmin(admin.ModelAdmin):
    """[DE] Admin-Ansicht für OfferDetail. [EN] Admin view for OfferDetail."""

    list_display = ["id", "offer", "title", "price", "delivery_time_in_days", "offer_type"]
    search_fields = ["title", "offer__title"]
    list_filter = ["offer_type"]
