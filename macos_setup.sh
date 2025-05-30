#!/bin/bash

# Sprawdź czy Homebrew jest zainstalowany
if ! command -v brew &> /dev/null; then
    echo "Instalowanie Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# Instalacja poppler, Tesseract OCR i języków Tesseract
if ! command -v pdfinfo &> /dev/null || ! command -v tesseract &> /dev/null; then
    echo "Instalowanie poppler, Tesseract OCR i języków Tesseract..."
    brew install poppler tesseract tesseract-lang
fi

# Sprawdź czy Python jest zainstalowany
if ! command -v python3 &> /dev/null; then
    echo "Instalowanie Python 3..."
    brew install python@3
fi

# Stwórz i aktywuj środowisko wirtualne
echo "Konfigurowanie środowiska Python..."
python3 -m venv venv
source venv/bin/activate

# Instalacja wymaganych pakietów Python
echo "Instalowanie wymaganych pakietów Python..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Konfiguracja zakończona! Możesz teraz uruchomić aplikację używając ./run_app.command"

# Nadaj uprawnienia wykonywania dla skryptu uruchomieniowego
chmod +x run_app.command
