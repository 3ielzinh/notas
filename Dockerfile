# Dockerfile para Django - Sistema de Notas Técnicas
FROM python:3.14.2-slim

# Evita buffering de logs Python
ENV PYTHONUNBUFFERED=1

# Diretório de trabalho no container
WORKDIR /app

# Instala dependências do sistema para PostgreSQL e PDF
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    postgresql-client \
    libpq-dev \
    gcc \
    g++ \
    make \
    cmake && \
    rm -rf /var/lib/apt/lists/*

# Copia requirements e instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia código da aplicação
COPY . .

# Cria diretórios necessários
RUN mkdir -p /app/staticfiles /app/data/backups

# Coleta arquivos estáticos
RUN python manage.py collectstatic --noinput || true

# Expõe porta 8000
EXPOSE 8000

# Script de inicialização
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
