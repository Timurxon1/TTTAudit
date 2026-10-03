from django.db import migrations


def replace_deputy_director(apps, schema_editor):
    TeamMember = apps.get_model("core", "TeamMember")
    otabek = TeamMember.objects.filter(slug="xudayberdiev-otabek-talipovich").first()
    davronbek = TeamMember.objects.filter(slug="botirov-davronbek-baxtiyorovich").first()
    if not davronbek:
        return

    davronbek.dept = "energy"
    davronbek.is_leadership = True
    davronbek.order = otabek.order if otabek else 2
    davronbek.role_uz = "Bosh direktor oʻrinbosari"
    davronbek.role_ru = "Заместитель Генерального директора"
    davronbek.role_en = "Deputy General Director"
    davronbek.save(update_fields=[
        "dept", "is_leadership", "order", "role_uz", "role_ru", "role_en",
    ])

    if otabek:
        otabek.delete()


class Migration(migrations.Migration):
    dependencies = [("core", "0007_pdf_content_ru")]
    operations = [migrations.RunPython(replace_deputy_director, migrations.RunPython.noop)]
