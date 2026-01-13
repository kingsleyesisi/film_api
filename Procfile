release: python manage.py migrate
web: gunicorn starwars_api.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --timeout 60
