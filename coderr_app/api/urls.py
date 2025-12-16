"""[DE] URL-Routing für Offers und OfferDetails. [EN] URL routing for offers and offer details."""

from django.urls import include, path

from rest_framework.routers import DefaultRouter

from coderr_app.api.views import OfferDetailView, OfferViewSet

router = DefaultRouter()
router.register("offers", OfferViewSet, basename="offer")

urlpatterns = [
    path("", include(router.urls)),
    path("offerdetails/<int:pk>/", OfferDetailView.as_view(), name="offer-detail-item"),
]
