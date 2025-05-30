#!/bin/zsh
echo "🚀 Uruchamianie PDF Converter..."
cd "$(dirname "$0")"
export TK_SILENCE_DEPRECATION=1
python3 app.py
echo "✅ Aplikacja zakończona"
