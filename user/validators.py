import re

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _


def SymbolValidator(string):
    if not re.findall('[()[\]{}|\\`~!@#$%^&*_\-+=;:\'",<>./?]', string):
        raise ValidationError(
            _(f"Password must contain at least 1 symbol: " +
              "A-Z a-z 0-9 @#$%^&*_"),
            code='password_no_symbol',
        )

# def validate_confirm_password(self, password1):
#     print(password1)
#     if not re.findall('[A-Za-z0-9@#$%^&+=]{8,}', password1):
#         raise ValidationError(
#             _("The New Password must contain at least 1 symbol: " +
#               "A-Z a-z 0-9 @#$"),
#             code='password1_no_symbol',
#         )
#     return password1
