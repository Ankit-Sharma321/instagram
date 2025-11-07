# from django.contrib import admin
# from .models import InstagramAccount


# @admin.register(InstagramAccount)
# class InstagramAccountAdmin(admin.ModelAdmin):
#     list_display = ("username", "is_active", "last_success", "login_attempts")
#     list_filter = ("is_active", "created_at")
#     search_fields = ("username",)
#     readonly_fields = ("created_at", "updated_at", "last_success", "session_data")

#     # NEVER show the password in the admin list
#     def get_fields(self, request, obj=None):
#         fields = super().get_fields(request, obj)
#         if "password" in fields:
#             fields = list(fields)
#             fields.remove("password")
#         return fields

# core/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.http import HttpResponseRedirect
from .models import InstagramAccount
import json


@admin.register(InstagramAccount)
class InstagramAccountAdmin(admin.ModelAdmin):
    list_display = [
        "username",
        "password_preview",  # ← shows encrypted password
        "session_preview",  # ← shows sessionid
        "is_active",
        "login_attempts",
        "last_success",
        "copy_session_button",  # ← COPY BUTTON
    ]
    list_editable = ["is_active"]
    search_fields = ["username"]
    readonly_fields = [
        "password",
        "session_data",
        "last_success",
        "created_at",
        "updated_at",
    ]
    list_per_page = 25

    def password_preview(self, obj):
        if obj.password:
            return format_html(
                '<code class="text-xs bg-gray-100 p-1 rounded">{}</code>',
                obj.password[:50] + "..." if len(obj.password) > 50 else obj.password,
            )
        return "-"

    password_preview.short_description = "Password (Encrypted)"

    def session_preview(self, obj):
        sessionid = obj.get_sessionid()
        if sessionid:
            return format_html(
                '<code class="text-xs bg-green-100 p-1 rounded">{}</code>',
                sessionid[:40] + "..." if len(sessionid) > 40 else sessionid,
            )
        return "-"

    session_preview.short_description = "Session ID"

    def copy_session_button(self, obj):
        if obj.get_sessionid():
            return format_html(
                "<button onclick=\"navigator.clipboard.writeText('{}') "
                "&& alert('Session ID copied!')\" "
                'class="bg-blue-600 text-white px-3 py-1 rounded text-xs">'
                "Copy Session ID</button>",
                obj.get_sessionid(),
            )
        return "-"

    copy_session_button.short_description = "Action"
    copy_session_button.allow_tags = True
