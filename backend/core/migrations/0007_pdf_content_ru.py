from django.db import migrations


def apply_pdf_content(apps, schema_editor):
    Direction = apps.get_model("core", "Direction")
    Direction.objects.filter(slug="energoaudit").update(
        title_ru="Энергетический аудит",
        summary_ru=(
            "Проводим энергетический аудит в соответствии с требованиями законодательства Республики Узбекистан, "
            "включая Закон № ЗРУ-940 и Постановление Кабинета Министров № 690. Оцениваем эффективность использования "
            "энергоресурсов, определяем потенциал энергосбережения, разрабатываем рекомендации по повышению "
            "энергоэффективности и энергетический паспорт объекта."
        ),
    )
    Direction.objects.filter(slug="olchov-auditi").update(
        title_ru="Контрольный обмер в строительстве",
        summary_ru=(
            "Проверяем соответствие фактически выполненных строительно-монтажных и ремонтно-строительных работ "
            "проектно-сметной и исполнительной документации, анализируем объёмы и стоимость выполненных работ."
        ),
    )


class Migration(migrations.Migration):
    dependencies = [("core", "0006_image_size_validators")]
    operations = [migrations.RunPython(apply_pdf_content, migrations.RunPython.noop)]
