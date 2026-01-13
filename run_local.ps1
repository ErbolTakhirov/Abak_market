# Script to run the project locally without Docker
$ErrorActionPreference = "Stop"

Write-Host ">>> Checking Virtual Environment..."
if (-not (Test-Path "venv")) {
    Write-Host ">>> Creating venv..."
    python -m venv venv
}

Write-Host ">>> Activating venv..."
& ".\venv\Scripts\Activate.ps1"

Write-Host ">>> Installing dependencies..."
pip install -r requirements.txt

# Set local development environment variables
$env:USE_SQLITE = "True"
$env:DEBUG = "True"
# Ensure we don't try to use Docker hostnames if they are set in .env
$env:DATABASE_HOST = "localhost" 
$env:REDIS_URL = "redis://localhost:6379/0" 

Write-Host ">>> Applying Migrations (SQLite)..."
python manage.py migrate

Write-Host ">>> Creating Superuser (if needed)..."
# Verify if superuser exists or just prompt user to create one if they want
# python manage.py createsuperuser 
# (Skipping automatic creation to avoid interaction hang, user can run manually)

Write-Host ">>> Starting Server..."
Write-Host ">>> Access at http://127.0.0.1:8000"
python manage.py runserver
