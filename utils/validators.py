import re
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible

@deconstructible
class IvoryCoastPhoneValidator:
    message = "Entrez un numéro de téléphone valide en Côte d'Ivoire (ex: +2250700000000 ou 0700000000)."
    code = "invalid_phone"

    def __call__(self, value):
        # Nettoyer les espaces et tirets
        cleaned_value = re.sub(r'[\s\-\.]', '', value)
        
        # Si le numéro commence par 01, 05, 07 (mobile CI) ou 27 (fixe CI) et fait 10 chiffres, on ajoute +225
        if re.match(r'^(01|05|07|27)\d{8}$', cleaned_value):
            cleaned_value = f"+225{cleaned_value}"
            
        # Vérification finale du format international ivoirien (+225 suivi de 10 chiffres)
        if not re.match(r'^\+225(01|05|07|27)\d{8}$', cleaned_value):
            raise ValidationError(self.message, code=self.code)
        
        # Vous pouvez réassigner la valeur nettoyée si besoin ou juste valider
        return cleaned_value
