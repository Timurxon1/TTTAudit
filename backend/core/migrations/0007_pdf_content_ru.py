from django.db import migrations


def apply_pdf_content(apps, schema_editor):
    Direction = apps.get_model("core", "Direction")
    Direction.objects.filter(slug="energoaudit").update(
        title_uz="Energiya auditi",
        title_ru="Энергетический аудит",
        title_en="Energy audit",
        summary_uz=(
            "Oʻzbekiston Respublikasi qonunchiligi, jumladan OʻRQ-940-son Qonun va Vazirlar Mahkamasining 690-son "
            "qarori talablariga muvofiq energiya auditini oʻtkazamiz. Energiya resurslaridan foydalanish "
            "samaradorligini baholaymiz, energiya tejash salohiyatini aniqlaymiz, energiya samaradorligini oshirish "
            "boʻyicha tavsiyalar va obyektning energetik pasportini ishlab chiqamiz."
        ),
        summary_ru=(
            "Проводим энергетический аудит в соответствии с требованиями законодательства Республики Узбекистан, "
            "включая Закон № ЗРУ-940 и Постановление Кабинета Министров № 690. Оцениваем эффективность использования "
            "энергоресурсов, определяем потенциал энергосбережения, разрабатываем рекомендации по повышению "
            "энергоэффективности и энергетический паспорт объекта."
        ),
        summary_en=(
            "We conduct energy audits in accordance with the legislation of Uzbekistan, including Law No. ZRU-940 "
            "and Cabinet of Ministers Resolution No. 690. We assess energy-resource efficiency, identify energy-saving "
            "potential, develop efficiency recommendations and prepare the facility’s energy passport."
        ),
    )
    Direction.objects.filter(slug="olchov-auditi").update(
        title_uz="Qurilishda nazorat oʻlchovi",
        title_ru="Контрольный обмер в строительстве",
        title_en="Control measurement in construction",
        summary_uz=(
            "Haqiqatda bajarilgan qurilish-montaj va taʼmirlash-qurilish ishlarining loyiha-smeta hamda ijro "
            "hujjatlariga muvofiqligini tekshiramiz, bajarilgan ishlar hajmi va qiymatini tahlil qilamiz."
        ),
        summary_ru=(
            "Проверяем соответствие фактически выполненных строительно-монтажных и ремонтно-строительных работ "
            "проектно-сметной и исполнительной документации, анализируем объёмы и стоимость выполненных работ."
        ),
        summary_en=(
            "We verify that completed construction, installation and repair works comply with the design, estimate "
            "and as-built documentation, and analyse the quantities and value of the completed work."
        ),
    )


class Migration(migrations.Migration):
    dependencies = [("core", "0006_image_size_validators")]
    operations = [migrations.RunPython(apply_pdf_content, migrations.RunPython.noop)]
