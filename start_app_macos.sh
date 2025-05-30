#!/bin/zsh
# Skrypt uruchamiający aplikację PDF Converter na macOS
# Omija problemy z conda i uruchamia aplikację z systemowym Python

echo "🚀 PDF to DOCX Converter - uruchamianie..."

# Ustawienie flagi dla Tkinter na macOS, aby uniknąć ostrzeżeń o deprekacji
export TK_SILENCE_DEPRECATION=1

# Przejdź do katalogu, w którym znajduje się skrypt
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"
echo "🖥️  $(uname -s)"
echo "📁 Katalog: $(pwd)"

echo "🐍 Uruchamianie aplikacji app.py..."

python3 app.py

if [ $? -ne 0 ]; then
    echo "❌ Wystąpił błąd podczas uruchamiania aplikacji app.py."
    exit 1
fi

echo "✅ Aplikacja zakończyła działanie."

# Opcjonalnie: Deaktywacja środowiska po zamknięciu aplikacji (jeśli skrypt nie kończy się od razu)
# conda deactivate
