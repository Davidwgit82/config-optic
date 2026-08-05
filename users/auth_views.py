from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from utils.validators import normalize_ivorian_phone


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = "phone"

    def validate(self, attrs):
        # Normalise le téléphone AVANT que la classe parente ne fasse authenticate()
        if "phone" in attrs:
            attrs["phone"] = normalize_ivorian_phone(attrs["phone"])
        return super().validate(attrs)

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['first_name'] = user.first_name
        token['phone'] = user.phone
        return token


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer