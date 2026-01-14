# 🚀 Инструкция по деплою (Production Guide)

Этот документ описывает, как развернуть проект **Абак маркет** (Grocery Store) в продакшн-среду (Render, Railway, VPS).

---

## 🛠️ Переменные окружения (`.env`)

Для работы проекта в продакшне необходимо задать следующие переменные.
**ВАЖНО:** Никогда не коммите файл `.env` в репозиторий!

```ini
# --- Основные настройки ---
DEBUG=False
SECRET_KEY=сложный-случайный-ключ
ALLOWED_HOSTS=your-domain.com,app-name.onrender.com

# --- База данных (PostgreSQL) ---
# Пример для Render (Internal URL) или VPS
DATABASE_URL=postgres://user:password@host:5432/dbname

# --- Redis (Кэш и Celery) ---
REDIS_URL=redis://redis:6379/0

# --- Настройки безопасности (ОБЯЗАТЕЛЬНО для HTTPS) ---
CSRF_TRUSTED_ORIGINS=https://your-domain.com,https://app-name.onrender.com

# --- Специфично для проекта ---
COMPANY_NAME="Абак маркет"
WHATSAPP_API_TOKEN=ваш_токен
# Остальные настройки см. в .env.example
```

---

## ☁️ Вариант 1: Деплой на Render.com (Рекомендуется)

Самый простой способ. Бесплатного тарифа хватит для старта.

1.  **Создайте PostgreSQL базу** на Render dashboard.
    *   Скопируйте `Internal Database URL`.
2.  **Создайте Web Service**:
    *   Подключите ваш GitHub репозиторий.
    *   **Runtime:** Python 3
    *   **Build Command:** `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
    *   **Start Command:** `gunicorn config.wsgi:application`
3.  **Настройте Environment Variables**:
    *   Добавьте `DATABASE_URL` (вставьте скопированный URL).
    *   Добавьте `SECRET_KEY`.
    *   `DEBUG = False`.
    *   `PYTHON_VERSION = 3.11.0` (или ваша версия).

---

## 🐧 Вариант 2: Деплой на VPS (Ubuntu 22.04 + Nginx + Gunicorn)

Для полного контроля над сервером.

### 1. Подготовка сервера
```bash
sudo apt update
sudo apt install python3-pip python3-venv python3-dev libpq-dev postgresql postgresql-contrib nginx
```

### 2. Создание БД и Пользователя
```bash
sudo -u postgres psql
CREATE DATABASE abak_market;
CREATE USER abak_user WITH PASSWORD 'password123';
ALTER ROLE abak_user SET client_encoding TO 'utf8';
ALTER ROLE abak_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE abak_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE abak_market TO abak_user;
\q
```

### 3. Настройка проекта
```bash
git clone https://github.com/your-username/grocery-store.git /var/www/abak
cd /var/www/abak
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Отредактируйте .env (DATABASE_URL=postgres://abak_user:password123@localhost/abak_market)
python manage.py collectstatic
python manage.py migrate
```

### 4. Настройка Gunicorn (Systemd)
Создайте файл `/etc/systemd/system/abak.service`:
```ini
[Unit]
Description=gunicorn daemon
After=network.target

[Service]
User=root
Group=www-data
WorkingDirectory=/var/www/abak
ExecStart=/var/www/abak/venv/bin/gunicorn --access-logfile - --workers 3 --bind unix:/var/www/abak/abak.sock config.wsgi:application

[Install]
WantedBy=multi-user.target
```
Запуск:
```bash
sudo systemctl start abak
sudo systemctl enable abak
```

### 5. Настройка Nginx
Создайте файл `/etc/nginx/sites-available/abak`:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        root /var/www/abak/staticfiles;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/abak/abak.sock;
    }
}
```
Активация:
```bash
sudo ln -s /etc/nginx/sites-available/abak /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

---

## 🏥 Health Check

Для проверки работоспособности (например, в Kubernetes или Docker Swarm) доступен эндпоинт:

`GET /health/`

Ответ:
```json
{"status": "healthy", "checks": {"database": "ok", "cache": "ok"}}
```

---

## 🐳 Docker Deployment

Просто запустите:
```bash
docker-compose up --build -d
```
Не забудьте настроить `.env` перед запуском!
