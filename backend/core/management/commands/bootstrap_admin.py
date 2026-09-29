"""Environment secretlari orqali production superadminini idempotent sozlash."""

import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "DJANGO_ADMIN_USERNAME/PASSWORD berilganda superadmin yaratadi yoki yangilaydi."

    def handle(self, *args, **options):
        username = os.environ.get("DJANGO_ADMIN_USERNAME", "").strip()
        password = os.environ.get("DJANGO_ADMIN_PASSWORD", "")
        if not username and not password:
            self.stdout.write("Admin bootstrap: oʻtkazib yuborildi")
            return
        if not username or not password:
            raise CommandError("DJANGO_ADMIN_USERNAME va DJANGO_ADMIN_PASSWORD birga berilishi shart")

        user_model = get_user_model()
        user, created = user_model.objects.get_or_create(username=username)
        user.is_active = True
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save(update_fields=["password", "is_active", "is_staff", "is_superuser"])
        action = "yaratildi" if created else "yangilandi"
        self.stdout.write(self.style.SUCCESS(f"Admin bootstrap: {username} {action}"))
