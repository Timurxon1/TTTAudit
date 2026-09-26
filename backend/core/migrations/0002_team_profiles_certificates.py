import re

import django.db.models.deletion
from django.db import migrations, models
from django.utils.text import slugify


def fill_slugs(apps, schema_editor):
    """Mavjud xodimlarga lotin ismidan noyob slug beradi (unique cheklovidan oldin)."""
    TeamMember = apps.get_model("core", "TeamMember")
    used = set()
    for member in TeamMember.objects.order_by("pk"):
        base = slugify(re.sub(r"[ʻʼ'‘’`]", "", member.full_name or ""))[:130] or "xodim"
        slug, n = base, 2
        while slug in used:
            slug, n = f"{base}-{n}", n + 1
        used.add(slug)
        member.slug = slug
        member.save(update_fields=["slug"])


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="teammember",
            name="slug",
            # PostgreSQL'da SlugField vaqtincha db_index yaratadi; quyidagi
            # unique SlugField ga o'tishda Django xuddi shu `_like` indeksini
            # yana yaratib DuplicateTable bilan yiqiladi. Ma'lumot to'ldirish
            # bosqichida indeks kerak emas, shuning uchun oddiy CharField.
            field=models.CharField(max_length=140, null=True, blank=True),
        ),
        migrations.RunPython(fill_slugs, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="teammember",
            name="slug",
            field=models.SlugField(
                help_text="Profil manzili: /jamoa/<slug>/ (lotin ismidan)", max_length=140, unique=True,
            ),
        ),
        migrations.AddField(
            model_name="teammember",
            name="education",
            field=models.JSONField(
                blank=True, default=list,
                help_text='[{"years": "2004", "uz": "...", "ru": "...", "en": "..."}]', verbose_name="Maʼlumoti",
            ),
        ),
        migrations.AddField(
            model_name="teammember",
            name="experience",
            field=models.JSONField(
                blank=True, default=list,
                help_text='[{"years": "1979–1989", "uz": "...", "ru": "...", "en": "..."}]',
                verbose_name="Ish tajribasi",
            ),
        ),
        migrations.AlterField(
            model_name="teammember",
            name="dept",
            field=models.CharField(
                choices=[
                    ("management", "Rahbariyat"),
                    ("energy", "Energoaudit"),
                    ("construction", "Qurilishda nazorat oʻlchovi"),
                ],
                default="energy", max_length=16, verbose_name="Boʻlim",
            ),
        ),
        migrations.CreateModel(
            name="StaffCertificate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("scan", models.ImageField(blank=True, null=True, upload_to="team/certificates/", verbose_name="Skan")),
                ("title", models.CharField(max_length=255, verbose_name="Nomi")),
                ("issuer", models.CharField(blank=True, max_length=255, verbose_name="Bergan tashkilot")),
                ("number", models.CharField(blank=True, max_length=80, verbose_name="Raqam")),
                ("issued_on", models.DateField(blank=True, null=True, verbose_name="Berilgan sana")),
                ("valid_until", models.DateField(blank=True, null=True, verbose_name="Amal qilish muddati")),
                ("scope_uz", models.TextField(blank=True)),
                ("scope_ru", models.TextField(blank=True)),
                ("scope_en", models.TextField(blank=True)),
                ("order", models.PositiveSmallIntegerField(default=0)),
                ("member", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE, related_name="certificates",
                    to="core.teammember", verbose_name="Mutaxassis",
                )),
            ],
            options={
                "verbose_name": "Xodim sertifikati",
                "verbose_name_plural": "Xodim sertifikatlari",
                "ordering": ["member", "order", "pk"],
            },
        ),
    ]
