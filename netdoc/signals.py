"""Signals for NetDoc models."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2023, Andrea Dainese"
__license__ = "GPLv3"

import base64
from cryptography.fernet import Fernet, InvalidToken

from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.conf import settings

from netdoc import models

SECRET_KEY = settings.SECRET_KEY.encode("utf-8")
FERNET_KEY = base64.urlsafe_b64encode(SECRET_KEY.ljust(32)[:32])


@receiver(pre_save, sender=models.Credential)
def credential_encrypt(instance, **kwargs):  # pylint: disable=unused-argument
    """Encrypt credentials before saving."""
    fernet_o = Fernet(FERNET_KEY)
    for field in models.CREDENTIAL_ENCRYPTED_FIELDS:
        original_value = getattr(instance, field)
        if not original_value:
            # Empty field
            continue
        # Check if already encrypted
        try:
            fernet_o.decrypt(original_value.encode())
            continue
        except InvalidToken:
            pass
        # Original value is not encrypted
        encrypted_value = fernet_o.encrypt(original_value.encode())
        setattr(instance, field, encrypted_value.decode())
