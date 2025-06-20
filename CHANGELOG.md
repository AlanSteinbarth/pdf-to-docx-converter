# Historia zmian

## [4.2.0] - 2025-06-20
### Dodano
- **ENTERPRISE DOCUMENTATION**: profesjonalna dokumentacja kodu z markdown-style docstringami
- **JAKOŚĆ KODU**: osiągnięto Pylint score 8.65/10 - enterprise-grade quality
- **REFAKTORING**: poprawki jakości kodu, usunięcie code smells i warning'ów
- **DOKUMENTACJA TECHNICZNA**: szczegółowe sekcje kodu z opisami funkcjonalności
- **README ENHANCEMENT**: rozszerzona dokumentacja z architekturą kodu
- Nowoczesny design w stylu macOS z obsługą motywu dzień/noc
- Wysoki kontrast i czytelność dla lepszej dostępności
- Jednolity styl przycisków i elementów UI
- Stabilność uruchamiania na różnych systemach operacyjnych
- **Zrzuty ekranu** w folderze `screenshots/` z wizualizacją interfejsu
- **Profesjonalna okładka** `cover.png` - hero image w stylu Apple MacBook Pro

### Zmieniono
- **Import order**: poprawiona kolejność importów (standard library first)
- **Docstrings**: zamiana na profesjonalne markdown-style dokumenty
- **Code structure**: logiczne sekcje z emoji i nagłówkami
- **Error handling**: usunięcie niepotrzebnych else/elif po return
- **String statements**: eliminacja pointless string statements
- Ulepszony wygląd interfejsu użytkownika
- Poprawiona kompatybilność z różnymi systemami operacyjnymi
- Zaktualizowana dokumentacja i struktura projektu

### Techniczne
- **Pylint Score**: 7.29 → 8.65/10 (+1.36 punktów)
- **Code Quality**: enterprise-grade standards
- **Documentation**: professional markdown docstrings
- **Maintainability**: znacząco ulepszona

## [4.1.0] - 2025-06-18
### Dodano
- ENTERPRISE: logowanie do pliku z rotacją (logs/app.log)
- ENTERPRISE: konfiguracja przez plik config.yaml (output_dir, log_level, ocr_lang)
- ENTERPRISE: testy jednostkowe (pytest, katalog tests/)
- ENTERPRISE: workflow CI/CD (GitHub Actions)

## [4.0.0] - 2025-05-30
### Dodano
- Automatyczne rozpoznawanie tekstu (OCR) dla PDF-ów bez warstwy tekstowej (skany, zdjęcia)
- Zaawansowany preprocessing obrazu: autokontrast, wyostrzanie, mocniejsza binarizacja, DPI x3
- Rozpoznawanie wyłącznie języka polskiego dla lepszej skuteczności OCR
- Nowy, stabilny i responsywny interfejs (Tkinter, PanedWindow, podgląd PDF)
- Przycisk "Pomoc / O programie" na górze panelu
- Pasek postępu, logi, anulowanie konwersji, wsparcie dla wielu plików
- Obsługa macOS, Windows, Linux

### Zmieniono
- Usunięto drag & drop (pełna stabilność na wszystkich systemach)
- Uproszczono kod, usunięto artefakty i stare backupy
- Poprawiono dokumentację i instrukcje

### Naprawiono
- Problemy z widocznością przycisków i podglądu na macOS
- Błędy środowiskowe z pytesseract
- Błędy layoutu i responsywności

## [3.2.0] - 2024-12-19
### Dodano ✨
- **Wieloplatformowe wsparcie** - program działa na Windows, macOS i Linux
- Automatyczna detekcja systemu operacyjnego z modułem `platform`
- Inteligentny wybór domyślnego folderu wyjściowego per system operacyjny:
  - Windows: `%USERPROFILE%\Documents`
  - macOS: `~/Documents`
  - Linux: `~/Documents`
- Wieloplatformowe otwieranie folderów:
  - Windows: `explorer`
  - macOS: `open`
  - Linux: `xdg-open`
- Rozszerzone instrukcje instalacji dla wszystkich systemów operacyjnych
- Informacje o systemie w oknie "O autorze"
- Wieloplatformowa detekcja Poppler i Tesseract z odpowiednimi komunikatami błędów

### Zmieniono 🔧
- Zaktualizowane FAQ z informacjami o wspieranych systemach operacyjnych
- Poprawiona obsługa błędów z systemowo-specyficznymi komunikatami
- Ulepszona dokumentacja z instrukcjami instalacji dla macOS i Linux

### Techniczne 🛠️
- Usunięto hardkodowane ścieżki Windows
- Dodano metodę `get_default_output_dir()` z automatyczną detekcją systemu
- Zaktualizowano `open_output_dir()` z wieloplatformową obsługą
- Poprawiono `check_poppler()` z detekcją dla różnych systemów operacyjnych
- Rozszerzono `show_install_instructions()` o wszystkie systemy operacyjne

## [3.1.0] - 2025-05-25

### Dodano
- Wsparcie dla OCR w języku polskim i angielskim
- Podgląd tekstu i obrazu po preprocessingu
- Drag & drop plików
- Anulowanie konwersji w trakcie
- Szczegółowe logi konwersji
- Automatyczne wykrywanie i konfiguracja Poppler
- Wsparcie dla wielu plików (konwersja wsadowa)

### Zmieniono
- Poprawiono obsługę Poppler z AppData
- Zwiększono szerokość listy plików do 900px
- Ulepszono preprocessing obrazu przed OCR
- Dodano sekcje i komentarze w kodzie

### Naprawiono
- Błąd z wykrywaniem Poppler mimo prawidłowej instalacji
- Problemy z podglądem obrazu po preprocessingu
- Szerokość okna wyboru plików

### Techniczne
- Refaktoryzacja kodu i dodanie sekcji
- Dodanie obsługi błędów i logowania
- Optymalizacja przetwarzania wielu plików
- Dokumentacja w języku polskim

## [3.0.0] - 2025-04-15

### Dodano
- Pierwsza publiczna wersja
- Podstawowa konwersja PDF na DOCX/TXT
- Interfejs użytkownika w Tkinter
- Obsługa OCR przez Tesseract
- Konfiguracja przez GUI
