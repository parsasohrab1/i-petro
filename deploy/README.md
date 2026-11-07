# راه‌اندازی iPetro روی VPS ایرانی (PostgreSQL + API + ورود با رمز)

این پوشه داشبورد iPetro را بدون وابستگی به claude.ai اجرا می‌کند: صفحه‌ی `platform/index.html` همان است که هست؛ فایل `server/shim.js` رابط `window.claude` (پایگاه داده، کاربر، فایل، دانلود) را به API همین سرور وصل می‌کند.

## ساختار
```
nginx (TLS، پورت 80/443)  ->  app (FastAPI، فقط داخل شبکه)  ->  db (PostgreSQL 16، فقط داخل شبکه)
```
فقط nginx به بیرون باز است. PostgreSQL و API هیچ پورتی روی اینترنت ندارند.

## حداقل سرور
۴ vCPU، ۱۶ گیگ RAM، ۲۰۰ گیگ SSD، Ubuntu 22.04/24.04. برای این بخش (iPetro به‌تنهایی) ۲ vCPU و ۴ گیگ هم کافی است.

## ۱) آماده‌سازی سرور
```bash
sudo apt update && sudo apt install -y docker.io docker-compose-v2 rsync
sudo ufw allow 22/tcp && sudo ufw allow 80/tcp && sudo ufw allow 443/tcp && sudo ufw enable
```
اگر از داخل ایران به مخزن‌های Docker دسترسی نبود، از آینه‌ی (mirror) ارائه‌دهنده‌ی سرور استفاده کنید یا ایمیج‌ها را از یک ماشین دیگر با `docker save | docker load` منتقل کنید.

## ۲) انتقال کد
گیت‌هاب از ایران ممکن است باز نشود؛ از رایانه‌ای که دسترسی دارد منتقل کنید:
```bash
rsync -a --exclude .git ./ user@SERVER:/opt/ipetro/
```

## ۳) تنظیمات
```bash
cd /opt/ipetro/deploy
cp .env.example .env
nano .env        # DOMAIN و POSTGRES_PASSWORD (طولانی و تصادفی) را پر کنید
mkdir certs      # fullchain.pem و privkey.pem گواهی دامنه را اینجا بگذارید
```
دامنه (A record) باید به IP سرور اشاره کند. گواهی را می‌توانید با certbot (`certbot certonly --standalone -d دامنه`) بگیرید یا گواهی تجاری بگذارید.

## ۴) اجرا
```bash
docker compose up -d --build
docker compose ps            # db و app و nginx باید Up باشند
curl -k https://localhost/healthz
```

## ۵) ساخت مالک و اعضا
```bash
docker compose exec app python -m server.manage create-user --email owner@شرکت.ir --name "نام مالک" --role owner --id owner
docker compose exec app python -m server.manage create-user --email ali@شرکت.ir --name "علی" --role member --id <شناسه‌ی عضو>
docker compose exec app python -m server.manage list-users
```
- نقش‌ها: `owner` (مالک: همه‌چیز، از جمله گزارش‌ها و پاسخ‌های ذهن‌نگار)، `admin` (برابر «ویرایشگر» قبلی)، `member`.
- رمز حداقل ۱۰ کاراکتر است. فراموشی رمز: `set-password --email ...`.
- **شناسه‌ی کاربر (`--id`) باید با شناسه‌ی عضو در داده برابر باشد.** پس از انتقال داده با `list-members` شناسه‌ها را ببینید و برای هر عضو همان را بدهید.

## ۶) انتقال داده‌ی فعلی
۱. در داشبورد فعلی (claude.ai) از «ERP ← پشتیبان‌گیری» فایل JSON کامل را دانلود کنید (`ppt-backup-....json`).
۲. فایل را روی سرور بگذارید و وارد کنید:
```bash
docker compose cp ppt-backup-2026-10-31.json app:/tmp/b.json
docker compose exec app python -m server.manage import-backup /tmp/b.json
docker compose exec app python -m server.manage list-members
```
۳. برای داده‌ی بازار (مناقصه‌ها، رویدادها، سرمایه‌گذاران …) که ایجنت می‌سازد: روی رایانه‌ای که مخزن و `pip install -r requirements.txt` دارد این را بزنید: `python -c "from agent import platform_sync as p; print(p.export(include_seed=True))"` (پوشه‌ی `data/platform_export` ساخته می‌شود). آن پوشه را روی سرور بگذارید و `import-export data/platform_export/manifest.json` را داخل کانتینر اجرا کنید.
۴. فایل‌های بارگذاری‌شده‌ی قبلی (امضا، اثر انگشت، سربرگ، مدارک) در پشتیبان JSON نیستند؛ باید یک بار دوباره بارگذاری شوند.

## ۷) پشتیبان‌گیری
```bash
sudo crontab -e
15 2 * * *  REMOTE=user@سرور-دوم:/backups /opt/ipetro/deploy/backup.sh
```
پشتیبان روی همان سرور فقط در برابر خطای نرم‌افزاری کمک می‌کند؛ حتماً `REMOTE` را روی یک ماشین دیگر بگذارید. بازیابی: `gunzip -c فایل.sql.gz | docker compose exec -T db psql -U ipetro ipetro`.

## ۸) به‌روزرسانی
کد جدید را دوباره `rsync` کنید و `docker compose up -d --build` بزنید. داده در حجم `pgdata` می‌ماند.

## کنترل دسترسی (سمت سرور)
| مسیر | چه کسی می‌خواند / می‌نویسد |
|---|---|
| `reports/*`، `mindtest/*` | فقط خود فرد؛ خواندن را مالک هم دارد؛ هیچ‌کس برای دیگری نمی‌نویسد |
| `attendance/*` | خود فرد و مدیران |
| `members`، `tasks` | مدیران همه؛ عضو فقط رکورد خودش / تسک‌های مربوط به خودش |
| `finance`، `clients` (از جمله حساب‌های سامانه‌ی ثبت) | فقط مدیران |
| `scholarships`، `settings/scholar` | فقط مالک |
| `settings/*` | خواندن همه؛ نوشتن مدیران |
| بقیه (بازار، پیگیری، نامه‌ها …) | هر کاربر واردشده |
این جدول در `server/rules.py` است و با `tests/test_server.py` تست می‌شود. نامه‌ها (`letters`) برای همه‌ی کاربران واردشده خوانا است؛ اگر باید به دفتر محدود شود، قانون آن را به `rules.py` اضافه کنید.

## محدودیت‌ها
- **نمره‌دهی خودکار گزارش‌ها با Claude کار نمی‌کند**؛ `api.anthropic.com` از ایران در دسترس نیست و این قابلیت در این نسخه خاموش است.
- فونت Vazirmatn از Google Fonts و نقشه‌ی دفتر (Leaflet/OpenStreetMap) از CDN بیرونی می‌آیند؛ اگر فیلتر باشند، صفحه با فونت جایگزین باز می‌شود و نقشه‌ی انتخاب دفتر کار نمی‌کند (مختصات را دستی وارد کنید). برای رفع کامل، فایل‌ها را روی خود سرور میزبانی کنید.
- API با **یک worker** اجرا می‌شود (به‌روزرسانی زنده درون‌پردازشی است). برای چند سرور باید LISTEN/NOTIFY اضافه شود.
- ورود فقط با ایمیل و رمز است؛ احراز دومرحله‌ای ندارد.
