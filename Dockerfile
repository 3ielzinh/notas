# Dockerfile para Django - Sistema de Notas Técnicas
# Otimizado para ambientes com memória limitada
FROM python:3.14.2-slim

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Diretório de trabalho
WORKDIR /app

# Instala apenas dependências de runtime (SEM build tools)
# psycopg-binary já vem compilado, não precisa gcc
RUN rm -f /etc/apt/apt.conf.d/docker-clean && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        postgresql-client \
        libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copia e instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

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
