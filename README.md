# TTT Audit — sayt (tttaudit.uz)

Energoaudit va qurilishda nazorat oʻlchovi boʻyicha ekspert tashkilotining rasmiy sayti.
Django 5.2 SSR + React vidjetlari (Vite). Uch til: /uz/ /ru/ /en/.

## Lokal ishga tushirish

```bash
python -m venv .venv && source .venv/Scripts/activate   # Git Bash (Windows)
pip install -r backend/requirements-dev.txt
cd backend
python manage.py migrate
python manage.py seed_content        # tahririy kontent (yoʻnalish, xizmat, qonun, maqola)
python manage.py import_tttaudit     # mijoz faktlari: hujjatlar, direktor + 38 mutaxassis, 46 sertifikat, 143 loyiha
python manage.py sync_site_content   # admin uchun «Sayt matnlari» roʻyxati va standart slaydlar
python manage.py createsuperuser
cd ../frontend && npm install && npm run build && cd ../backend
python manage.py runserver
```
Sayt: http://127.0.0.1:8000/uz/ · Admin: /admin/ · Testlar (`backend/` ichida): `pytest -q --cov=core`

Testlardan oldin har doim repo ildizida `cd frontend && npm run build` bajaring — testlardan biri
(`backend/core/tests/test_widgets_build.py`) yigʻilgan `backend/frontend/dist/widgets/widgets.js` faylini tekshiradi.

## Tuzilma
- `backend/core/models.py` — kontent modellari (`_uz/_ru/_en` maydonlar, `{{ obj|tr:"title" }}`).
- `backend/core/compliance.py`, `backend/core/energy.py` — talab qoidalari va A–G chegaralari (server va React uchun yagona manba).
  `energy.BANDS_VERIFIED = False` — A–G chegaralari oʻrinbosar, shuning uchun toifa API, talab tekshiruvi va sahifada
  koʻrsatilmaydi (faqat solishtirma isteʼmol va energopasport talabi). Meʼyoriy hujjat tasdiqlangach `True`.
- `backend/core/media.py` — ommaviy media va murojaat fayllarini xodimga berish; `backend/core/middleware.py` — soʻrov hajmi chegarasi.
- `backend/core/templates/core/` — sahifalar; `backend/core/static/core/css/site.css` — dizayn tizimi.
- `frontend/src/` — uchta React vidjet; `npm run build` → `backend/frontend/dist/widgets/`.
- `backend/data/tttaudit/` — nashr uchun tayyorlangan JSON va ommaviy media (38 mutaxassis — 24 energetika / 14 qurilish,
  143 loyiha, 8 hujjat/sertifikat).
- `backend/tools/prepare_logo.py` — `logo/` dagi PNG'dan sayt logotiplari (natija allaqachon commit qilingan; bu skript
  faqat logotip qayta yasalganda kerak, konteynerda ishlamaydi).

## Tarjima
Interfeys satrlari (`backend/` ichida): `python manage.py maketranslations --report` (faqat oʻqish, hech narsa yozmaydi) →
`backend/locale/translations.json` ni tahrirlash → `python manage.py maketranslations` (yozadi).
Oʻzbekcha interfeys matnini tahrirlagandan keyin shu buyruqni ishga tushirish va `frontend/src/i18n.js`
(vidjet matnlari, qoʻlda `backend/locale/translations.json` bilan sinxron tutiladi) ni ham yangilash shart.

## Admin panel: saytdagi hamma narsa
- **Kontent** — yoʻnalish, xizmat, qonun, yangilik, loyiha (+ xaritadagi joy), jamoa (+ sertifikat skanlari),
  hujjat, asbob, mijoz, raqamlar, ofis, murojaatlar. Har bir matn maydoni uz/ru/en.
- **Sayt sozlamalari** — rekvizitlar, geroy bloki, kompaniya sahifasi, **brend rasmlari** (logotip, oq logotip,
  favicon, OG surat; boʻsh boʻlsa `static/core/img/` dagi standart fayl).
- **Bosh sahifa slaydlari** — surat, yorliq, izoh, alt, kadr markazi, tartib, koʻrsatish/yashirish.
- **Sayt matnlari** — shablon va vidjetlardagi *barcha* interfeys satrlari (sarlavhalar, tugmalar, forma
  yozuvlari). Boʻsh maydon — standart tarjima; toʻldirilgani darhol (≤5 soniyada, barcha worker'larda) chiqadi.
  `%(n)s` / `{n}` oʻrinbosarlari saqlanishi shart — forma tekshiradi. Roʻyxat `sync_site_content` bilan
  shablonlardan yangilanadi (yangi satr qoʻshilsa — qoʻshiladi, olib tashlangani — tahrirlanmagan boʻlsa oʻchadi).
  Mexanizm: `backend/core/sitetext.py` (`gettext` ustidan qayta yozuv, `SiteTextMiddleware`).
- Kodda qoladi: sahifa tuzilmasi/dizayn, bosh sahifadagi vedomost *namunasidagi* raqamlar (`backend/core/home.py`,
  qator nomlari «Sayt matnlari» da tahrirlanadi), energiya chegaralari (`backend/core/energy.py`).

## Railway'ga deploy
1. GitHub repo'dan yangi loyiha → servis Dockerfile orqali yigʻiladi (`railway.json`: healthcheck `/healthz`).
2. **PostgreSQL** qoʻshing; servis oʻzgaruvchisi `DATABASE_URL=${{Postgres.DATABASE_URL}}`.
3. **Volume** qoʻshing, mount path: `/app/media` (yuklangan rasmlar, skanlar, murojaat fayllari; usiz har
   deploy'da yoʻqoladi). Egasini `docker-entrypoint.sh` oʻzi toʻgʻrilaydi.
4. Oʻzgaruvchilar (qolganlari `.env.example` da):
   - `DJANGO_SECRET_KEY` — uzun tasodifiy qiymat (`python -c "import secrets;print(secrets.token_urlsafe(50))"`)
   - `DJANGO_ALLOWED_HOSTS=tttaudit.uz,www.tttaudit.uz` va `DJANGO_CSRF_TRUSTED_ORIGINS=https://tttaudit.uz,https://www.tttaudit.uz`
     (`*.up.railway.app` domeni avtomatik qoʻshiladi — `RAILWAY_PUBLIC_DOMAIN`)
   - `SITE_URL=https://tttaudit.uz`, `TRUST_X_REAL_IP=1`, ixtiyoriy `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`,
     `WEB_CONCURRENCY` (gunicorn worker soni, standart 3)
5. Birinchi deploy'dan keyin admin: Railway servis → *Shell* (yoki `railway ssh`) →
   `python manage.py createsuperuser`.
6. Domen: Settings → Networking → Custom Domain → DNS'da CNAME. HTTPS ishlashi tasdiqlangach `DJANGO_HSTS_SECONDS`.

Har ishga tushishda (`docker-entrypoint.sh`): `migrate` → `createcachetable` → `seed_content` →
`import_tttaudit` → `sync_site_content` → gunicorn. Hammasi takroriy ishga tushishda admin tahrirlarini saqlaydi.

## Prod
`.env.example` → muhit oʻzgaruvchilari. `Dockerfile` gunicorn + whitenoise. PostgreSQL `DATABASE_URL`.
Murojaat chegarasi cache orqali: prodda `DatabaseCache` (`createcachetable` CMD da), lokal/testda `LocMemCache`.
Telegram: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.
Ilova root boʻlmagan `app` foydalanuvchisi bilan ishlaydi; `docker-entrypoint.sh` media volume egasini oʻzi toʻgʻrilaydi.

### Boshlangʻich maʼlumot buyruqlari (CMD da har ishga tushishda)
- `seed_content` (flagsiz) — bazada kamida bitta yoʻnalish boʻlsa **hech narsa qilmaydi**, shuning uchun admin
  tahrirlarini oʻchirmaydi va CMD da qolishi xavfsiz. `seed_content --force` esa `SiteSettings` geroy/kompaniya
  matnlarini, yoʻnalish, xizmat, qonun va maqolalarni (slug/raqam boʻyicha) fayldagi matn bilan **qayta yozadi** —
  admin paneldagi shu maydonlardagi tahrirlar yoʻqoladi (admin qoʻshgan yangi yozuvlar qoladi).
- `import_tttaudit` (flagsiz) — maʼlumoti bor jadvallarni (ofis, hujjat, asbob, raqam, xodim, xodim sertifikati,
  loyiha, mijoz) oʻtkazib yuboradi. `SiteSettings` rekvizitlaridan (nom, STIR, telefon, e-pochta, rahbar, manzil,
  xodimlar soni) faqat boʻsh yoki model standart qiymatida qolganlarini `facts.json` dan toʻldiradi — admin panelda
  tahrirlangan rekvizit saqlanadi, shuning uchun CMD da qolishi xavfsiz. `--force` jadvallarni fayllari bilan birga
  qayta yaratadi (eski suratlar/skanlar oʻchiriladi, `media/team/` oʻsmaydi) va rekvizitlarni fayldagi qiymatga qaytaradi.

### Prod: muhim
- **`DJANGO_DEBUG=0` va haqiqiy `DJANGO_SECRET_KEY` majburiy.** `DEBUG=0` da maxfiy kalit berilmasa (yoki dev
  kaliti qolsa) sayt `ImproperlyConfigured` bilan ishga tushmaydi. Docker build'dagi `collectstatic`
  `DJANGO_SECRET_KEY=build-only` bilan ishlaydi.
- **Media fayllar.** `/media/` ostida faqat `settings.PUBLIC_MEDIA_PREFIXES` papkalari (`credentials/`, `team/`,
  `instruments/`, `projects/`, `directions/`, `hero/`) ilovaning oʻzi tomonidan xizmat qilinadi — DEBUG va prodda
  bir xil. `leads/` (mijoz yuklagan fayllar) hech qachon ommaga ochiq emas: admin paneldagi murojaat sahifasida
  «Yuklab olish» havolasi (`/admin-files/lead/<id>/`, faqat `is_staff`) orqali olinadi. Prodda shu prefikslar
  uchun teskari proksida alias (masalan nginx `location /media/credentials/ { alias ...; }`) tezroq, lekin
  ilova usiz ham ishlaydi. `leads/` uchun alias **qoʻymang**.
- **Soʻrov hajmi.** `MaxBodySizeMiddleware` `Content-Length` > `MAX_REQUEST_BODY_BYTES` (fayl chegarasi + 2 MB)
  boʻlsa CSRF va forma tahlilidan oldin 413 qaytaradi. Proksida ham cheklash foydali, masalan nginx'da
  `client_max_body_size 30m;`.
- **HSTS.** `DJANGO_HSTS_SECONDS` (standart `3600`), `DJANGO_HSTS_INCLUDE_SUBDOMAINS` va `DJANGO_HSTS_PRELOAD`
  (standart `0`). Domen (va subdomenlar) faqat HTTPS orqali ishlashi tasdiqlangandan keyingina `31536000` ga
  koʻtaring — HSTS brauzerlarda keshlanadi va orqaga qaytarish qiyin.
- **Murojaat chegarasi va baza.** `DATABASE_URL` boʻlmasa (SQLite) cache `LocMemCache` — chegara hisoblagichi har
  gunicorn worker'da alohida (amalda `LEAD_RATE_LIMIT × workers`). Prodda PostgreSQL (`DATABASE_URL`) ishlating:
  shunda `DatabaseCache` umumiy.
- **`TRUST_X_REAL_IP=1` ni faqat** `X-Real-IP` sarlavhasini **oʻzi qayta yozadigan** teskari proksi ortida
  yoqing (Railway, toʻgʻri sozlangan nginx). Aks holda barcha tashrif buyuruvchilar bitta chegara
  hisoblagichini (`LEAD_RATE_LIMIT`) baham koʻradi, yoki sarlavha soxtalashtirilib chegara chetlab oʻtiladi.
- **`media/` uchun doimiy volume** biriktiring — kredential skanlari, xodim suratlari, murojaat qildirilgan
  fayllar shu yerda saqlanadi; konteyner qayta yaratilganda yoʻqolmasligi kerak.
- **`seed_content --force` ni prodda ishga tushirmang** — mijoz admin panelda tahrirlagan matnlar qayta yoziladi
  (yuqoridagi boʻlim).
- Oʻzbekcha interfeys matnini oʻzgartirgandan keyin `python manage.py maketranslations` ishga tushiring va
  `frontend/src/i18n.js` ni qoʻlda sinxron tutib boring (vidjet matnlari tarjima faylidan avtomatik olinmaydi).
- Testlardan oldin repo ildizida `cd frontend && npm run build` bajaring — bitta test yigʻilgan bundlni tekshiradi.

## Kontent qoidalari
Faqat energoaudit va qurilishda nazorat oʻlchovi. Manbasiz raqam yoʻq. Qonun faqat `verified_on` bilan chiqadi.

## Mijoz tasdiqlashi kerak
- Davlat energetika reestri chegaralari: 4 000 000 kVt·soat elektr / 375 000 m³ gaz (VM qarori № 690 asosida,
  saytda koʻrsatiladi) — raqamlarni mijoz tasdiqlasin.
- Nazorat oʻlchovi xizmat haqi chegarasi 0,3% — asos hujjat tasdiqlanmagan, saytdan olib tashlangan
  (`compliance.MEASUREMENT_FEE_CAP` ishlatilmaydi).
- A–G energosamaradorlik toifalari chegaralari — yashirin (`energy.BANDS_VERIFIED = False`).
- Mijozlar roʻyxati (`clients.json`, eski moliyaviy audit saytidan) — «Buyurtmachilar orasida» boʻlimi olib tashlangan.
- Loyihalar joylashuvi (`backend/data/tttaudit/project_locations.json`) ish nomi va buyurtmachi matnidan aniqlangan. Joyi
  matnda aniq (`high`) boʻlganlari xaritada; taxminiylari (`medium`, masalan nomida shahar boʻlgan kompaniya) yashirin —
  mijoz tasdiqlasa admin panelda «Loyihalar joyi» → `is_public`. Xorijdagi 2 ish faqat reestrda.
- Ofis koordinatasi (Yandex: 40.406844, 71.782245) — prodda eski qiymat qolgan boʻlsa admin panelda yoki
  `import_tttaudit --force` bilan yangilanadi (flagsiz import tahrirlangan rekvizitga tegmaydi).
- Loyiha nomlari ingliz tilida — hozir /en/ da oʻzbekcha chiqadi.
- Mutaxassislar sertifikatlari ru/en tarjimasi — hozir oʻzbekcha.
- Asosiy e-pochta manzili.
- Ism transliteratsiyalari (`import_tttaudit.STAFF_LATIN_NAMES`: Zuhriddinov T. D., Ergashev Sh. R.).
- Xodimlar soni: byulletendagi 50 / 24 / 16 va roʻyxatdagi 38 mutaxassis (takror birlashtirilgach) farqi.
- Direktor tarjimai holi faqat muhandislik tarixiga qisqartirilgan (`import_tttaudit.DIRECTOR`: maʼlumoti va
  1979–1995 ish joylari, 1997-yildan bosh direktor) — eski saytdagi moliyaviy audit qatorlari chiqarilmagan; tasdiqlasin.
- Direktor surati (`img/team/kZeWGs8BiqT2DLVxMvDS.jpg`) 133×200 — sifatliroq portret kerak.
- Xodim sertifikatlari skanlari (`staff_certificates.json`): 45 ta «high», 1 ta «medium» (Ergashboev — sertifikatda
  «Inomjon»); ism tuzatishi `STAFF_NAME_FIXES` (Tuxlibayev Ulugʻbek Soyibovich).
