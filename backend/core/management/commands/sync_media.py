"""Bazadagi FileField/ImageField yo'llari uchun yo'q media fayllarni tiklaydi.

Railway yangi container yaratganda doimiy volume ulanmagan bo'lsa `/app/media`
bo'sh bo'ladi, lekin PostgreSQL yozuvlari saqlanadi. Bu buyruq bazaga tegmaydi:
faqat repositorydagi nashr aktivlaridan aynan yo'q fayllarni qayta nusxalaydi.
Admin yuklagan, repositoryda manbasi bo'lmagan fayllar o'tkazib yuboriladi.
"""
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Bazadagi yo'llar bo'yicha yo'q public media fayllarni repository aktivlaridan tiklaydi."

    def handle(self, *args, **options):
        roots = (
            Path(settings.BASE_DIR) / "data" / "tttaudit" / "img",
            Path(settings.BASE_DIR) / "core" / "static" / "core" / "img" / "slides",
        )
        sources: dict[str, Path] = {}
        for root in roots:
            if root.exists():
                for path in root.rglob("*"):
                    if path.is_file():
                        sources.setdefault(path.name, path)

        restored = missing_source = 0
        for model in apps.get_app_config("core").get_models():
            file_fields = [
                field for field in model._meta.fields
                if field.get_internal_type() in ("FileField", "ImageField")
            ]
            if not file_fields:
                continue
            for obj in model.objects.all().iterator():
                for model_field in file_fields:
                    field = getattr(obj, model_field.name)
                    if not field.name or field.storage.exists(field.name):
                        continue
                    source = sources.get(Path(field.name).name)
                    if source is None:
                        missing_source += 1
                        continue
                    with source.open("rb") as handle:
                        field.storage.save(field.name, File(handle))
                    restored += 1

        self.stdout.write(self.style.SUCCESS(
            f"Media: {restored} fayl tiklandi, {missing_source} manbasiz fayl o'tkazib yuborildi"
        ))
