from datetime import datetime, date
from rest_framework.exceptions import PermissionDenied

def validate_product_creation_age(birthdate_str):
    """
    Validates user age based on the string timestamp excracted from the JWT token
    """
    # Rule 2: If the birthdate is missing from the token payload
    if not birthdate_str:
        raise PermissionDenied("Please specify your birthdate to create a product.")
    
    try:
        birthdate = datetime.strptime(birthdate_str, "%Y-%m-%d").date()
    except ValueError:
        raise PermissionDenied("Invalid birthdate format found in token.")
    
    # Calculate exact age accurately
    today = date.today()
    age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))

    # Rule 1: If the user is a minor
    if age < 18:
        raise PermissionDenied("You must be 18 year old to create a product.")