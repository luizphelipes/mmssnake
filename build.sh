#!/bin/bash

# Script de build com múltiplas tentativas
set -e

echo "🚀 Iniciando build do MMSSnake..."

# Função para tentar build com diferentes estratégias
try_build() {
    local strategy=$1
    echo "📦 Tentando build com estratégia: $strategy"
    
    case $strategy in
        "cache")
            docker build --build-arg BUILDKIT_INLINE_CACHE=1 -t mmssnake:latest .
            ;;
        "alpine")
            docker build -f Dockerfile.alpine -t mmssnake:alpine .
            ;;
        "no-cache")
            docker build --no-cache -t mmssnake:latest .
            ;;
        "simple")
            # Dockerfile simplificado sem cache mounts
            docker build --no-cache --build-arg BUILDKIT_INLINE_CACHE=0 -t mmssnake:simple .
            ;;
    esac
}

# Tentar diferentes estratégias
strategies=("cache" "alpine" "no-cache" "simple")

for strategy in "${strategies[@]}"; do
    if try_build "$strategy"; then
        echo "✅ Build bem-sucedido com estratégia: $strategy"
        exit 0
    else
        echo "❌ Falha na estratégia: $strategy"
        continue
    fi
done

echo "💥 Todas as estratégias de build falharam"
exit 1 