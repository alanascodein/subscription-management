import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

class ProofBillPasswordValidator:
    """
    Validates that the password meets ProofBill requirements:
    - At least 9 characters long
    - Contains at least one uppercase letter
    - Contains at least one lowercase letter
    - Contains at least one special character
    """
    def __init__(self, min_length=9):
        self.min_length = min_length

    def validate(self, password, user=None):
        if len(password) < self.min_length:
            raise ValidationError(
                _(f"This password must contain at least {self.min_length} characters."),
                code='password_too_short',
            )
        if not re.search(r'[A-Z]', password):
            raise ValidationError(
                _("This password must contain at least one uppercase letter."),
                code='password_no_upper',
            )
        if not re.search(r'[a-z]', password):
            raise ValidationError(
                _("This password must contain at least one lowercase letter."),
                code='password_no_lower',
            )
        if not re.search(r'[^A-Za-z0-9]', password):
            raise ValidationError(
                _("This password must contain at least one special character."),
                code='password_no_special',
            )

    def get_help_text(self):
        return _(
            f"Your password must be at least {self.min_length} characters long and "
            "contain uppercase letters, lowercase letters, and at least one special character."
        )
