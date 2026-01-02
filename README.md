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

- **Python 3.14+**
- **Django 6.0**
- **Git**

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
├── media/                     # Uploads
└── data/                      # Banco de dados
```

## 🐍 Instalação Local

### 1. Clone o repositório

```bash
git clone <url-do-repositorio>
cd django_notas_inss
```

### 2. Crie o ambiente virtual

```bash
# Windows
python -m venv venv
.\venv\Scripts\Activate.ps1

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente

```bash
# Copie o arquivo de exemplo
cp .env.example .env

# Edite o arquivo .env com suas configurações
```

### 5. Execute as migrações

```bash
python manage.py migrate
```

### 6. Crie um superusuário

```bash
python manage.py createsuperuser
```

### 7. Inicie o servidor

```bash
python manage.py runserver
```

A aplicação estará disponível em: **http://127.0.0.1:8000/**

## 🔧 Comandos Úteis

```bash
# Verificar configuração
python manage.py check

# Criar migrações
python manage.py makemigrations

# Aplicar migrações
python manage.py migrate

# Criar superusuário
python manage.py createsuperuser

# Coletar arquivos estáticos
python manage.py collectstatic

# Rodar testes
pytest
```

## 📚 Documentação

- **Planejamento**: Ver [PLANEJAMENTO.md](PLANEJAMENTO.md) para detalhes completos da migração
- **Django Docs**: https://docs.djangoproject.com/

## 🔒 Níveis de Acesso

1. **VISUALIZAR**: Acesso apenas à pesquisa de notas
2. **ANALISTA**: Pesquisa + configuração de notas
3. **ADMIN**: Acesso total ao sistema

## 🛠️ Stack Tecnológica

- **Framework**: Django 6.0
- **Python**: 3.14.2
- **Banco de Dados**: SQLite3 (desenvolvimento) / PostgreSQL (produção)
- **Processamento PDF**: PyMuPDF, pikepdf
- **Frontend**: Django Templates + Bootstrap/Tailwind

## 📝 Status do Projeto

**Fase Atual**: Fase 2 Completa ✅ | Fase 3 em Planejamento 🚧

- [x] Fase 1: Estrutura Base
- [x] Fase 2: Models e Migrações
  - [x] Models implementados (Term, Note, UserProfile)
  - [x] Django Admin configurado
  - [x] Banco de dados populado com dados de exemplo
  - [x] Django 6.0 instalado (compatível com Python 3.14)
- [ ] Fase 3: Autenticação e Autorização (próxima)

**Acesso ao Admin**: http://127.0.0.1:8000/admin/  
**Credenciais**: `admin` / `admin123`

## 📞 Suporte

Para dúvidas e suporte, consulte a documentação no arquivo [PLANEJAMENTO.md](PLANEJAMENTO.md).

---

**Data de Criação**: 31/12/2025  
**Versão**: 1.0.0  
**Python**: 3.14.2  
**Django**: 6.0
