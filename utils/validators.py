import re
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible

def normalize_ivorian_phone(value: str) -> str:
    cleaned = re.sub(r'[\s\-\.]', '', value)
    if re.match(r'^(01|05|07|27)\d{8}$', cleaned):
        cleaned = f"+225{cleaned}"
    return cleaned

@deconstructible
@deconstructible
class IvoryCoastPhoneValidator:
    message = "Entrez un numéro de téléphone valide en Côte d'Ivoire (ex: +2250700000000 ou 0700000000)."
    code = "invalid_phone"

    def __call__(self, value):
        cleaned_value = normalize_ivorian_phone(value)
        if not re.match(r'^\+225(01|05|07|27)\d{8}$', cleaned_value):
            raise ValidationError(self.message, code=self.code)
