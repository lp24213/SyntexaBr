#!/bin/bash
# ============================================================
# VEREDA / SYNTEXA — AWS GPU Cluster Control
# ============================================================
set -euo pipefail

COMPOSE_FILE="/opt/syntexa-gpu/docker-compose.gpu.yml"

function show_help() {
    echo "Uso: $0 {start|stop|restart|status|logs|update}"
    echo ""
    echo "  start   - Inicia o cluster GPU"
    echo "  stop    - Para o cluster GPU"
    echo "  restart - Reinicia o cluster GPU"
    echo "  status  - Mostra status dos serviços"
    echo "  logs    - Mostra logs (tail -f)"
    echo "  update  - Pull de imagens e reinício"
    echo "  health  - Verifica saúde de todos os serviços"
}

case "${1:-help}" in
    start)
        echo "[VEREDA] Iniciando cluster GPU..."
        sudo docker compose -f "$COMPOSE_FILE" up -d
        echo "[OK] Cluster iniciado"
        ;;
    stop)
        echo "[VEREDA] Parando cluster GPU..."
        sudo docker compose -f "$COMPOSE_FILE" down
        echo "[OK] Cluster parado"
        ;;
    restart)
        echo "[VEREDA] Reiniciando cluster GPU..."
        sudo docker compose -f "$COMPOSE_FILE" restart
        echo "[OK] Cluster reiniciado"
        ;;
    status)
        sudo docker compose -f "$COMPOSE_FILE" ps
        ;;
    logs)
        sudo docker compose -f "$COMPOSE_FILE" logs -f
        ;;
    update)
        echo "[VEREDA] Atualizando imagens..."
        sudo docker compose -f "$COMPOSE_FILE" pull
        sudo docker compose -f "$COMPOSE_FILE" up -d
        echo "[OK] Cluster atualizado"
        ;;
    health)
        echo "[VEREDA] Verificando saúde..."
        for port in 8000 8001 8002 8003; do
            if curl -sf "http://localhost:$port/health" > /dev/null 2>&1; then
                echo "[OK] Porta $port: SAUDÁVEL"
            else
                echo "[ERRO] Porta $port: INDISPONÍVEL"
            fi
        done
        ;;
    *)
        show_help
        exit 1
        ;;
esac
