from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from auth_app.models import UserProfile


class RegistrationSerializer(serializers.Serializer):
    """Serializer for user registration."""

    username = serializers.CharField(max_length=150, validators=[UniqueValidator(queryset=User.objects.all())])
    email = serializers.EmailField(validators=[UniqueValidator(queryset=User.objects.all())])
    password = serializers.CharField(write_only=True)
    repeated_password = serializers.CharField(write_only=True)
    type = serializers.ChoiceField(choices=[UserProfile.TYPE_CUSTOMER, UserProfile.TYPE_BUSINESS])

    def validate(self, attrs: dict) -> dict:
        """Validates that the passwords match."""

        if attrs["password"] != attrs["repeated_password"]:
            message = "Passwords do not match."
            raise serializers.ValidationError({"repeated_password": message})
        return attrs

    def create(self, validated_data: dict) -> User:
        """Creates user and related profile."""

        validated_data.pop("repeated_password")
        user = self._create_user(validated_data)
        self._create_profile(user, validated_data["type"])
        return user

    def _create_user(self, data: dict) -> User:
        """Helper method to create the user."""
        return User.objects.create_user(username=data["username"], email=data["email"], password=data["password"])

    def _create_profile(self, user: User, user_type: str) -> None:
        """Helper method to create the UserProfile."""
        UserProfile.objects.create(user=user, type=user_type)


class LoginSerializer(serializers.Serializer):
    """Serializer for user login."""

    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)


class ProfileSerializer(serializers.ModelSerializer):
    """Full serializer for profile detail view."""


    user = serializers.IntegerField(source="user.id", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    first_name = serializers.CharField(source="user.first_name", allow_blank=True, required=False)
    last_name = serializers.CharField(source="user.last_name", allow_blank=True, required=False)
    email = serializers.EmailField(source="user.email", required=False)

    class Meta:
        """Meta configuration for ProfileSerializer."""

        model = UserProfile
        fields = ["user", "username", "first_name", "last_name", "file", "location", "tel", "description", "working_hours", "type", "email", "created_at"]
        read_only_fields = ["username", "type", "created_at"]

    def update(self, instance: UserProfile, validated_data: dict) -> UserProfile:
        """Updates user and profile data."""

        user_data = validated_data.pop("user", {})
        for key, value in user_data.items():
            setattr(instance.user, key, value)
        instance.user.save()
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        return instance


class BusinessProfileListSerializer(serializers.ModelSerializer):
    """Serializer for the business profiles list."""

    user = serializers.IntegerField(source="user.id", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)

    class Meta:
        """Meta for BusinessProfileListSerializer."""

        model = UserProfile
        fields = ["user", "username", "first_name", "last_name", "file", "location", "tel", "description", "working_hours", "type"]
        

class CustomerProfileListSerializer(serializers.ModelSerializer):
    """Serializer for the customer profiles list."""

    user = serializers.IntegerField(source="user.id", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)

    class Meta:
        """Meta for CustomerProfileListSerializer."""

        model = UserProfile
        fields = ["user", "username", "first_name", "last_name", "file", "type" ]
