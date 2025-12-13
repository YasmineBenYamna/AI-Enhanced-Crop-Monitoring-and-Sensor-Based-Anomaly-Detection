#!/bin/bash
set -e

echo "=========================================="
echo "Starting Django Application"
echo "=========================================="

# Wait for database
/app/scripts/wait-for-db.sh

# Run migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Create superuser if doesn't exist
echo "Creating superuser..."
python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='admin123'
    )
    print('Superuser created: admin/admin123')
else:
    print('Superuser already exists')
END

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput || true

# Start Django server
echo "Starting Django server on 0.0.0.0:8000..."
python manage.py runserver 0.0.0.0:8000