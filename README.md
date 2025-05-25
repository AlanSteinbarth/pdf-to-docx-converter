# Konwerter PDF -> DOCX/TXT z OCR

Program do konwersji plików PDF na format DOCX (Microsoft Word) lub TXT z obsługą OCR (rozpoznawania tekstu ze skanów), nowoczesnym interfejsem i zaawansowanymi funkcjami.

## Najważniejsze funkcje
- Konwersja wielu plików PDF na DOCX lub TXT (wsadowo, z podfolderami)
- Automatyczne wykrywanie i obsługa Poppler oraz Tesseract OCR
- Drag & drop plików PDF do listy
- Multiselect i usuwanie wielu plików naraz z listy
- Zapamiętywanie ostatniego folderu wyjściowego i ostatnio używanych plików
- Kolejkowanie i automatyczna konwersja dużych zbiorów plików (z podfolderami)
- Podgląd tekstu PDF oraz obrazu po preprocessingu OCR
- Preprocessing obrazu (skala szarości, wyostrzanie, binarizacja), DPI=500, język pol+eng, PSM 6
- Szeroka lista plików, wygodne przyciski, logi, statusy, anulowanie konwersji
- Szybka instrukcja obsługi oraz linki do Poppler/Tesseract w Pomocy

## Wymagania
- Python 3.x
- Biblioteki:
  - pdf2docx
  - pdf2image
  - pytesseract
  - pillow
  - pdfminer.six
  - tkinter (standardowa biblioteka Python)
- Zewnętrzne narzędzia:
  - Poppler (do konwersji PDF na obrazy)
  - Tesseract OCR (do rozpoznawania tekstu ze skanów)

## Instalacja
1. Zainstaluj wymagane biblioteki Python:
   ```bash
   pip install pdf2docx pdf2image pytesseract pillow pdfminer.six
   ```
2. Pobierz i zainstaluj Poppler:
   - [Poppler dla Windows](https://github.com/oschwartz10612/poppler-windows/releases)
   - Rozpakuj do folderu, np. `C:/Program Files/poppler`
   - Dodaj ścieżkę do `.../poppler/Library/bin` do zmiennej PATH
3. Pobierz i zainstaluj Tesseract OCR:
   - [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
   - Zainstaluj i dodaj do PATH (np. `C:/Program Files/Tesseract-OCR`)
   - Dla polskiego OCR doinstaluj język polski (`pol`)

## Uruchomienie
1. Uruchom program za pomocą:
   ```bash
   python app.py
   ```
2. Dodaj pliki PDF do listy (przeciągnij lub użyj przycisku "Wybierz pliki"/"Dodaj folder")
3. (Opcjonalnie) Zmień folder docelowy
4. Wybierz format wyjściowy (DOCX lub TXT)
5. Kliknij "Konwertuj" aby rozpocząć proces
6. Możesz anulować konwersję w dowolnym momencie

## Opis interfejsu
| Przycisk/Funkcja | Opis |
|-----------------|------|
| **Wybierz pliki** | Dodaje pliki PDF do listy |
| **Dodaj folder** | Dodaje wszystkie pliki PDF z folderu i podfolderów |
| **Usuń wybrane** | Usuwa zaznaczone pliki z listy (multiselect) |
| **Wyczyść listę** | Usuwa wszystkie pliki z listy |
| **Podgląd obrazu** | Pokazuje, jak wygląda strona po przygotowaniu do OCR |
| **Podgląd tekstu** | Wyświetla fragment tekstu z wybranego PDF |
| **Logi** | Szczegółowy przebieg konwersji i komunikaty |
| **Anuluj** | Przerywa konwersję |
| **Pomoc** | Instrukcja, FAQ, linki do Poppler/Tesseract |

## FAQ (Często zadawane pytania)
1. **Co to jest OCR?**
   - OCR (Optical Character Recognition) rozpoznaje tekst ze skanów/obrazów PDF.
2. **Kiedy używany jest OCR?**
   - Gdy PDF jest skanem lub nie zawiera tekstu – program wykrywa to automatycznie.
3. **Jak dodać pliki?**
   - Przeciągnij pliki PDF do listy lub użyj przycisków "Wybierz pliki"/"Dodaj folder".
4. **Jak usunąć pliki z listy?**
   - Zaznacz jeden lub więcej plików i kliknij "Usuń wybrane".
5. **Jak poprawić jakość OCR?**
   - Program automatycznie stosuje preprocessing i wysoki DPI. Jakość zależy od oryginału.
6. **Gdzie pobrać Poppler i Tesseract?**
   - Linki w menu Pomoc oraz powyżej.

## Znane ograniczenia
- Program nie obsługuje plików PDF zabezpieczonych hasłem
- OCR do DOCX nie jest wspierany – wynik OCR zapisywany jest jako TXT
- Jakość OCR zależy od jakości skanu

## Autor
Alan Steinbarth  
Wersja: 3.1 (OCR, preprocessing, nowoczesny GUI)  
Email: alan.steinbarth@gmail.com

## Licencja
Ten program jest dostępny na licencji open source.
