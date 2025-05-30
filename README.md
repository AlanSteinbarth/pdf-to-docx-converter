# Konwerter PDF -> DOCX/TXT z OCR

Zaawansowany, wieloplatformowy konwerter PDF na DOCX/TXT z automatycznym rozpoznawaniem tekstu (OCR) dla skanów i zdjęć. Nowoczesny, stabilny interfejs, wsparcie dla macOS, Windows, Linux.

## Najważniejsze funkcje
- Automatyczne rozpoznawanie tekstu (OCR) dla PDF-ów bez warstwy tekstowej (skany, zdjęcia)
- Zaawansowany preprocessing obrazu: autokontrast, wyostrzanie, mocniejsza binarizacja, DPI x3
- Rozpoznawanie wyłącznie języka polskiego dla lepszej skuteczności OCR
- Nowy, stabilny i responsywny interfejs (Tkinter, PanedWindow, podgląd PDF)
- Przycisk "Pomoc / O programie" na górze panelu
- Pasek postępu, logi, anulowanie konwersji, wsparcie dla wielu plików
- Obsługa macOS, Windows, Linux

## Instalacja
1. Zainstaluj wymagane biblioteki:
   ```bash
   pip install -r requirements.txt
   ```
2. Zainstaluj Poppler i Tesseract OCR:
   - **macOS:**
     ```bash
     brew install poppler tesseract tesseract-lang
     ```
   - **Windows:**
     - Pobierz Poppler: https://github.com/oschwartz10612/poppler-windows/releases
     - Pobierz Tesseract: https://github.com/tesseract-ocr/tesseract
   - **Linux:**
     ```bash
     sudo apt install poppler-utils tesseract-ocr tesseract-ocr-pol
     ```

## Uruchomienie
```bash
python app.py
```

## Nowości w wersji 4.0.0 (30.05.2025)
- Automatyczny, skuteczny OCR dla skanów i zdjęć (język polski)
- Lepsza jakość rozpoznawania tekstu (DPI x3, wyostrzanie, binarizacja)
- Stabilny, nowoczesny interfejs
- Usunięto drag & drop (pełna stabilność)
- Poprawiona dokumentacja

## Licencja
MIT

## Autor
Alan Steinbarth
