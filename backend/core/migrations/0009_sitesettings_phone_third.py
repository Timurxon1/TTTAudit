from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("core", "0008_replace_otabek_with_davronbek")]

    operations = [
        migrations.AddField(
            model_name="sitesettings",
            name="phone_third",
            field=models.CharField(blank=True, max_length=40, verbose_name="Uchinchi telefon"),
        ),
    ]
