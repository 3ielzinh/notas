# 🚀 Deploy em Produção - Sistema de Notas Técnicas INSS

## 📋 Pré-requisitos

- Docker Engine 20.10+
- Docker Compose v2.0+
- Domínio configurado (para SSL/TLS)
- Servidor Linux (recomendado: Ubuntu 22.04 LTS)

## 🔧 Configuração Inicial

### 1. Clonar o repositório
```bash
git clone <url-do-repositorio>
cd DJANGO_NOTAS_TECNICAS
```

### 2. Configurar variáveis de ambiente
```bash
# Copiar arquivo de exemplo
cp .env.production .env

# Gerar SECRET_KEY segura
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Editar .env com suas configurações
nano .env
```

**Configurações obrigatórias no `.env`:**
```bash
DEBUG=False
SECRET_KEY=<cole-aqui-a-chave-gerada>
ALLOWED_HOSTS=seu-dominio.com,www.seu-dominio.com
DB_PASSWORD=<senha-forte-banco>
```

### 3. Criar diretórios necessários
```bash
mkdir -p data/backups logs/nginx backups
chmod 755 data/backups logs/nginx backups
```

### 4. Build e iniciar containers
```bash
# Usando docker-compose de produção
docker-compose -f docker-compose.prod.yml up -d --build
```

### 5. Executar migrações
```bash
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

### 6. Criar superusuário
```bash
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

### 7. Importar termos de anonimização
```bash
# Se tiver arquivo CSV com termos
docker cp termos.csv notas_django_prod:/app/
docker-compose -f docker-compose.prod.yml exec web python manage.py shell
>>> from apps.terms.models import Term
>>> # Importar seus termos aqui
```

## 🔐 Configurar SSL/TLS (HTTPS)

### Opção 1: Let's Encrypt com Certbot

```bash
# Instalar certbot
sudo apt-get install certbot python3-certbot-nginx

# Criar diretórios
mkdir -p certbot/conf certbot/www

# Obter certificado
sudo certbot certonly --webroot \
  -w ./certbot/www \
  -d seu-dominio.com \
  -d www.seu-dominio.com

# Copiar certificados para o projeto
sudo cp -r /etc/letsencrypt certbot/conf/

# Descomentar seção HTTPS no nginx.conf
nano nginx.conf

# Reiniciar nginx
docker-compose -f docker-compose.prod.yml restart nginx
```

### Renovação automática
```bash
# Adicionar ao crontab
sudo crontab -e

# Adicionar linha:
0 3 * * * certbot renew --quiet && docker-compose -f /caminho/para/projeto/docker-compose.prod.yml restart nginx
```

## 📊 Monitoramento

### Ver logs
```bash
# Logs do Django
docker-compose -f docker-compose.prod.yml logs -f web

# Logs do Nginx
docker-compose -f docker-compose.prod.yml logs -f nginx

# Logs do PostgreSQL
docker-compose -f docker-compose.prod.yml logs -f db
```

### Status dos containers
```bash
docker-compose -f docker-compose.prod.yml ps
```

### Health check
```bash
# Verificar saúde dos serviços
docker-compose -f docker-compose.prod.yml exec web curl http://localhost:8000/
```

## 💾 Backup

### Backup do banco de dados
```bash
# Criar backup
docker-compose -f docker-compose.prod.yml exec db pg_dump -U postgres django_notas > backup_$(date +%Y%m%d_%H%M%S).sql

# Ou usar o script automático (criar)
echo '#!/bin/bash
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose -f docker-compose.prod.yml exec -T db pg_dump -U postgres django_notas | gzip > ${BACKUP_DIR}/backup_${DATE}.sql.gz
find ${BACKUP_DIR} -name "backup_*.sql.gz" -mtime +7 -delete
' > backup.sh
chmod +x backup.sh

# Adicionar ao crontab (backup diário às 2h)
0 2 * * * /caminho/para/projeto/backup.sh
```

### Restaurar backup
```bash
# Descompactar e restaurar
gunzip < backup_20260102.sql.gz | docker-compose -f docker-compose.prod.yml exec -T db psql -U postgres django_notas
```

## 🔄 Atualização do Sistema

```bash
# 1. Fazer backup
./backup.sh

# 2. Baixar novas alterações
git pull origin main

# 3. Rebuild e reiniciar
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build

# 4. Executar migrações
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

## 🔧 Troubleshooting

### Container não inicia
```bash
# Ver logs detalhados
docker-compose -f docker-compose.prod.yml logs web

# Verificar variáveis de ambiente
docker-compose -f docker-compose.prod.yml exec web env | grep -E 'DEBUG|SECRET_KEY|DB_'
```

### Erro de permissão em arquivos
```bash
# Ajustar permissões
sudo chown -R 1000:1000 media data logs
sudo chmod -R 755 media data logs
```

### Limpar containers e volumes (CUIDADO!)
```bash
# Remove tudo exceto volumes com dados
docker-compose -f docker-compose.prod.yml down

# Para remover TUDO incluindo dados (BACKUP ANTES!)
docker-compose -f docker-compose.prod.yml down -v
```

## 🛡️ Segurança

### Firewall
```bash
# Permitir apenas portas necessárias
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

### Atualizações de segurança
```bash
# Atualizar imagens base regularmente
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

## 📞 Suporte

Para problemas ou dúvidas:
- Verificar logs do sistema
- Consultar documentação do Django
- Revisar configurações do .env

## 📝 Checklist de Deploy

- [ ] SECRET_KEY alterada
- [ ] DEBUG=False
- [ ] ALLOWED_HOSTS configurado
- [ ] Senha do banco alterada
- [ ] Certificado SSL configurado
- [ ] Firewall configurado
- [ ] Backup automático configurado
- [ ] Logs sendo monitorados
- [ ] Termos de anonimização importados
- [ ] Superusuário criado
- [ ] Teste de acesso ao sistema realizado
