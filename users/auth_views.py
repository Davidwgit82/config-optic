from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    # Indique explicitement d'utiliser le champ 'phone'
    username_field = "phone"

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Tu peux ajouter des claims personnalisés dans le payload JWT si besoin
        token['first_name'] = user.first_name
        token['phone'] = user.phone
        return token

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer