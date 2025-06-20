# Współtworzenie i zgłaszanie błędów

Dziękujemy za zainteresowanie rozwojem konwertera PDF -> DOCX/TXT!

## Jak zgłosić błąd lub sugestię
1. Utwórz Issue na GitHubie (opisz problem, system, wersję, logi).
2. Dołącz przykładowy plik PDF, jeśli to możliwe.
3. Sprawdź, czy masz zainstalowane Poppler i Tesseract oraz wymagane biblioteki Python.

## Jak rozwijać projekt
1. Forkuj repozytorium
2. Utwórz nowy branch (np. `feature/nazwa-funkcji`)
3. Wprowadź zmiany, przetestuj na różnych systemach
4. **Sprawdź jakość kodu**: `python3 -m pylint app.py --score=y` (cel: 8.0+/10)
5. **Uruchom testy**: `python3 -m pytest tests/ -v`
6. Zaktualizuj README.md i CHANGELOG.md
7. Otwórz Pull Request

## Standardy Jakości Kodu
- **Pylint Score**: minimum 8.0/10 (obecnie: 8.65/10)
- **Docstrings**: markdown-style documentation dla wszystkich funkcji
- **PEP 8**: compliance z Python style guide
- **Error Handling**: comprehensive exception handling
- **Code Structure**: logiczne sekcje z opisami
- **Import Order**: standard library first, third-party, local imports

## Testowanie
- Przetestuj konwersję PDF z tekstem, skanów, zdjęć, plików wielostronicowych
- Sprawdź interfejs na macOS, Windows, Linux
- Upewnij się, że OCR działa (log: "Tesseract OCR został pomyślnie zainicjowany.")
- Sprawdź logi, podgląd PDF, anulowanie konwersji

## Kontakt
- Autor: Alan Steinbarth
- Zgłoszenia: przez Issues na GitHubie
