import phonenumbers
from typing import Optional


def get_e164_number(phone_number: Optional[str]) -> str:
    """Returns the phone number in E164 format

    Args:
        phone_number (Optional[str]): the phone number to be formated to E164

    Returns:
        str: phone number formated in E164 format
    """
    if not phone_number:
        return ""
    if len(phone_number) < 10:
        return phone_number
    parsed = phonenumbers.parse(phone_number, "US")
    return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)