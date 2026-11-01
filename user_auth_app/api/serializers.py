from django.contrib.auth import authenticate
from rest_framework import serializers

from user_auth_app.models import User


class RegistrationSerializer(serializers.ModelSerializer):
    """Validate registration data and create a new user."""

    password = serializers.CharField(write_only=True)
    confirmed_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username",  "password", "confirmed_password","email"]

        extra_kwargs = {
            "email": {"required": True, "allow_blank": False},
        }

    def validate_email(self, value):
        """Ensure the email is not already used (case insensitive)."""

        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Email already exists")

        return value

    def validate(self, data):
        """Ensure that password and confirmed_password match."""

        if data["password"] != data["confirmed_password"]:
            raise serializers.ValidationError(
                {"confirmed_password": "Passwords do not match"}
            )

        return data

    def create(self, validated_data):
        """Create the user with a hashed password."""

        validated_data.pop("confirmed_password")

        user = User.objects.create_user(**validated_data)

        return user
    
    
    
class UserLoginSerializer(serializers.Serializer):
    """Validate login credentials."""

    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        """Authenticate the user and add it to the validated data as "user"."""
        username = data.get("username")
        password = data.get("password")

        user = authenticate(username=username, password=password)

        if user is None:
            raise serializers.ValidationError("Invalid username or password")

        data["user"] = user
        return data