from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=True, style={
            'input_type': 'password'
        },
        min_length=8
    )

    class Meta:
        model = User
        fields = (
            'first_name',
            'last_name',
            'email',
            'phone',
            'country',
            'password'
        )

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)  


""" profile user """
class UserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="get_full_name", read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'phone', 'first_name', 
            'last_name', 'full_name', 'email', 
            'country', 'longitude', 'latitude', 'created_at'
        )

        read_only_fields = ("id", "phone", "created_at")

    def validate_latitude(self, value):
        if value is not None and not (-90 <= value <= 90):
            raise serializers.ValidationError("Latitude invalide.")
        return value

    def validate_longitude(self, value):
        if value is not None and not (-180 <= value <= 180):
            raise serializers.ValidationError("Longitude invalide.")
        return value
    

""" list des users """
class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User

        fields = ['id', 'first_name', 'last_name', 'phone', 'email', 'country', 'longitude', 'latitude', 'is_staff', 'is_active']