"""Tahririy kontent: yoʻnalishlar, xizmatlar, meʼyoriy hujjatlar, maqolalar.

    python manage.py seed_content          # faqat boʻsh bazani toʻldiradi
    python manage.py seed_content --force  # mavjud yozuvlarni shu matn bilan yangilaydi

Kompaniya haqidagi faktlar (litsenziya, jamoa, mijozlar, raqamlar) bu yerda
YOʻQ — ular data/tttaudit/*.json dan `import_tttaudit` bilan yuklanadi.

Qoidalar:
- Kompaniya haqida manbasiz daʼvo yozilmaydi (muddat, narx, kafolat, raqam).
- Qonunga tayangan hujjat `verified_on` bilan belgilanadi; boʻsh boʻlsa
  u saytda koʻrinmaydi. Tekshiruv: lex.uz dagi amaldagi tahrir.
- Xizmat jarayoni va natijalari — umumiy metodika, mijoz koʻrib chiqadi.
"""
import datetime as dt

from django.core.management.base import BaseCommand

from core.models import Direction, LegalAct, Post, Service, SiteSettings

# lex.uz bilan solishtirilgan sana
VERIFIED_ON = dt.date(2026, 9, 11)


def t(uz, ru="", en=""):
    return {"uz": uz, "ru": ru or uz, "en": en or uz}


# ------------------------------------------------------------------ direction
DIRECTIONS = [
    {
        "slug": "energoaudit",
        "order": 0,
        "accent": Direction.ACCENT_AMBER,
        "kicker_uz": "Yoʻnalish I", "kicker_ru": "Направление I", "kicker_en": "Practice I",
        "title_uz": "Energosamaradorlik auditi",
        "title_ru": "Энергетический аудит",
        "title_en": "Energy efficiency audit",
        "summary_uz": "ЗРУ-940 boʻyicha majburiy energoaudit, bino energopasporti va energosamaradorlik toifasi.",
        "summary_ru": ("Проводим энергетический аудит в соответствии с требованиями законодательства "
                       "Республики Узбекистан, включая Закон № ЗРУ-940 и Постановление Кабинета Министров № 690. "
                       "Оцениваем эффективность использования энергоресурсов, определяем потенциал энергосбережения, "
                       "разрабатываем рекомендации по повышению энергоэффективности и энергетический паспорт объекта."),
        "summary_en": "Mandatory energy audit under ZRU-940, building energy passport and efficiency category.",
        "problem_title_uz": "Nega bu endi majburiy",
        "problem_title_ru": "Почему это теперь обязательно",
        "problem_title_en": "Why this is now mandatory",
        "problem_body_uz": (
            "2024-yilda «Energiyani tejash, undan oqilona foydalanish va "
            "energiya samaradorligini oshirish toʻgʻrisida»gi yangi qonun qabul qilindi. "
            "Unga koʻra davriy energoaudit majburiy tartibda besh yilda kamida bir marta "
            "oʻtkaziladi.\n\n"
            "Foydalaniladigan maydoni 200 m² dan katta bino va inshootlar uchun "
            "energosamaradorlik toifasi belgilanadi.\n\n"
            "Obyektingizga qaysi talab tegishli ekanini va audit muddatini dastlabki "
            "suhbatda aniqlaymiz."
        ),
        "problem_body_ru": (
            "В 2024 году принят новый закон «Об экономии энергии, ее рациональном "
            "использовании и повышении энергоэффективности». Периодический энергоаудит "
            "по нему проводится в обязательном порядке не реже одного раза в пять лет.\n\n"
            "Для зданий и сооружений с используемой площадью более 200 м² определяется "
            "категория энергоэффективности.\n\n"
            "Какое требование касается вашего объекта и когда нужен аудит — определим "
            "на первой встрече."
        ),
        "problem_body_en": (
            "A new law on energy saving, rational use and energy efficiency was adopted "
            "in 2024. Periodic energy audits under it are mandatory at least once every "
            "five years.\n\n"
            "Buildings and structures with a usable area over 200 m² are assigned an "
            "energy efficiency category.\n\n"
            "We establish which requirement applies to your site, and when, at the first meeting."
        ),
        "legal_note_uz": "Energoaudit majburiy va ixtiyoriy shaklda tashkil etiladi (ЗРУ-940).",
        "legal_note_ru": "Энергоаудит организуется в обязательной и добровольной форме (Закон № ЗРУ-940).",
        "legal_note_en": "Energy audits are organised as mandatory or voluntary (ZRU-940).",
        "process": [
            t("Dastlabki suhbat: obyekt turi, maydon, isteʼmol, oldingi auditlar",
              "Первая встреча: тип объекта, площадь, потребление, прежние аудиты",
              "First meeting: site type, area, consumption, previous audits"),
            t("Maʼlumot yigʻish: uch yillik isteʼmol, hisoblagichlar, ishlab chiqarish hajmi",
              "Сбор данных: потребление за три года, приборы учёта, объём производства",
              "Data collection: three years of consumption, meters, output"),
            t("Obyektda instrumental tekshiruv", "Инструментальное обследование на объекте", "On-site instrumental survey"),
            t("Energiya balansi — qayerda va qancha yoʻqotilyapti", "Энергобаланс — где и сколько теряется", "Energy balance — where and how much is lost"),
            t("Tadbirlar roʻyxati: sarf, yillik tejov, qoplanish muddati",
              "Перечень мероприятий: затраты, годовая экономия, срок окупаемости",
              "Measures: cost, annual saving, payback period"),
            t("Energopasport va hisobot", "Энергопаспорт и отчёт", "Energy passport and report"),
        ],
        "deliverables": [
            t("Bino yoki korxonaning energetik pasporti", "Энергетический паспорт здания или предприятия", "Energy passport of the building or plant"),
            t("Energiya balansi va yoʻqotishlar tahlili", "Энергобаланс и анализ потерь", "Energy balance and loss analysis"),
            t("Tadbirlar rejasi: tadbir → sarf → yillik tejov → qoplanish muddati",
              "План мероприятий: мера → затраты → годовая экономия → окупаемость",
              "Action plan: measure → cost → annual saving → payback"),
        ],
    },
    {
        "slug": "olchov-auditi",
        "order": 1,
        "accent": Direction.ACCENT_STEEL,
        "kicker_uz": "Yoʻnalish II", "kicker_ru": "Направление II", "kicker_en": "Practice II",
        "title_uz": "Qurilishda nazorat oʻlchovi",
        "title_ru": "Контрольный обмер в строительстве",
        "title_en": "Construction control measurement",
        "summary_uz": "Bajarilgan ishlar hajmi va smeta hujjatdagi raqamga mosmi — nazorat oʻlchovi va smeta tahlili.",
        "summary_ru": ("Проверяем соответствие фактически выполненных строительно-монтажных и ремонтно-строительных "
                       "работ проектно-сметной и исполнительной документации, анализируем объёмы и стоимость "
                       "выполненных работ."),
        "summary_en": "Do completed volumes and the estimate match the documents — control measurement and estimate review.",
        "problem_title_uz": "Muammo qanday tugʻiladi",
        "problem_title_ru": "Как возникает проблема",
        "problem_title_en": "How the problem arises",
        "problem_body_uz": (
            "Pudratchi bajarilgan ishlar dalolatnomasini topshiradi: shuncha m³ beton, "
            "shuncha m² suvoq, shuncha tonna armatura. Buyurtmachi imzolaydi va toʻlaydi.\n\n"
            "Keyin maʼlum boʻladiki: hajm oshirib yozilgan, material arzonrogʻiga "
            "almashtirilgan yoki smeta normalari notoʻgʻri qoʻllanilgan.\n\n"
            "Audit — obyektda haqiqatda nima borligini oʻlchash va uni hujjatdagi raqam "
            "bilan solishtirish."
        ),
        "problem_body_ru": (
            "Подрядчик сдаёт акт выполненных работ: столько-то м³ бетона, столько-то м² "
            "штукатурки, столько-то тонн арматуры. Заказчик подписывает и платит.\n\n"
            "Потом выясняется: объём завышен, материал заменён на более дешёвый или "
            "сметные нормы применены неверно.\n\n"
            "Аудит — это замер того, что фактически есть на объекте, и сверка с цифрой в документе."
        ),
        "problem_body_en": (
            "The contractor submits a completion act: so many m³ of concrete, so many m² "
            "of plaster, so many tonnes of rebar. The client signs and pays.\n\n"
            "Later it turns out the volume was overstated, material was swapped for a "
            "cheaper one, or estimate norms were misapplied.\n\n"
            "The audit measures what is actually on site and compares it with the document."
        ),
        "process": [
            t("Hujjatlarni qabul qilish: loyiha-smeta, shartnoma, bajarilgan ishlar dalolatnomalari",
              "Приём документов: проектно-сметная документация, договор, акты выполненных работ",
              "Documents: design estimate, contract, completion acts"),
            t("Kameral tahlil: smeta normalari, koeffitsiyentlar, takror pozitsiyalar",
              "Камеральный анализ: сметные нормы, коэффициенты, повторы",
              "Desk review: estimate norms, coefficients, duplicates"),
            t("Obyektda oʻlchov va fotofiksatsiya — tomonlar ishtirokida",
              "Обмер и фотофиксация на объекте — в присутствии сторон",
              "On-site measurement and photos — with both parties present"),
            t("Taqqoslash vedomosti: hujjat boʻyicha / haqiqatda / farq",
              "Сравнительная ведомость: по документу / фактически / разница",
              "Comparison sheet: per document / actual / difference"),
            t("Dalolatnoma va hisobot", "Акт и отчёт", "Act and report"),
        ],
        "deliverables": [
            t("Nazorat oʻlchovi dalolatnomasi", "Акт контрольного обмера", "Control measurement act"),
            t("Hajmlar taqqoslash vedomosti: hujjat / haqiqat / farq",
              "Сравнительная ведомость объёмов: документ / факт / разница",
              "Volume comparison: document / actual / difference"),
            t("Smeta qayta hisobi — farq summasi soʻmda", "Пересчёт сметы — сумма расхождения в сумах", "Estimate recalculation — difference in UZS"),
        ],
    },
]

# ------------------------------------------------------------------- services
SERVICES = {
    "energoaudit": [
        {
            "slug": "majburiy",
            "title_uz": "Majburiy energoaudit", "title_ru": "Обязательный энергоаудит", "title_en": "Mandatory energy audit",
            "summary_uz": "Davlat energetika reestriga kiritilgan subyektlar uchun",
            "summary_ru": "Для субъектов Государственного энергетического реестра",
            "summary_en": "For entities listed in the State Energy Register",
            "body_uz": ("ЗРУ-940 ga koʻra periodik energoaudit majburiy tartibda besh yilda kamida "
                        "bir marta oʻtkaziladi. Audit natijasida energetik pasport va tadbirlar "
                        "rejasi tuziladi."),
            "body_ru": ("Согласно Закону № ЗРУ-940 периодический энергоаудит проводится в обязательном "
                        "порядке не реже одного раза в пять лет. По его итогам составляются энергетический "
                        "паспорт и план мероприятий."),
            "body_en": ("Under ZRU-940, a periodic energy audit is mandatory at least once every five "
                        "years. The audit results in an energy passport and an action plan."),
            "process": [
                t("Reestrdagi holat va audit muddatini aniqlash", "Статус в реестре и срок аудита", "Register status and audit deadline"),
                t("Uch yillik isteʼmol maʼlumotlarini yigʻish", "Сбор данных о потреблении за три года", "Three years of consumption data"),
                t("Instrumental tekshiruv", "Инструментальное обследование", "Instrumental survey"),
                t("Energiya balansi va tadbirlar rejasi", "Энергобаланс и план мероприятий", "Energy balance and action plan"),
                t("Energopasport", "Энергопаспорт", "Energy passport"),
            ],
            "deliverables": [t("Energetik pasport", "Энергетический паспорт", "Energy passport"),
                             t("Audit hisoboti", "Отчёт об аудите", "Audit report"),
                             t("Tadbirlar rejasi", "План мероприятий", "Action plan")],
            "faq": [
                {"q": t("Reestrga kirganimni qanday bilaman?", "Как узнать, включены ли мы в реестр?", "How do I know if we are on the register?"),
                 "a": t("Soʻrov qoldiring — tekshirib beramiz.", "Оставьте заявку — проверим.", "Send a request and we will check.")},
                {"q": t("Ishlab chiqarishni toʻxtatish kerakmi?", "Нужно ли останавливать производство?", "Do we have to stop production?"),
                 "a": t("Yoʻq. Oʻlchovlar ish rejimida oʻtkaziladi.", "Нет. Замеры проводятся в рабочем режиме.", "No. Measurements are taken under normal operation.")},
            ],
        },
        {
            "slug": "energopasport",
            "title_uz": "Bino energopasporti", "title_ru": "Энергопаспорт здания", "title_en": "Building energy passport",
            "summary_uz": "200 m² dan katta bino va inshootlar uchun energosamaradorlik toifasi",
            "summary_ru": "Категория энергоэффективности для зданий площадью более 200 м²",
            "summary_en": "Energy efficiency category for buildings over 200 m²",
            "body_uz": ("Foydalaniladigan maydoni 200 m² dan katta bino va inshootlar uchun "
                        "energosamaradorlik toifasi belgilanadi (ЗРУ-940). Energopasport yangi "
                        "qurilgan, mavjud, rekonstruksiya va modernizatsiya qilingan obyektlar uchun "
                        "tuziladi (VM qarori № 690)."),
            "body_ru": ("Для зданий и сооружений с используемой площадью более 200 м² определяется "
                        "категория энергоэффективности (Закон № ЗРУ-940). Энергопаспорт составляется для "
                        "новых, существующих, реконструируемых и модернизируемых объектов "
                        "(Постановление КМ № 690)."),
            "body_en": ("Buildings and structures with a usable area over 200 m² are assigned an energy "
                        "efficiency category (ZRU-940). An energy passport is prepared for newly built, "
                        "existing, reconstructed and modernised facilities (CM Resolution No. 690)."),
            "process": [
                t("Bino konstruksiyalari va muhandislik tizimlarini oʻrganish", "Изучение конструкций и инженерных систем", "Envelope and building services review"),
                t("Isteʼmol maʼlumotlari va hisoblagichlar", "Данные потребления и приборы учёта", "Consumption data and meters"),
                t("Issiqlik yoʻqotishlarini tekshirish", "Обследование теплопотерь", "Heat loss survey"),
                t("Toifa hisobi va energopasport", "Расчёт категории и энергопаспорт", "Category calculation and passport"),
            ],
            "deliverables": [t("Energopasport", "Энергопаспорт", "Energy passport"),
                             t("Energosamaradorlik toifasi boʻyicha xulosa", "Заключение о категории энергоэффективности", "Efficiency category statement")],
        },
        {
            "slug": "termografiya",
            "title_uz": "Termografik tekshiruv", "title_ru": "Термографическое обследование", "title_en": "Thermographic survey",
            "summary_uz": "Issiqlik yoʻqotishlarini aniqlash", "summary_ru": "Выявление теплопотерь", "summary_en": "Detecting heat losses",
            "body_uz": ("Issiqlik kamerasi bino qayerdan issiqlik yoʻqotayotganini koʻrsatadi: "
                        "koʻprik konstruksiyalar, deraza konturi, tom va poydevor birikmasi.\n\n"
                        "Tekshiruv ichki va tashqi harorat farqi yetarli boʻlganda oʻtkaziladi — "
                        "aks holda natija ishonchsiz boʻladi."),
            "body_ru": ("Тепловизор показывает, где здание теряет тепло: мостики холода, оконные "
                        "контуры, примыкания кровли и фундамента.\n\n"
                        "Обследование проводится при достаточной разнице внутренней и наружной "
                        "температуры — иначе результат недостоверен."),
            "body_en": ("A thermal imaging camera shows where a building loses heat: thermal bridges, "
                        "window perimeters, roof and foundation junctions.\n\n"
                        "The survey is carried out only when the difference between indoor and outdoor "
                        "temperatures is sufficient — otherwise the result is unreliable."),
            "process": [
                t("Sharoitni tekshirish va sanani belgilash", "Проверка условий и выбор даты", "Checking conditions and scheduling"),
                t("Fasad va ichki yuzalarni suratga olish", "Съёмка фасада и внутренних поверхностей", "Imaging facades and interiors"),
                t("Termogrammalar tahlili", "Анализ термограмм", "Thermogram analysis"),
                t("Yoʻqotishlar xaritasi va tavsiyalar", "Карта потерь и рекомендации", "Loss map and recommendations"),
            ],
            "deliverables": [t("Termogrammalar izohlari bilan", "Термограммы с пояснениями", "Annotated thermograms"),
                             t("Tavsiyalar", "Рекомендации", "Recommendations")],
        },
        {
            "slug": "ekspress",
            "title_uz": "Ekspress-baholash", "title_ru": "Экспресс-оценка", "title_en": "Express assessment",
            "summary_uz": "Toʻliq audit kerakmi yoʻqmi — dastlabki baho",
            "summary_ru": "Нужен ли полный аудит — предварительная оценка",
            "summary_en": "Is a full audit needed — preliminary assessment",
            "body_uz": ("Isteʼmol maʼlumotlari va bino parametrlari asosida solishtirma sarf "
                        "hisoblanadi. Natija toʻliq audit kerakmi degan qaror uchun asos boʻladi. "
                        "Ekspress-baho rasmiy hujjat emas."),
            "body_ru": ("По данным потребления и параметрам здания рассчитывается удельный расход. "
                        "Результат — основание для решения о полном аудите. Экспресс-оценка не "
                        "является официальным документом."),
            "body_en": ("Specific consumption is calculated from consumption data and building "
                        "parameters. The result serves as the basis for deciding whether a full audit "
                        "is needed. The express assessment is not an official document."),
            "process": [
                t("Isteʼmol va maydon maʼlumotlari", "Данные о потреблении и площади", "Consumption and area data"),
                t("Solishtirma sarf hisobi", "Расчёт удельного расхода", "Specific consumption"),
                t("Tavsiya", "Рекомендация", "Recommendation"),
            ],
            "deliverables": [t("Ekspress-xulosa", "Экспресс-заключение", "Express note")],
        },
    ],
    "olchov-auditi": [
        {
            "slug": "nazorat-olchovi",
            "title_uz": "Nazorat oʻlchovi", "title_ru": "Контрольный обмер", "title_en": "Control measurement",
            "summary_uz": "Bajarilgan ishlar hajmining instrumental tekshiruvi",
            "summary_ru": "Инструментальная проверка объёмов выполненных работ",
            "summary_en": "Instrumental verification of completed work volumes",
            "body_uz": ("Nazorat oʻlchovi — qurilish-montaj ishlarining haqiqatda bajarilgan "
                        "hajmini aniqlash. Vizual koʻrik, instrumental oʻlchov va hisoblash birga "
                        "qoʻllaniladi.\n\n"
                        "Natijada har bir smeta pozitsiyasi boʻyicha uch ustunli vedomost tuziladi: "
                        "hujjat boʻyicha, haqiqatda, farq."),
            "body_ru": ("Контрольный обмер — определение фактически выполненных объёмов "
                        "строительно-монтажных работ. Применяются осмотр, инструментальный замер и "
                        "расчёт.\n\n"
                        "По каждой сметной позиции составляется ведомость в три колонки: по "
                        "документу, фактически, разница."),
            "body_en": ("Control measurement establishes the volume of construction and installation "
                        "work actually performed. Visual inspection, instrumental measurement and "
                        "calculation are used together.\n\n"
                        "For each estimate item a three-column statement is prepared: per document, "
                        "actual, difference."),
            "process": [
                t("Loyiha-smeta hujjati va dalolatnomalarni qabul qilish", "Приём ПСД и актов", "Receiving estimate and acts"),
                t("Kameral tahlil", "Камеральный анализ", "Desk review"),
                t("Obyektda oʻlchov, tomonlar ishtirokida", "Обмер на объекте в присутствии сторон", "On-site measurement with both parties"),
                t("Taqqoslash vedomosti va dalolatnoma", "Сравнительная ведомость и акт", "Comparison sheet and act"),
            ],
            "deliverables": [t("Nazorat oʻlchovi dalolatnomasi", "Акт контрольного обмера", "Control measurement act"),
                             t("Ortiqcha toʻlov hisobi", "Расчёт переплаты", "Overpayment calculation")],
            "faq": [
                {"q": t("Qurilishni toʻxtatish kerakmi?", "Нужно ли останавливать стройку?", "Do we have to stop the works?"),
                 "a": t("Yoʻq. Oʻlchov ish jarayoniga xalaqit bermaydi.", "Нет. Обмер не мешает работам.", "No. Measurement does not interrupt the works.")},
            ],
        },
        {
            "slug": "smeta-auditi",
            "title_uz": "Smeta auditi", "title_ru": "Аудит сметы", "title_en": "Estimate audit",
            "summary_uz": "Loyiha-smeta hujjatidagi normalar va koeffitsiyentlar tahlili",
            "summary_ru": "Анализ норм и коэффициентов в проектно-сметной документации",
            "summary_en": "Review of norms and coefficients in the design estimate",
            "body_uz": ("Obyektga chiqmasdan, hujjat asosida oʻtkaziladi: notoʻgʻri rastsenka, "
                        "takrorlangan pozitsiya, asossiz koeffitsiyent."),
            "body_ru": ("Проводится по документам, без выезда на объект: неверные расценки, "
                        "повторяющиеся позиции, необоснованные коэффициенты."),
            "body_en": ("Carried out on the basis of documents, without a site visit: incorrect unit "
                        "rates, duplicated items, unjustified coefficients."),
            "process": [
                t("Smeta va loyiha hujjatini qabul qilish", "Приём сметы и проекта", "Receiving the estimate"),
                t("Normativ bazaga solishtirish", "Сверка с нормативной базой", "Checking against norms"),
                t("Takror va asossiz pozitsiyalarni aniqlash", "Выявление повторов и необоснованных позиций", "Finding duplicates and unjustified items"),
                t("Tuzatilgan smeta va xulosa", "Исправленная смета и заключение", "Corrected estimate and opinion"),
            ],
            "deliverables": [t("Smeta auditi xulosasi", "Заключение по аудиту сметы", "Estimate audit opinion"),
                             t("Tuzatilgan smeta hisobi", "Исправленный расчёт сметы", "Corrected estimate")],
        },
        {
            "slug": "texnik-nazorat",
            "title_uz": "Texnik nazorat", "title_ru": "Технический надзор", "title_en": "Technical supervision",
            "summary_uz": "Qurilish jarayonida bosqichma-bosqich nazorat",
            "summary_ru": "Поэтапный контроль в процессе строительства",
            "summary_en": "Stage-by-stage control during construction",
            "body_uz": ("Hali bajarilmagan ish uchun toʻlamaslik uchun: har bosqichda hajm va sifat "
                        "tasdiqlanadi, yashirin ishlar yopilishidan oldin qayd etiladi."),
            "body_ru": ("Чтобы не платить за невыполненное: на каждом этапе подтверждаются объём и "
                        "качество, скрытые работы фиксируются до закрытия."),
            "body_en": ("So that you do not pay for work not yet done: volume and quality are confirmed "
                        "at each stage, and hidden works are recorded before they are covered."),
            "process": [
                t("Bosqichlar jadvalini kelishish", "Согласование графика этапов", "Agreeing the stage schedule"),
                t("Har bosqichda obyektga chiqish", "Выезд на каждом этапе", "Site visit at each stage"),
                t("Yashirin ishlar dalolatnomalari", "Акты скрытых работ", "Hidden works acts"),
                t("Davriy hisobot", "Периодический отчёт", "Periodic report"),
            ],
            "deliverables": [t("Bosqich dalolatnomalari", "Акты этапов", "Stage acts"),
                             t("Nazorat hisoboti", "Отчёт о надзоре", "Supervision report")],
        },
        {
            "slug": "nizo",
            "title_uz": "Nizoda mustaqil xulosa", "title_ru": "Независимое заключение в споре", "title_en": "Independent opinion in disputes",
            "summary_uz": "Tomonlar turli raqam koʻrsatayotganda uchinchi tomon oʻlchovi",
            "summary_ru": "Замер третьей стороной, когда стороны приводят разные цифры",
            "summary_en": "Third-party measurement when the parties' figures differ",
            "body_uz": ("Tomonlar bir-biriga qarama-qarshi raqam koʻrsatayotganda mustaqil uchinchi "
                        "tomon kerak boʻladi. Oʻlchov ikkala tomon ishtirokida oʻtkaziladi va "
                        "bayonnoma bilan rasmiylashtiriladi."),
            "body_ru": ("Когда стороны приводят противоположные цифры, нужна независимая третья "
                        "сторона. Замер проводится в присутствии обеих сторон и оформляется протоколом."),
            "body_en": ("When the parties present conflicting figures, an independent third party is "
                        "needed. The measurement is carried out in the presence of both parties and "
                        "recorded in minutes."),
            "process": [
                t("Nizo hujjatlarini oʻrganish", "Изучение документов спора", "Reviewing the dispute file"),
                t("Tomonlarni oʻlchovga chaqirish", "Приглашение сторон на замер", "Inviting both parties"),
                t("Oʻlchov va bayonnoma", "Замер и протокол", "Measurement and minutes"),
                t("Xulosa", "Заключение", "Opinion"),
            ],
            "deliverables": [t("Xulosa", "Заключение", "Opinion"),
                             t("Oʻlchov bayonnomasi", "Протокол замера", "Measurement minutes")],
        },
    ],
}

# ------------------------------------------------------------------ legal acts
ACTS = [
    {"number": "ЗРУ-940", "order": 0, "directions": ["energoaudit"],
     "title_uz": "«Energiyani tejash, undan oqilona foydalanish va energiya samaradorligini oshirish toʻgʻrisida»gi Qonun",
     "title_ru": "Закон «Об экономии энергии, ее рациональном использовании и повышении энергоэффективности»",
     "title_en": "Law on energy saving, its rational use and improving energy efficiency",
     "applies_to_uz": "Energiya subyektlari, bino va inshootlar",
     "applies_to_ru": "Субъекты энергии, здания и сооружения",
     "applies_to_en": "Energy entities, buildings and structures",
     "requirement_uz": ("Energoaudit majburiy va ixtiyoriy shaklda tashkil etiladi. Foydalaniladigan "
                        "maydoni 200 m² dan katta bino va inshootlar uchun energosamaradorlik toifasi belgilanadi."),
     "requirement_ru": ("Энергоаудит организуется в обязательной и добровольной форме. Для зданий и "
                        "сооружений с используемой площадью более 200 м² определяется категория энергоэффективности."),
     "requirement_en": ("Energy audits are mandatory or voluntary. Buildings over 200 m² of usable area "
                        "are assigned an energy efficiency category."),
     "deadline_uz": "Davriy energoaudit — besh yilda kamida bir marta",
     "deadline_ru": "Периодический энергоаудит — не реже одного раза в пять лет",
     "deadline_en": "Periodic energy audit — at least once every five years",
     "lex_url": "https://www.lex.uz/acts/7052217",
     "verified_on": VERIFIED_ON},
    {"number": "VM qarori № 690", "order": 1, "directions": ["energoaudit"],
     "title_uz": "Yoqilgʻi-energetika resurslari isteʼmolchilari hamda bino va inshootlar energiya isteʼmolining energoauditini oʻtkazish tartibini belgilash toʻgʻrisida",
     "title_ru": "Об установлении порядка проведения энергоаудита потребителей топливно-энергетических ресурсов и энергопотребления зданий и сооружений",
     "title_en": "On the procedure for energy audits of fuel and energy consumers and of energy use in buildings",
     "adopted_on": dt.date(2024, 10, 19), "effective_on": dt.date(2024, 10, 21),
     "applies_to_uz": "Yoqilgʻi-energetika resurslari isteʼmolchilari, bino va inshootlar",
     "applies_to_ru": "Потребители ТЭР, здания и сооружения",
     "applies_to_en": "Fuel and energy consumers, buildings and structures",
     "requirement_uz": ("Energoaudit yangi qurilayotgan, mavjud, qayta profillangan, rekonstruksiya, "
                        "kapital taʼmir va modernizatsiya qilinayotgan bino va inshootlarning energetik "
                        "pasportini ishlab chiqishda oʻtkaziladi."),
     "requirement_ru": ("Энергоаудит проводится при разработке энергетических паспортов вновь строящихся, "
                        "существующих, перепрофилированных, реконструируемых, капитально ремонтируемых и "
                        "модернизируемых зданий и сооружений."),
     "requirement_en": ("An energy audit is carried out when preparing energy passports for new, existing, "
                        "repurposed, reconstructed, overhauled and modernised buildings."),
     "lex_url": "https://gov.uz/ru/uzenergoinspeksiya/news/view/25092",
     "verified_on": VERIFIED_ON},
    # Quyidagi ikkitasi hali manba bilan tasdiqlanmagan — saytda koʻrinmaydi
    {"number": "A–G toifalari", "order": 2, "directions": ["energoaudit"],
     "title_uz": "Bino va inshootlarning energosamaradorlik toifalari",
     "title_ru": "Категории энергоэффективности зданий и сооружений",
     "title_en": "Energy efficiency categories for buildings",
     "applies_to_uz": "Foydalaniladigan maydoni 200 m² dan katta bino va inshootlar",
     "applies_to_ru": "Здания и сооружения с используемой площадью более 200 м²",
     "applies_to_en": "Buildings and structures with a usable area over 200 m²",
     "requirement_uz": "Toifalar shkalasi va chegaralari meʼyoriy hujjatdan olinishi kerak (ЗРУ-940 da shkala yoʻq).",
     "requirement_ru": "Шкала категорий и её границы должны быть взяты из нормативного документа (в Законе № ЗРУ-940 шкалы нет).",
     "requirement_en": "The category scale and its thresholds must be taken from a normative document (ZRU-940 contains no scale).",
     "verified_on": None},
    {"number": "Nazorat oʻlchovi tartibi", "order": 3, "directions": ["olchov-auditi"],
     "title_uz": "Byudjet mablagʻlari hisobidan moliyalashtiriladigan obyektlarda nazorat oʻlchovi oʻtkazish tartibi",
     "title_ru": "Порядок проведения контрольного обмера на объектах, финансируемых из бюджета",
     "title_en": "Procedure for control measurement on budget-funded construction",
     "applies_to_uz": "Byudjet mablagʻlari hisobiga moliyalashtiriladigan qurilish obyektlari",
     "applies_to_ru": "Строительные объекты, финансируемые за счёт бюджетных средств",
     "applies_to_en": "Construction projects financed from the state budget",
     "requirement_uz": "Hujjat raqami, sanasi va talablari lex.uz dan topilishi kerak.",
     "requirement_ru": "Номер, дата и требования документа должны быть сверены с lex.uz.",
     "requirement_en": "The document number, date and requirements must be checked against lex.uz.",
     "verified_on": None},
]

# -------------------------------------------------------------------- posts
POSTS = [
    {"slug": "energoaudit-kimga-majburiy", "published_on": dt.date(2026, 6, 18), "act": "ЗРУ-940", "is_published": True,
     "title_uz": "Energoaudit kimga majburiy", "title_ru": "Кому обязателен энергоаудит",
     "title_en": "Who is required to carry out an energy audit",
     "excerpt_uz": "ЗРУ-940 nimani talab qiladi va davriy audit qanchalik tez-tez oʻtkaziladi.",
     "excerpt_ru": "Что требует Закон № ЗРУ-940 и как часто проводится периодический аудит.",
     "excerpt_en": "What ZRU-940 requires and how often a periodic audit must be carried out.",
     "body_uz": ("Energoaudit majburiy va ixtiyoriy shaklda tashkil etiladi. Davriy energoaudit "
                 "majburiy tartibda besh yilda kamida bir marta oʻtkaziladi (ЗРУ-940).\n\n"
                 "Foydalaniladigan maydoni 200 m² dan katta bino va inshootlar uchun "
                 "energosamaradorlik toifasi belgilanadi.\n\n"
                 "Korxonangizga qaysi talab tegishli ekanini bilmasangiz — soʻrov qoldiring, tekshirib beramiz."),
     "body_ru": ("Энергоаудит организуется в обязательной и добровольной форме. Периодический "
                 "энергоаудит проводится в обязательном порядке не реже одного раза в пять лет "
                 "(Закон № ЗРУ-940).\n\n"
                 "Для зданий и сооружений с используемой площадью более 200 м² определяется "
                 "категория энергоэффективности.\n\n"
                 "Если Вы не знаете, какое требование касается Вашего предприятия, оставьте заявку — мы проверим."),
     "body_en": ("Energy audits are organised as mandatory or voluntary. A periodic energy audit is "
                 "mandatory at least once every five years (ZRU-940).\n\n"
                 "Buildings and structures with a usable area over 200 m² are assigned an energy "
                 "efficiency category.\n\n"
                 "If you are not sure which requirement applies to your enterprise, send a request and we will check.")},
    {"slug": "f2-dalolatnomasi-tekshirish", "published_on": dt.date(2026, 5, 30), "is_published": True,
     "title_uz": "Bajarilgan ishlar dalolatnomasini imzolashdan oldin nimani tekshirish kerak",
     "title_ru": "Что проверить перед подписанием акта выполненных работ",
     "title_en": "What to check before signing a completion act",
     "excerpt_uz": "Eng koʻp uchraydigan nomuvofiqliklar va ularni qanday aniqlash mumkin.",
     "excerpt_ru": "Самые частые расхождения и как их выявить.",
     "excerpt_en": "The most common discrepancies and how to detect them.",
     "body_uz": ("Bajarilgan ishlar dalolatnomasini imzolash — pul toʻlash bilan teng. "
                 "Imzodan keyin daʼvo qilish ancha qiyin.\n\n"
                 "Koʻp uchraydigan holatlar: hajm oshirib yozilishi, material almashtirilishi, "
                 "smeta normalari notoʻgʻri qoʻllanilishi, bir ishning ikki pozitsiyada takrorlanishi.\n\n"
                 "Bularning bir qismi obyektga chiqmasdan, hujjat tahlilida topiladi."),
     "body_ru": ("Подписать акт выполненных работ — всё равно что заплатить. После подписи "
                 "предъявить претензию намного сложнее.\n\n"
                 "Частые случаи: завышенный объём, замена материала, неверно применённые "
                 "сметные нормы, одна работа в двух позициях.\n\n"
                 "Часть из них выявляется без выезда — при анализе документов."),
     "body_en": ("Signing a completion act is as good as paying. Once it is signed, raising a claim "
                 "becomes much harder.\n\n"
                 "Common cases: overstated volumes, substituted materials, misapplied estimate norms, "
                 "the same work listed under two items.\n\n"
                 "Some of these can be found without a site visit, during document review.")},
    {"slug": "energopasport-toifa-nima-beradi", "published_on": dt.date(2026, 4, 22), "act": "A–G toifalari", "is_published": False,
     "title_uz": "Binoning energosamaradorlik toifasi nima beradi",
     "title_ru": "Что даёт категория энергоэффективности здания",
     "title_en": "What a building's energy efficiency category gives",
     "excerpt_uz": "Toifa qanday hisoblanadi va uni qanday oshirish mumkin.",
     "excerpt_ru": "Как рассчитывается категория и как её повысить.",
     "excerpt_en": "How the category is calculated and how it can be improved.",
     "body_uz": "Toifalar shkalasi manba bilan tasdiqlangach yoziladi.",
     "body_ru": "Материал будет подготовлен после подтверждения шкалы категорий источником.",
     "body_en": "This article will be written once the category scale is confirmed by a source."},
    {"slug": "nazorat-olchovi-kim-otkazadi", "published_on": dt.date(2026, 3, 12), "act": "Nazorat oʻlchovi tartibi", "is_published": False,
     "title_uz": "Nazorat oʻlchovini kim oʻtkaza oladi",
     "title_ru": "Кто может проводить контрольный обмер",
     "title_en": "Who may carry out control measurement",
     "excerpt_uz": "Byudjet obyektlarida oʻlchov oʻtkazish uchun qanday talablar bor.",
     "excerpt_ru": "Какие требования предъявляются к контрольному обмеру на бюджетных объектах.",
     "excerpt_en": "What requirements apply to control measurement on budget-funded facilities.",
     "body_uz": "Meʼyoriy hujjat lex.uz bilan tasdiqlangach yoziladi.",
     "body_ru": "Материал будет подготовлен после сверки нормативного документа с lex.uz.",
     "body_en": "This article will be written once the normative document is checked against lex.uz."},
]

SITE = {
    "hero_kicker_uz": "Ekspert tashkiloti · Fargʻona · 1997-yildan",
    "hero_kicker_ru": "Экспертная организация · Фергана · с 1997 года",
    "hero_kicker_en": "Expert organisation · Fergana · since 1997",
    "hero_title_uz": "Energoaudit va qurilishda nazorat oʻlchovi",
    "hero_title_ru": "Энергоаудит и контрольный обмер в строительстве",
    "hero_title_en": "Energy audit and construction control measurement",
    "hero_accent_uz": "", "hero_accent_ru": "", "hero_accent_en": "",
    "seo_title_uz": "Energoaudit va qurilishda nazorat oʻlchovi — TTT Audit, Fargʻona",
    "seo_title_ru": "Энергоаудит и контрольный обмер в строительстве — TTT Audit, Фергана",
    "seo_title_en": "Energy audit and construction control measurement — TTT Audit, Fergana",
    "hero_text_uz": (
        "Majburiy energoaudit va bino energopasporti, bajarilgan ish hajmlarining "
        "nazorat oʻlchovi, loyiha-smeta hujjatlari ekspertizasi va texnik nazorat. "
        "Xulosa davlat organi, bank va sud uchun dalil boʻladi."
    ),
    "hero_text_ru": (
        "Обязательный энергоаудит и энергопаспорт здания, контрольный обмер выполненных "
        "объёмов работ, экспертиза проектно-сметной документации и технический надзор. "
        "Заключение служит доказательством для госоргана, банка и суда."
    ),
    "hero_text_en": (
        "Mandatory energy audit and building energy passport, control measurement of "
        "completed construction work, design-estimate expertise and technical supervision. "
        "Our report is evidence for state bodies, banks and courts."
    ),
    "about_uz": (
        "Ekspert tashkiloti Oʻzbekiston Respublikasida 1997-yil 12-martdan rasman faoliyat "
        "yuritadi. Tashkilot Oʻzbekiston muhandis-konsultantlar uyushmasi (UZACE) aʼzosi "
        "sifatida energoaudit va nazorat oʻlchovi sohasida ishlaydi.\n\n"
        "Bugun tashkilotda 50 xodim ishlaydi: 24 nafari energoaudit va energosamaradorlik "
        "boʻyicha, 16 nafari texnik nazorat boʻyicha mutaxassis. Menejment tizimi "
        "ISO 9001:2015, ISO 45001:2018 va ISO 27001:2022 boʻyicha sertifikatlangan.\n\n"
        "Kasbiy faoliyat «Imkon-sugʻurta» AJ tomonidan 10 000 000 000 soʻmga sugʻurtalangan."
    ),
    "about_ru": (
        "Экспертная организация официально действует в Республике Узбекистан с 12 марта "
        "1997 года и является членом Ассоциации инженеров-консультантов Узбекистана (UZACE) "
        "в области энергоаудита и контрольного обмера.\n\n"
        "В организации работает 50 человек: 24 специалиста по энергоаудиту и "
        "энергоэффективности и 16 специалистов по техническому надзору. Система менеджмента "
        "сертифицирована по ISO 9001:2015, ISO 45001:2018 и ISO 27001:2022.\n\n"
        "Профессиональная деятельность застрахована АО «Imkon-sug’urta» на сумму "
        "10 000 000 000 сум."
    ),
    "about_en": (
        "The expert organisation has operated in Uzbekistan since 12 March 1997 and is a "
        "member of the Association of Consulting Engineers of Uzbekistan (UZACE) for energy "
        "audit and control measurement.\n\n"
        "Staff of 50: 24 energy audit and efficiency specialists and 16 technical "
        "supervision specialists. Management system certified to ISO 9001:2015, "
        "ISO 45001:2018 and ISO 27001:2022.\n\n"
        "Professional liability insured by Imkon-sug'urta JSC for UZS 10,000,000,000."
    ),
}


class Command(BaseCommand):
    help = "Tahririy kontent (yoʻnalish, xizmat, hujjat, maqola). Boʻsh bazani toʻldiradi."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force", action="store_true",
            help="Mavjud yozuvlarni shu fayldagi matn bilan yangilash (admin tahrirlari yoʻqoladi).",
        )

    def handle(self, *args, **options):
        if Direction.objects.exists() and not options["force"]:
            # Konsol xabarlari ASCII: Windows konsoli (cp1251) oʻ/gʻ ni chiqara olmaydi
            self.stdout.write("Kontent allaqachon bor - otkazib yuborildi (--force bilan yangilanadi).")
            return

        self._site()
        directions = self._directions()
        services = self._services(directions)
        self._acts(directions)
        self._posts()

        self.stdout.write(self.style.SUCCESS(
            f"Kontent: {Direction.objects.count()} yonalish / {Service.objects.count()} xizmat / "
            f"{LegalAct.objects.count()} hujjat "
            f"({LegalAct.objects.filter(verified_on__isnull=False).count()} tekshirilgan) / "
            f"{Post.objects.filter(is_published=True).count()} maqola"
        ))

    def _site(self) -> None:
        site = SiteSettings.load()
        for field, value in SITE.items():
            setattr(site, field, value)
        site.save()

    def _directions(self) -> dict:
        directions = {}
        for payload in DIRECTIONS:
            data = dict(payload)
            slug = data.pop("slug")
            directions[slug], _ = Direction.objects.update_or_create(slug=slug, defaults=data)
        return directions

    def _services(self, directions: dict) -> dict:
        services = {}
        for direction_slug, items in SERVICES.items():
            for order, payload in enumerate(items):
                data = dict(payload)
                slug = data.pop("slug")
                services[slug], _ = Service.objects.update_or_create(
                    direction=directions[direction_slug], slug=slug,
                    defaults={**data, "order": order},
                )
        return services

    def _acts(self, directions: dict) -> None:
        for payload in ACTS:
            data = dict(payload)
            number = data.pop("number")
            linked = data.pop("directions", [])
            obj, _ = LegalAct.objects.update_or_create(number=number, defaults=data)
            obj.directions.set([directions[d] for d in linked if d in directions])

    def _posts(self) -> None:
        acts = {a.number: a for a in LegalAct.objects.all()}
        for payload in POSTS:
            data = dict(payload)
            slug = data.pop("slug")
            act_number = data.pop("act", None)
            Post.objects.update_or_create(slug=slug, defaults={**data, "legal_act": acts.get(act_number)})
