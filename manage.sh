#!/bin/bash
# Script de gerenciamento do Sistema de Notas Técnicas
# Uso: ./manage.sh [comando]

COMPOSE_FILE="docker-compose.prod.yml"

case "$1" in
    start)
        echo "🚀 Iniciando sistema..."
        docker-compose -f $COMPOSE_FILE up -d
        echo "✅ Sistema iniciado!"
        ;;
    
    stop)
        echo "🛑 Parando sistema..."
        docker-compose -f $COMPOSE_FILE down
        echo "✅ Sistema parado!"
        ;;
    
    restart)
        echo "🔄 Reiniciando sistema..."
        docker-compose -f $COMPOSE_FILE restart
        echo "✅ Sistema reiniciado!"
        ;;
    
    logs)
        echo "📋 Exibindo logs..."
        docker-compose -f $COMPOSE_FILE logs -f --tail=100
        ;;
    
    status)
        echo "📊 Status dos containers:"
        docker-compose -f $COMPOSE_FILE ps
        ;;
    
    backup)
        echo "💾 Criando backup do banco de dados..."
        BACKUP_DIR="./backups"
        mkdir -p $BACKUP_DIR
        DATE=$(date +%Y%m%d_%H%M%S)
        docker-compose -f $COMPOSE_FILE exec -T db pg_dump -U postgres django_notas | gzip > ${BACKUP_DIR}/backup_${DATE}.sql.gz
        echo "✅ Backup criado: ${BACKUP_DIR}/backup_${DATE}.sql.gz"
        echo "🗑️  Removendo backups com mais de 7 dias..."
        find ${BACKUP_DIR} -name "backup_*.sql.gz" -mtime +7 -delete
        ;;
    
    restore)
        if [ -z "$2" ]; then
            echo "❌ Especifique o arquivo de backup"
            echo "Uso: ./manage.sh restore backup_20260102.sql.gz"
            exit 1
        fi
        echo "♻️  Restaurando backup: $2"
        gunzip < "$2" | docker-compose -f $COMPOSE_FILE exec -T db psql -U postgres django_notas
        echo "✅ Backup restaurado!"
        ;;
    
    migrate)
        echo "🔄 Executando migrações..."
        docker-compose -f $COMPOSE_FILE exec web python manage.py migrate
        echo "✅ Migrações executadas!"
        ;;
    
    shell)
        echo "🐍 Abrindo shell Django..."
        docker-compose -f $COMPOSE_FILE exec web python manage.py shell
        ;;
    
    bash)
        echo "💻 Abrindo bash no container..."
        docker-compose -f $COMPOSE_FILE exec web bash
        ;;
    
    collectstatic)
        echo "📦 Coletando arquivos estáticos..."
        docker-compose -f $COMPOSE_FILE exec web python manage.py collectstatic --noinput
        echo "✅ Arquivos estáticos coletados!"
        ;;
    
    update)
        echo "🔄 Atualizando sistema..."
        echo "1. Criando backup..."
        ./manage.sh backup
        echo "2. Baixando alterações..."
        git pull origin main
        echo "3. Reconstruindo containers..."
        docker-compose -f $COMPOSE_FILE down
        docker-compose -f $COMPOSE_FILE up -d --build
        echo "4. Executando migrações..."
        docker-compose -f $COMPOSE_FILE exec web python manage.py migrate
        echo "5. Coletando arquivos estáticos..."
        docker-compose -f $COMPOSE_FILE exec web python manage.py collectstatic --noinput
        echo "✅ Sistema atualizado!"
        ;;
    
    clean)
        echo "🧹 Limpando sistema..."
        docker-compose -f $COMPOSE_FILE down
        docker system prune -f
        echo "✅ Sistema limpo!"
        ;;
    
    *)
        echo "📖 Uso: ./manage.sh [comando]"
        echo ""
        echo "Comandos disponíveis:"
        echo "  start         - Iniciar sistema"
        echo "  stop          - Parar sistema"
        echo "  restart       - Reiniciar sistema"
        echo "  logs          - Ver logs em tempo real"
        echo "  status        - Ver status dos containers"
        echo "  backup        - Criar backup do banco"
        echo "  restore       - Restaurar backup do banco"
        echo "  migrate       - Executar migrações"
        echo "  shell         - Abrir shell Django"
        echo "  bash          - Abrir bash no container"
        echo "  collectstatic - Coletar arquivos estáticos"
        echo "  update        - Atualizar sistema completo"
        echo "  clean         - Limpar sistema (remove containers parados)"
        echo ""
        exit 1
        ;;
esac
