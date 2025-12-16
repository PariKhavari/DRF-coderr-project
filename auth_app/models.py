from django.contrib.auth.models import User
from django.db import models


class UserProfile(models.Model):
    TYPE_CUSTOMER = "customer"
    TYPE_BUSINESS = "business"

    TYPE_CHOICES = [
        (TYPE_CUSTOMER, "Customer"),
        (TYPE_BUSINESS, "Business"),
    ]

    user = models.OneToOneField(User,on_delete=models.CASCADE,related_name="profile")
    type = models.CharField(max_length=20,choices=TYPE_CHOICES)
    file = models.CharField(max_length=255,blank=True,default="")
    location = models.CharField(max_length=255,blank=True,default="")
    tel = models.CharField(max_length=50,blank=True,default="")
    description = models.TextField(blank=True,default="")
    working_hours = models.CharField( max_length=100,blank=True,default="")
    created_at = models.DateTimeField(auto_now_add=True)
    uploaded_at= models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"
        ordering = ["user__username"]

    def __str__(self) -> str:
        return f"{self.user.username} ({self.type})"
