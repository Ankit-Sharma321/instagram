from django.contrib import admin
from django.utils.html import format_html
from .models import InstagramAccount
from cryptography.fernet import Fernet
import os
import json

fernet = Fernet(os.getenv('FERNET_KEY').encode())

@admin.register(InstagramAccount)
class InstagramAccountAdmin(admin.ModelAdmin):
    list_display = ['username', 'real_password', 'real_sessionid', 'copy_btn', 'is_active', 'created_at']
    search_fields = ['username']
    list_filter = ['is_active', 'created_at']
    readonly_fields = ['username', 'password', 'session_data', 'created_at']

    def real_password(self, obj):
        return obj.password
    real_password.short_description = "Password"

    def real_sessionid(self, obj):
        try:
            decrypted = fernet.decrypt(obj.session_data.encode()).decode()
            data = json.loads(decrypted)
            sessionid = data.get("authorization_data", {}).get("sessionid", "")
            if sessionid:
                short = sessionid[:60] + "..." if len(sessionid) > 60 else sessionid
                return format_html('<code style="font-size:10px;background:#000;color:#0f0;padding:5px;">{}</code>', short)
            else:
                return format_html('<span style="color:red;">NO SESSION</span>')
        except:
            return format_html('<span style="color:orange;">DECRYPT ERROR</span>')
    real_sessionid.short_description = "Session ID"

    def copy_btn(self, obj):
        try:
            decrypted = fernet.decrypt(obj.session_data.encode()).decode()
            sessionid = json.loads(decrypted).get("authorization_data", {}).get("sessionid", "")
            if sessionid:
                return format_html(
                    '<button onclick="navigator.clipboard.writeText(\'{}\');this.innerText=\'COPIED!\';setTimeout(()=>this.innerText=\'COPY\',2000)" '
                    'style="background:#00ff00;color:black;padding:8px 16px;border:none;border-radius:8px;font-weight:bold;cursor:pointer;">'
                    'COPY</button>', sessionid
                )
        except:
            pass
        return "-"
    copy_btn.short_description = "Action"