from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.http import Http404
from django.shortcuts import get_object_or_404

from rest_framework import generics, status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.models import UserProfile

from .permissions import IsProfileOwnerOrReadOnly
from .serializers import (
    BusinessProfileListSerializer,
    CustomerProfileListSerializer,
    LoginSerializer,
    ProfileSerializer,
    RegistrationSerializer,
)

class RegistrationView(APIView):
    """Endpoint for user registration."""

    permission_classes = [AllowAny]

    def post(self, request):
        """Creates a new user and token."""

        serializer = RegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        data = {"token": token.key, "username": user.username, "email": user.email, "user_id": user.id}
        return Response(data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """Endpoint for user login."""

    permission_classes = [AllowAny]

    def post(self, request):
        """Authenticates a user and returns a token."""

        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        username = serializer.validated_data["username"]
        password = serializer.validated_data["password"]
        user = authenticate(username=username, password=password)
        if user is None:
            return Response({"detail": "Invalid credentials."}, status=status.HTTP_400_BAD_REQUEST)
        token, _ = Token.objects.get_or_create(user=user)
        data = {"token": token.key, "username": user.username, "email": user.email, "user_id": user.id}
        return Response(data, status=status.HTTP_200_OK)


class ProfileDetailView(generics.RetrieveUpdateAPIView):
    """Detail and update view for a profile."""

    queryset = UserProfile.objects.select_related("user")
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated,IsProfileOwnerOrReadOnly]

    def get_object(self):
        """ Retrieves the profile or raises 404 if not found."""
        user_id = self.kwargs["pk"]
        user = get_object_or_404(User, pk=user_id)
        try:
            return user.profile
        except UserProfile.DoesNotExist:
            raise Http404("User profile not found.")

class BusinessProfileListView(generics.ListAPIView):
    """List of all business profiles."""

    serializer_class = BusinessProfileListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filters profiles with type 'business'."""

        return UserProfile.objects.filter(type=UserProfile.TYPE_BUSINESS).select_related("user")


class CustomerProfileListView(generics.ListAPIView):
    """List of all customer profiles."""

    serializer_class = CustomerProfileListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filters profiles with type 'customer'."""
        return UserProfile.objects.filter(type=UserProfile.TYPE_CUSTOMER).select_related("user")


