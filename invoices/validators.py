import re

from django.core.exceptions import ValidationError


def normalize_whatsapp_number(value):
    """Normalize an international phone number without guessing a country."""
    if not value.strip():
        return ""
    number = re.sub(r"[\s().-]", "", value)
    if number.startswith("00"):
        number = "+" + number[2:]
    if not re.fullmatch(r"\+[1-9][0-9]{6,14}", number):
        raise ValidationError(
            "Bitte eine internationale Telefonnummer mit Ländervorwahl eingeben, "
            "zum Beispiel +49 151 23456789."
        )
    return number
