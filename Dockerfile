# Dockerfile para Django - Sistema de Notas Técnicas
FROM python:3.14.2-slim

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Diretório de trabalho
WORKDIR /app

# Instala dependências do sistema (mínimas para PostgreSQL e build de psycopg)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        postgresql-client \
        libpq5 \
        libpq-dev \
        gcc \
        libc6-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copia e instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Remove gcc e build tools após instalação (reduz tamanho da imagem)
RUN apt-get purge -y --auto-remove gcc libc6-dev libpq-dev

# Copia código da aplicação
COPY . .

# Cria diretórios necessários
RUN mkdir -p /app/staticfiles /app/data/backups

# Coleta arquivos estáticos
RUN python manage.py collectstatic --noinput || true

# Script de inicialização
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expõe porta 8000
EXPOSE 8000

# Usuário não-root para segurança (opcional mas recomendado)
RUN useradd -m -u 1000 django && chown -R django:django /app
USER django

ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "300"]
