# Как запустить проект локально (без Docker)

Я добавил специальный режим для локального запуска через SQLite, чтобы не нужно было поднимать базу данных PostgreSQL и Redis.


### Настройка AI (Grok и Whisper)
В `.env` файле я уже настроил использование **Grok** (через ключ `OPENAI_API_KEY`) и локального **Whisper**.

**Важно для Whisper:**
Для работы локального распознавания речи нужно установить **FFmpeg**:
1. Скачайте [FFmpeg](https://ffmpeg.org/download.html) (или `choco install ffmpeg` если есть Chocolatey).
2. Добавьте его в PATH.

Если FFmpeg не установлен, сервер запустится, но при попытке обработать голосовое будет ошибка.

### Способ 1: Автоматический (рекомендуется)
Просто запустите скрипт `run_local.ps1` в PowerShell:
```powershell
.\run_local.ps1
```
Он сам создаст `venv`, установит библиотеки, применит миграции и запустит сервер.

### Способ 2: Вручную
Если хотите сделать все сами, выполните эти команды по очереди:

1. **Создайте виртуальное окружение:**
   ```bash
   python -m venv venv
   ```

2. **Активируйте его:**
   ```powershell
   .\venv\Scripts\Activate
   ```

3. **Установите зависимости:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Примените миграции (с флагом для локальной БД):**
   *Важно: для локального запуска без Docker мы используем переменную `USE_SQLITE=True`*
   ```powershell
   $env:USE_SQLITE="True"; python manage.py migrate
   ```

5. **Создайте суперпользователя (для админки):**
   ```powershell
   $env:USE_SQLITE="True"; python manage.py createsuperuser
   ```

6. **Запустите сервер:**
   ```powershell
   $env:USE_SQLITE="True"; python manage.py runserver
   ```

После запуска сайт будет доступен по адресу: `http://127.0.0.1:8000`
Админка: `http://127.0.0.1:8000/admin/`
