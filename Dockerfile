# Dockerfile para Django - Sistema de Notas Técnicas
FROM python:3.14.2-slim

# Evita buffering de logs Python
ENV PYTHONUNBUFFERED=1

# Evita problemas com apt-get
ENV DEBIAN_FRONTEND=noninteractive
ENV APT_KEY_DONT_WARN_ON_DANGEROUS_USAGE=1

# Diretório de trabalho no container
WORKDIR /app

# Cria diretórios do apt-get e configura para evitar erros de limpeza
RUN mkdir -p /var/cache/apt/archives/partial && \
    echo 'APT::Update::Post-Invoke-Success { "touch /var/lib/apt/periodic/update-success-stamp 2>/dev/null || true"; };' > /etc/apt/apt.conf.d/99-custom

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
