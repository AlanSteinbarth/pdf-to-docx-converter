# Jak pomóc w rozwoju projektu

Dziękuję za zainteresowanie projektem konwertera PDF! Oto wskazówki jak możesz pomóc w jego rozwoju.

## Zgłaszanie błędów

1. Sprawdź czy błąd nie został już zgłoszony w zakładce Issues
2. Używaj szablonu zgłoszenia błędu, zawierającego:
   - Opis problemu
   - Kroki do odtworzenia
   - Oczekiwane zachowanie
   - Rzeczywiste zachowanie
   - Zrzuty ekranu (jeśli pomocne)
   - Informacje o systemie operacyjnym i wersjach:
     - Python
     - Poppler
     - Tesseract OCR
     - Używane biblioteki

## Proponowanie zmian

1. Zrób fork repozytorium
2. Stwórz nową gałąź dla swoich zmian (`git checkout -b feature/nazwa-funkcji`)
3. Wprowadź zmiany
4. Przetestuj zmiany
5. Utwórz pull request z opisem zmian

## Standardy kodowania

1. Używaj PEP 8 do formatowania kodu Python
2. Dodawaj komentarze w języku polskim
3. Wszystkie funkcje powinny mieć docstringi
4. Zachowaj istniejącą strukturę sekcji w kodzie:
   - Imports and Configuration
   - OCR Support Detection
   - Main Application Class
   - GUI Components
   - File Management
   - Conversion Logic
   - Text Processing
   - System Integration
   - Logging
5. Używaj znaczących nazw zmiennych i funkcji

## Testowanie

1. Przetestuj zmiany na różnych systemach operacyjnych
2. Sprawdź konwersję różnych typów PDF:
   - PDF z tekstem
   - Skany dokumentów
   - PDF z obrazami i tekstem
   - PDF w różnych językach
3. Przetestuj interfejs użytkownika:
   - Drag & drop
   - Podgląd tekstu i obrazu
   - Obsługa błędów
   - Anulowanie konwersji
4. Upewnij się, że nie wprowadzasz regresji

## Kontakt

Jeśli masz pytania lub potrzebujesz pomocy:
1. Utwórz Issue w projekcie
2. Opisz dokładnie swój problem lub propozycję
3. Bądź cierpliwy - postaramy się odpowiedzieć jak najszybciej

## Licencja

Projekt jest dostępny na licencji MIT. Twoje kontrybucje również będą objęte tą licencją.
