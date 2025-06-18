#!/bin/zsh
echo "🚀 Uruchamianie PDF Converter v4.1.0 Enterprise Edition..."
cd "$(dirname "$0")"
export TK_SILENCE_DEPRECATION=1
python3 app.py
echo "✅ Aplikacja zakończona"
