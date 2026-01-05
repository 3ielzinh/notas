#!/bin/bash
set -e

echo "Aguardando PostgreSQL estar disponível..."
until python -c "import psycopg; psycopg.connect('host=${DB_HOST:-db} port=${DB_PORT:-5432} user=${DB_USER:-postgres} password=${DB_PASSWORD} dbname=${DB_NAME:-django_notas}').close()" 2>/dev/null; do
    echo "Aguardando conexão com banco..."
    sleep 2
done

echo "PostgreSQL disponível! Aplicando migrações..."
python manage.py migrate --noinput

echo "Coletando arquivos estáticos..."
python manage.py collectstatic --noinput --clear || true

echo "Iniciando aplicação..."
exec "$@"
