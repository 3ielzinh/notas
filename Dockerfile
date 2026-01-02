# Dockerfile para Django - Sistema de Notas Técnicas
# Otimizado para ambientes com memória MUITO limitada
FROM python:3.14.2-slim

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Diretório de trabalho
WORKDIR /app

# Não instala postgresql-client (não é essencial, só para debug)
# psycopg[binary] já tem tudo que precisa
RUN rm -f /etc/apt/apt.conf.d/docker-clean

# Copia e instala dependências Python PRIMEIRO
COPY requirements.txt .
RUN pip install --no-cache-dir --progress-bar off --no-deps \
    Django==6.0 python-dotenv==1.0.0 gunicorn==21.2.0 whitenoise==6.6.0 && \
    pip install --no-cache-dir --progress-bar off --no-deps \
    "psycopg[binary]>=3.2.10" && \
    pip install --no-cache-dir --progress-bar off --no-deps \
    openpyxl==3.1.2 pypdf>=4.0.0 PyMuPDF>=1.24.0 reportlab>=4.0.0

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
