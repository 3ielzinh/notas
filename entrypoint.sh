#!/bin/bash
set -e

echo "Aguardando PostgreSQL estar disponível..."
while ! pg_isready -h db -p 5432 -U ${DB_USER:-postgres} > /dev/null 2>&1; do
    sleep 1
done

echo "PostgreSQL disponível! Aplicando migrações..."
python manage.py migrate --noinput

echo "Coletando arquivos estáticos..."
python manage.py collectstatic --noinput

echo "Iniciando aplicação..."
exec "$@"
