from django.urls import include, path
from rest_framework.routers import DefaultRouter
from coderr_app.api.views import OfferDetailView, OfferViewSet, OrderViewSet, OrderCountView, CompletedOrderCountView,ReviewViewSet, BaseInfoView


router = DefaultRouter()
router.register("offers", OfferViewSet, basename="offer")
router.register("orders", OrderViewSet, basename="order")
router.register("reviews", ReviewViewSet, basename="review")


urlpatterns = [
    path("", include(router.urls)),
    path("offerdetails/<int:pk>/", OfferDetailView.as_view(), name="offer-detail-item"),
    path("order-count/<int:business_user_id>/", OrderCountView.as_view(), name="order-count"),
    path("completed-order-count/<int:business_user_id>/", CompletedOrderCountView.as_view(), name="completed-order-count"),
    path("base-info/", BaseInfoView.as_view(), name="base-info"),
    
]


