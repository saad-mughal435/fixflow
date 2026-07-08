from rest_framework import generics, permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.accounts.models import Property
from apps.accounts.serializers import (
    LoginSerializer,
    PropertySerializer,
    RegisterSerializer,
    UserSerializer,
)
from apps.tickets.permissions import DemoModeDeleteGuard


class RegisterView(generics.CreateAPIView):
    """Public customer self-registration → returns JWT tokens + the user."""

    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": UserSerializer(user).data,
            },
            status=201,
        )


class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer


class MeView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user).data)


class PropertyViewSet(viewsets.ModelViewSet):
    """A customer's own properties."""

    serializer_class = PropertySerializer
    permission_classes = [permissions.IsAuthenticated, DemoModeDeleteGuard]
    pagination_class = None

    def get_queryset(self):
        return Property.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
