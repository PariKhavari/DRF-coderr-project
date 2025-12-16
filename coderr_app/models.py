"""[DE] Modelle für Angebote (Offers) der Coderr-Plattform. [EN] Models for offers of the Coderr platform."""

from django.contrib.auth.models import User
from django.db import models
from django.core.validators import MinValueValidator


class Offer(models.Model):
    """[DE] Hauptangebot, das von einem Business-User erstellt wird. [EN] Main offer created by a business user."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="offers")
    title = models.CharField(max_length=255)
    image = models.ImageField(upload_to="offers/", null=True, blank=True)
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """[DE] Meta-Informationen für Offer. [EN] Meta information for Offer."""

        verbose_name = "Offer"
        verbose_name_plural = "Offers"
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        """[DE] String-Repräsentation des Angebots. [EN] String representation of the offer."""
        return self.title

class OfferDetail(models.Model):
    """[DE] Detailvariante eines Angebots (z. B. basic/standard/premium). [EN] Detailed variant of an offer (e.g. basic/standard/premium)."""

    TYPE_BASIC = "basic"
    TYPE_STANDARD = "standard"
    TYPE_PREMIUM = "premium"
    TYPE_CHOICES = [(TYPE_BASIC, "Basic"), (TYPE_STANDARD, "Standard"), (TYPE_PREMIUM, "Premium")]

    offer = models.ForeignKey(Offer, on_delete=models.CASCADE, related_name="details")
    title = models.CharField(max_length=255)
    revisions = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    delivery_time_in_days = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    features = models.JSONField(default=list, blank=True)
    offer_type = models.CharField(max_length=20, choices=TYPE_CHOICES)

    class Meta:
        """[DE] Meta-Informationen für OfferDetail. [EN] Meta information for OfferDetail."""

        verbose_name = "Offer Detail"
        verbose_name_plural = "Offer Details"
        ordering = ["price"]

    def __str__(self) -> str:
        """[DE] String-Repräsentation des Angebotsdetails. [EN] String representation of the offer detail."""
        return f"{self.offer.title} - {self.title}"
    
    
class Order(models.Model):
    """[DE] Bestellung, die aus einem OfferDetail erstellt wird. [EN] Order created from an offer detail."""

    STATUS_IN_PROGRESS = "in_progress"
    STATUS_COMPLETED = "completed"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_IN_PROGRESS, "In progress"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    customer_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="customer_orders")
    business_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="business_orders")
    title = models.CharField(max_length=255)
    revisions = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    delivery_time_in_days = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    features = models.JSONField(default=list, blank=True)
    offer_type = models.CharField(max_length=20, choices=OfferDetail.TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_IN_PROGRESS)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """[DE] Meta-Informationen für Order. [EN] Meta information for Order."""

        verbose_name = "Order"
        verbose_name_plural = "Orders"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        """[DE] String-Repräsentation der Bestellung. [EN] String representation of the order."""
        return f"Order #{self.pk} - {self.title}"
