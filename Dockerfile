# Dockerfile para Django - Sistema de Notas Técnicas
FROM python:3.14-slim

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Instala dependências do sistema (wget para healthcheck)
RUN apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get update && \
    apt-get install -y --no-install-recommends wget && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Diretório de trabalho
WORKDIR /app

# Copia e instala dependências Python PRIMEIRO
COPY requirements.txt .

# Instala dependências de produção do requirements.txt
RUN pip install --no-cache-dir --progress-bar off --no-compile -r requirements.txt

# Cria usuário django
RUN useradd -m -u 1000 django

# Copia código da aplicação
COPY --chown=django:django . .

# Cria diretórios necessários
RUN mkdir -p /app/staticfiles /app/data/backups && \
    chown -R django:django /app/staticfiles /app/data/backups

# Copia e configura script de inicialização
COPY --chown=django:django entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Muda para usuário django
USER django

# Coleta arquivos estáticos
RUN python manage.py collectstatic --noinput || true

ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "300"]
