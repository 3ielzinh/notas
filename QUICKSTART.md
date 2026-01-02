# ⚡ Guia Rápido de Deploy

## 🚀 Deploy Rápido (5 minutos)

```bash
# 1. Configurar ambiente
cp .env.production .env
nano .env  # Alterar SECRET_KEY, DB_PASSWORD, ALLOWED_HOSTS

# 2. Iniciar sistema
chmod +x manage.sh
./manage.sh start

# 3. Configurar banco
./manage.sh migrate

# 4. Criar admin
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

# 5. Importar termos (se tiver)
# Copiar arquivos CSV para ./data/ e importar via admin

# ✅ Sistema pronto em: http://seu-servidor
```

## 📁 Estrutura de Arquivos Importante

```
DJANGO_NOTAS_TECNICAS/
├── .env                    # ⚠️ CONFIGURAR ANTES!
├── docker-compose.prod.yml # Produção
├── nginx.conf              # Config Nginx
├── manage.sh              # Scripts úteis
├── DEPLOY.md              # Guia completo
└── backups/               # Backups automáticos
```

## 🔑 Variáveis Obrigatórias (.env)

```bash
DEBUG=False
SECRET_KEY=<gerar-nova-chave>     # ⚠️ OBRIGATÓRIO
ALLOWED_HOSTS=seu-dominio.com     # ⚠️ OBRIGATÓRIO  
DB_PASSWORD=<senha-forte>         # ⚠️ OBRIGATÓRIO
```

### Gerar SECRET_KEY:
```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## 🛠️ Comandos Úteis

```bash
./manage.sh start          # Iniciar
./manage.sh stop           # Parar
./manage.sh logs           # Ver logs
./manage.sh backup         # Backup
./manage.sh status         # Status
./manage.sh update         # Atualizar
```

## 🔐 Configurar HTTPS (Let's Encrypt)

```bash
# 1. Instalar certbot
sudo apt-get install certbot

# 2. Obter certificado
sudo certbot certonly --standalone -d seu-dominio.com

# 3. Editar nginx.conf (descomentar seção HTTPS)
nano nginx.conf

# 4. Reiniciar
./manage.sh restart
```

## 💾 Backup Automático

```bash
# Adicionar ao crontab
crontab -e

# Backup diário às 2h da manhã
0 2 * * * /caminho/completo/manage.sh backup

# Renovar SSL às 3h da manhã
0 3 * * * certbot renew --quiet && /caminho/completo/manage.sh restart
```

## 🆘 Problemas Comuns

### Erro de permissão
```bash
sudo chown -R $USER:$USER media/ data/ logs/
chmod 755 media/ data/ logs/
```

### Container não inicia
```bash
./manage.sh logs  # Ver erro
docker-compose -f docker-compose.prod.yml ps  # Ver status
```

### Resetar tudo (CUIDADO!)
```bash
./manage.sh backup  # Backup primeiro!
./manage.sh stop
docker-compose -f docker-compose.prod.yml down -v
./manage.sh start
./manage.sh migrate
```

## 📞 Verificação Pós-Deploy

- [ ] Sistema acessível em http://seu-servidor
- [ ] Login funcionando
- [ ] Upload de PDF funcionando
- [ ] Busca funcionando
- [ ] Backup configurado

---

📖 **Documentação completa**: Ver [DEPLOY.md](DEPLOY.md)
