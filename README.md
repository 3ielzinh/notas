# 📁 Sistema de Notas Técnicas — INSS (Django)

Sistema web para gerenciamento, pesquisa e anonimização de notas técnicas do INSS. Desenvolvido com Django 6.0 e Python 3.14.

## 🚀 Funcionalidades

- **Pesquisa Avançada**: Busca semântica e por filtros em notas técnicas
- **Importação de Documentos**: Upload e processamento de PDFs
- **Anonimização Automática**: Censura de informações sensíveis
- **Gerenciamento de Termos**: Configuração de termos para anonimização
- **Interface Intuitiva**: Interface moderna com Django Templates
- **Autenticação**: Sistema de login com controle de acesso por níveis

## 📋 Requisitos

- **Docker & Docker Compose**
- **Git**
- **PostgreSQL 15** (via Docker)

## 🏗️ Estrutura do Projeto

```
django_notas_inss/
├── manage.py
├── requirements.txt
├── .env
├── .gitignore
│
├── config/                    # Configurações Django
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── apps/
│   ├── core/                  # App central
│   ├── accounts/              # Autenticação
│   ├── notes/                 # Notas técnicas
│   └── terms/                 # Termos de anonimização
│
├── templates/                 # Templates globais
├── static/                    # Arquivos estáticos
└── data/                      # Backups
```

## � Instalação com Docker

### 1. Clone o repositório

```bash
git clone https://www-gitinss.prevnet/dgrt/notas_dilag.git
cd notas_dilag
```

### 2. Configure as variáveis de ambiente

```bash
# Copie o arquivo de exemplo
cp .env.example .env

# Edite o arquivo .env (ajuste DB_PASSWORD se necessário)
```

### 3. Suba os containers

```bash
docker-compose up -d
```

### 4. Execute as migrações

```bash
docker-compose exec web python manage.py migrate
```

### 5. Crie um superusuário

```bash
docker-compose exec web python manage.py createsuperuser
```

A aplicação estará disponível em: **http://localhost:8000/**

> 📖 Para deploy em produção, consulte [DEPLOY.md](DEPLOY.md) ou [QUICKSTART.md](QUICKSTART.md)

## 🔧 Comandos Úteis

```bash
# Ver logs
docker-compose logs -f web

# Parar containers
docker-compose down

# Criar migrações
docker-compose exec web python manage.py makemigrations

# Aplicar migrações
docker-compose exec web python manage.py migrate

# Shell do Django
docker-compose exec web python manage.py shell

# Shell do banco de dados
docker-compose exec db psql -U postgres -d django_notas

# Backup do banco
docker-compose exec db pg_dump -U postgres django_notas > backup.sql
```

## 📚 Documentação

- **Deploy Produção**: [DEPLOY.md](DEPLOY.md) - Guia completo de deployment
- **Quick Start**: [QUICKSTART.md](QUICKSTART.md) - Início rápido (5 minutos)
- **Django Docs**: https://docs.djangoproject.com/

## 🔒 Níveis de Acesso

1. **VISUALIZAR**: Acesso apenas à pesquisa de notas
2. **ANALISTA**: Pesquisa + configuração de notas
3. **ADMIN**: Acesso total ao sistema

## 🛠️ Stack Tecnológica

- **Framework**: Django 6.0
- **Python**: 3.14.2
- **Banco de Dados**: PostgreSQL 15
- **Container**: Docker + Docker Compose
- **Web Server**: Gunicorn (dev) / Nginx + Gunicorn (prod)
- **Processamento PDF**: PyMuPDF (fitz)
- **Frontend**: Django Templates + CSS customizado

## 📝 Status do Projeto

**Status**: ✅ Produção Ready

- [x] Estrutura completa com Django 6.0 + Python 3.14
- [x] Autenticação e autorização por níveis
- [x] Sistema de pesquisa e filtros avançados
- [x] Anonimização automática (SIAPE, CPF, Nomes)
- [x] Processamento de PDFs com context-aware
- [x] Suporte a acentos e variações
- [x] Docker Compose (dev + produção)
- [x] Nginx reverse proxy + SSL ready
- [x] Sistema de backup automatizado
- [x] PDFs armazenados em database (BinaryField)

**Acesso ao Admin**: http://localhost:8000/admin/

## 📞 Suporte

Para dúvidas sobre deployment, consulte:
- [DEPLOY.md](DEPLOY.md) - Guia completo de produção
- [QUICKSTART.md](QUICKSTART.md) - Início rápido

---

**Última Atualização**: 02/01/2026  
**Versão**: 2.0.0  
**Python**: 3.14.2  
**Django**: 6.0  
**PostgreSQL**: 15
