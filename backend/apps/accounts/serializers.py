from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.accounts.models import CustomerProfile, Property
from apps.tickets.permissions import role_of

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    departments = serializers.SerializerMethodField()
    is_available = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "username", "email", "first_name", "last_name",
            "name", "role", "departments", "is_available",
        ]

    def get_role(self, user):
        return role_of(user)

    def get_name(self, user):
        return user.get_full_name() or user.get_username()

    def get_departments(self, user):
        profile = getattr(user, "staff_profile", None)
        return list(profile.departments.values_list("id", flat=True)) if profile else []

    def get_is_available(self, user):
        profile = getattr(user, "staff_profile", None)
        return profile.is_available if profile else None


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, validators=[validate_password])
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)
    company_name = serializers.CharField(required=False, allow_blank=True)

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("That username is already taken.")
        return value

    def create(self, data):
        user = User.objects.create_user(
            username=data["username"],
            email=data["email"],
            password=data["password"],
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name", ""),
        )
        group, _ = Group.objects.get_or_create(name="customers")
        user.groups.add(group)
        CustomerProfile.objects.create(
            user=user,
            phone=data.get("phone", ""),
            company_name=data.get("company_name", ""),
        )
        return user


class LoginSerializer(TokenObtainPairSerializer):
    """JWT login that also returns the resolved user (role-aware) for the SPA."""

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data


class PropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        fields = [
            "id", "label", "property_type", "address_line", "community",
            "city", "emirate", "unit_number", "access_notes", "is_active",
        ]
