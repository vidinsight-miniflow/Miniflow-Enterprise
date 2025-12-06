#!/bin/bash
# MiniFlow Enterprise - Başlatma Scripti
# Kullanım: ./start.sh [setup|run|help]

# Proje root dizinine git
cd "$(dirname "$0")"

# PYTHONPATH ayarla
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Komut al
COMMAND="${1:-run}"

# Eğer run komutu verilmişse veya hiçbir şey verilmemişse
if [ "$COMMAND" = "run" ] || [ -z "$1" ]; then
    echo "🔍 Setup kontrolü yapılıyor..."
    
    # Önce setup yap
    python -m src.miniflow setup
    
    # Setup başarılı mı kontrol et
    SETUP_EXIT_CODE=$?
    
    if [ $SETUP_EXIT_CODE -ne 0 ]; then
        echo ""
        echo "❌ Setup başarısız oldu! Run komutu çalıştırılamadı."
        echo "   Lütfen setup hatalarını düzeltin ve tekrar deneyin."
        exit $SETUP_EXIT_CODE
    fi
    
    echo ""
    echo "✅ Setup başarılı! Uygulama başlatılıyor..."
    echo ""
    
    # Setup başarılıysa run yap
    python -m src.miniflow run
else
    # Diğer komutlar (setup, help, vb.) direkt çalıştır
    python -m src.miniflow "$@"
fi

