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

# Copia e instala dependências Python PRIMEIRO
COPY requirements.txt .

# Instala dependências de produção do requirements.txt
RUN pip install --no-cache-dir --progress-bar off --no-compile -r requirements.txt

# Copia código da aplicação
COPY . .

# Cria usuário django antes de criar diretórios
RUN useradd -m -u 1000 django

# Cria diretórios necessários e define permissões
RUN mkdir -p /app/staticfiles /app/data/backups && \
    chown -R django:django /app

# Coleta arquivos estáticos como usuário django
USER django
RUN python manage.py collectstatic --noinput || true

# Script de inicialização
COPY --chown=django:django entrypoint.sh /entrypoint.sh
USER root
RUN chmod +x /entrypoint.sh
USER django

ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "300"]
