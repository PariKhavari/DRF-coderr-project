from django.contrib import admin
from auth_app.models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "type",
        "location",
        "tel",
        "created_at",
    ]
    list_filter = ["type"]
    search_fields = [
        "user__username",
        "user__email",
        "location",
    ]
