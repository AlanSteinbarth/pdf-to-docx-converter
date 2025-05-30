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

## ENTERPRISE FEATURES

- Zaawansowane logowanie do pliku z rotacją (`logs/app.log`)
- Konfiguracja przez plik `config.yaml` (output_dir, log_level, ocr_lang)
- Automatyczne testy jednostkowe (pytest, katalog `tests/`)
- Gotowy workflow CI/CD (GitHub Actions: `.github/workflows/python-app.yml`)

### Testy automatyczne

Aby uruchomić testy lokalnie:

```bash
pip install pytest pyyaml
pytest tests/
```

Testy uruchamiają się automatycznie przy każdym pushu do gałęzi `main` na GitHubie.

### Konfiguracja

Edytuj plik `config.yaml`, aby zmienić domyślne ustawienia aplikacji (np. katalog wyjściowy, poziom logowania, język OCR).

### Logowanie

Wszystkie logi audytowe zapisywane są do pliku `logs/app.log` z automatyczną rotacją (5 plików po 2MB).

## Licencja
MIT

## Autor
Alan Steinbarth
