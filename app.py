# =============================================================================
# PDF to DOCX/TXT Converter with OCR
# Author: Alan Steinbarth
# Version: 3.1
# =============================================================================

# =============================================================================
# Imports and Configuration
# =============================================================================
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext
import logging
import os
import subprocess
import re
import shutil
import glob
import webbrowser
import importlib.util
from datetime import datetime
from pdfminer.high_level import extract_text
from PIL import Image, ImageTk, ImageFilter

# Dynamiczne importowanie modułów OCR
OCR_MODULES = {}
required_modules = ['pdf2docx', 'pdf2image', 'pytesseract']

for module in required_modules:
    try:
        if module == 'pdf2docx':
            from pdf2docx import Converter
            OCR_MODULES[module] = Converter
        elif module == 'pdf2image':
            from pdf2image import convert_from_path
            OCR_MODULES[module] = convert_from_path
        elif module == 'pytesseract':
            import pytesseract
            OCR_MODULES[module] = pytesseract
    except ImportError:
        OCR_MODULES[module] = None

# =============================================================================
# OCR Support Detection
# Sprawdzanie dostępności modułów OCR i konfiguracja fallback
# =============================================================================
OCR_AVAILABLE = False
try:
    if all(OCR_MODULES.values()):
        Converter = OCR_MODULES['pdf2docx']
        convert_from_path = OCR_MODULES['pdf2image']
        pytesseract = OCR_MODULES['pytesseract']
        OCR_AVAILABLE = True
except Exception as e:
    print(f"OCR-related modules not fully available: {e}")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# =============================================================================
# Main Application Class
# =============================================================================
class PDFtoDocxConverterApp(tk.Tk):
    """
    Główna klasa aplikacji konwertera PDF na DOCX/TXT.
    
    Funkcjonalności:
    - Konwersja plików PDF na DOCX lub TXT
    - Obsługa OCR dla zeskanowanych dokumentów
    - Podgląd tekstu i obrazu po preprocessingu
    - Wsadowa konwersja wielu plików
    - Drag & drop plików
    - Zaawansowany interfejs użytkownika
    """

    def __init__(self):
        super().__init__()
        self.title("Konwerter PDF -> DOCX")
        self.geometry("900x800")  # Zwiększona wysokość okna
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.pdf_path = None
        self.output_dir = r"C:\Users\aleks\OneDrive\Pulpit"
        self.use_ocr = tk.BooleanVar()
        self.output_format = tk.StringVar(value="docx")
        self.selected_files = []
        self.image_preview = None  # Do podglądu obrazu po preprocessingu
        self.create_menu()
        self.create_widgets()
        self.conversion_thread = None
        self.running = True
        self.log_handler = GuiLogHandler(self.log_text)
        logging.getLogger().addHandler(self.log_handler)
        self.enable_drag_and_drop()

    def enable_drag_and_drop(self):
        """
        Konfiguruje obsługę przeciągania i upuszczania plików (drag & drop).
        Używa natywnej obsługi Windows poprzez bindowanie zdarzeń.
        """
        self.file_list.bind('<Button-1>', self.on_drag_start)
        self.file_list.bind('<B1-Motion>', self.on_drag_motion)
        self.file_list.bind('<ButtonRelease-1>', self.on_drop)
        
    def on_drag_start(self, event):
        """Rozpoczęcie przeciągania"""
        self._drag_data = {'x': event.x, 'y': event.y, 'item': None}
        
    def on_drag_motion(self, event):
        """Obsługa ruchu podczas przeciągania"""
        pass
        
    def on_drop(self, event):
        """Obsługa upuszczenia - otwiera okno wyboru plików"""
        self.select_files()

    def on_drop_files(self, event):
        files = self.tk.splitlist(event.data)
        pdfs = [f for f in files if f.lower().endswith('.pdf')]
        if pdfs:
            self.add_files_to_list(pdfs)

    def add_files_to_list(self, file_paths):
        """
        Dodaje pliki PDF do listy konwersji.
        Aktualizuje interfejs i wyświetla podgląd pierwszego pliku.
        """
        for path in file_paths:
            abs_path = os.path.abspath(path)
            if abs_path not in self.selected_files and os.path.isfile(abs_path):
                self.selected_files.append(abs_path)
                self.file_list.insert(tk.END, os.path.basename(abs_path))
                self.add_log(f"Dodano plik: {os.path.basename(abs_path)}")
        if self.selected_files:
            self.convert_button.config(state=tk.NORMAL)
            self.update_status(f"Wybrano {len(self.selected_files)} plików")
            if len(self.selected_files) == 1:
                self.update_preview(self.selected_files[0])

    def create_widgets(self):
        """
        Tworzy i konfiguruje wszystkie widżety interfejsu użytkownika.
        Organizuje elementy w panele:
        - lewy: wybór plików, opcje konwersji, przyciski kontrolne
        - prawy: podgląd tekstu/obrazu, logi
        """
        main_container = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        left_frame = ttk.Frame(main_container)
        main_container.add(left_frame, weight=2)
        file_frame = ttk.LabelFrame(left_frame, text="Wybór plików PDF", padding=5)
        file_frame.pack(fill=tk.X, padx=5, pady=5)
        btn_frame = ttk.Frame(file_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="Dodaj pliki", command=self.select_files).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Usuń wybrane", command=self.remove_selected_file).pack(side=tk.LEFT, padx=2)
        list_frame = ttk.Frame(file_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        self.file_list = tk.Listbox(list_frame, height=8, selectmode=tk.EXTENDED)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.file_list.yview)
        self.file_list.configure(yscrollcommand=scrollbar.set)
        self.file_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        list_frame.update_idletasks()
        list_frame.config(width=900)  # Szerokość dla całej listy
        output_frame = ttk.LabelFrame(left_frame, text="Folder docelowy", padding=5)
        output_frame.pack(fill=tk.X, padx=5, pady=5)
        path_frame = ttk.Frame(output_frame)
        path_frame.pack(fill=tk.X, expand=True, padx=5)
        self.output_label = ttk.Label(path_frame, text=f"Folder zapisu: {self.output_dir}")
        self.output_label.pack(side=tk.LEFT, pady=5)
        btn_frame = ttk.Frame(output_frame)
        btn_frame.pack(fill=tk.X, padx=5)
        ttk.Button(btn_frame, text="Zmień folder", command=self.select_output_dir).pack(side=tk.LEFT, pady=5, padx=2)
        options_frame = ttk.LabelFrame(left_frame, text="Opcje konwersji", padding=5)
        options_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(options_frame, text="Format wyjściowy:").pack(anchor=tk.W)
        ttk.Radiobutton(options_frame, text="DOCX", variable=self.output_format, value="docx").pack(anchor=tk.W)
        ttk.Radiobutton(options_frame, text="TXT", variable=self.output_format, value="txt").pack(anchor=tk.W)
        control_frame = ttk.Frame(left_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        self.convert_button = ttk.Button(control_frame, text="Konwertuj", command=self.start_conversion, state=tk.NORMAL if self.selected_files else tk.DISABLED)
        self.convert_button.pack(pady=5)
        self.progress_bar = ttk.Progressbar(control_frame, length=300, mode='determinate')
        self.progress_bar.pack(pady=5, fill=tk.X)
        self.status_label = ttk.Label(control_frame, text="Status: Oczekiwanie")
        self.status_label.pack(pady=5)
        self.cancel_button = ttk.Button(control_frame, text="Anuluj", command=self.cancel_conversion, state=tk.DISABLED)
        self.cancel_button.pack(pady=5)
        right_frame = ttk.Frame(main_container)
        main_container.add(right_frame, weight=1)
        preview_frame = ttk.LabelFrame(right_frame, text="Podgląd tekstu", padding=5)
        preview_frame.pack(fill=tk.BOTH, expand=True)
        self.preview_text = scrolledtext.ScrolledText(preview_frame, height=10, wrap=tk.WORD)
        self.preview_text.pack(fill=tk.BOTH, expand=True)
        img_frame = ttk.LabelFrame(right_frame, text="Podgląd obrazu po preprocessingu", padding=5)
        img_frame.pack(fill=tk.BOTH, expand=False)
        self.img_canvas = tk.Canvas(img_frame, width=350, height=350, bg='white')
        self.img_canvas.pack(fill=tk.BOTH, expand=True)
        log_frame = ttk.LabelFrame(right_frame, text="Logi", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=False)
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        # Czyścimy logi na starcie
        self.log_text.delete('1.0', tk.END)
        info_frame = tk.Frame(self)
        info_frame.pack(fill="x", padx=5, pady=5)
        self.file_info_label = tk.Label(info_frame, text="", justify=tk.LEFT, wraplength=550)
        self.file_info_label.pack(pady=5)
        self.author_label = tk.Label(self, text="Autor: Alan Steinbarth", fg="gray")
        self.author_label.pack(side=tk.BOTTOM, pady=5)
        self.file_list.bind('<<ListboxSelect>>', self.on_file_select)

    def select_files(self):
        """
        Otwiera okno dialogowe wyboru plików PDF.
        """
        file_paths = filedialog.askopenfilenames(
            title="Wybierz pliki PDF",
            filetypes=[("PDF files", "*.pdf")],
            initialdir=self.output_dir
        )
        if file_paths:
            self.add_files_to_list(file_paths)

    def remove_selected_file(self):
        """
        Usuwa zaznaczone pliki z listy konwersji.
        """
        selection = list(self.file_list.curselection())
        if selection:
            for index in reversed(selection):
                removed_file = self.selected_files.pop(index)
                self.file_list.delete(index)
                self.add_log(f"Usunięto plik: {os.path.basename(removed_file)}")
            if not self.selected_files:
                self.convert_button.config(state=tk.DISABLED)
            self.update_status(f"Pozostało {len(self.selected_files)} plików")

    def clear_files(self):
        self.selected_files.clear()
        self.file_list.delete(0, tk.END)
        self.convert_button.config(state=tk.DISABLED)
        self.update_status("Wyczyszczono listę plików")

    def select_output_dir(self):
        """
        Otwiera okno dialogowe wyboru folderu docelowego.
        """
        directory = filedialog.askdirectory(title="Wybierz folder docelowy", initialdir=self.output_dir)
        if directory:
            self.output_dir = directory
            self.output_label.config(text=f"Folder zapisu: {self.output_dir}")
            self.update_status(f"Zmieniono folder zapisu na: {self.output_dir}")

    def on_closing(self):
        if self.conversion_thread and self.conversion_thread.is_alive():
            if messagebox.askokcancel("Wyjście", "Konwersja jest w toku. Czy na pewno chcesz zamknąć aplikację?"):
                self.running = False
                self.destroy()
        else:
            self.running = False
            self.destroy()

    def show_install_instructions(self):
        text = """INSTRUKCJA INSTALACJI\n\n1. Poppler:\n   - Pobierz Poppler dla Windows: https://github.com/oschwartz10612/poppler-windows/releases\n   - Rozpakuj do folderu, np. C:/Program Files/poppler\n   - Dodaj ścieżkę do bin do zmiennej PATH (np. .../poppler/Library/bin)\n\n2. Tesseract OCR:\n   - Pobierz Tesseract: https://github.com/tesseract-ocr/tesseract\n   - Zainstaluj i dodaj do PATH (np. C:/Program Files/Tesseract-OCR)\n   - Dla polskiego OCR doinstaluj język polski (pol)\n\n3. Wymagane biblioteki Python:\n   pip install pdf2docx pdf2image pytesseract pillow pdfminer.six\n"""
        win = tk.Toplevel(self)
        win.title("Instrukcja instalacji")
        win.geometry("650x400")
        text_widget = scrolledtext.ScrolledText(win, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_widget.insert(tk.END, text)
        text_widget.config(state=tk.DISABLED)
        ttk.Button(win, text="Zamknij", command=win.destroy).pack(pady=5)

    def show_author_info(self):
        messagebox.showinfo("O autorze", "Autor: Alan Steinbarth\nWersja: 3.1 (z fallback OCR)\nEmail: alan.steinbarth@gmail.com")

    def create_menu(self):
        menubar = tk.Menu(self)
        
        # Menu Plik
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Wybierz pliki", command=self.select_files)
        filemenu.add_command(label="Wybierz folder docelowy", command=self.select_output_dir)
        filemenu.add_separator()
        filemenu.add_command(label="Wyjście", command=self.on_closing)
        menubar.add_cascade(label="Plik", menu=filemenu)
        
        # Menu Pomoc
        helpmenu = tk.Menu(menubar, tearoff=0)
        helpmenu.add_command(label="Jak używać?", command=self.show_faq)
        helpmenu.add_command(label="FAQ", command=self.show_faq)
        helpmenu.add_command(label="O programie", command=self.show_about)
        helpmenu.add_command(label="O autorze", command=self.show_author_info)
        helpmenu.add_separator()
        helpmenu.add_command(label="Pobierz Poppler", command=lambda: self.open_url('https://github.com/oschwartz10612/poppler-windows/releases'))
        helpmenu.add_command(label="Pobierz Tesseract", command=lambda: self.open_url('https://github.com/tesseract-ocr/tesseract'))
        helpmenu.add_command(label="Instrukcja instalacji", command=self.show_install_instructions)
        menubar.add_cascade(label="Pomoc", menu=helpmenu)
        
        self.config(menu=menubar)

    def open_url(self, url):
        webbrowser.open(url)

    def show_faq(self):
        faq_text = """Często zadawane pytania (FAQ):

1. Co to jest OCR?
   OCR (Optical Character Recognition) to technologia rozpoznawania tekstu ze skanowanych dokumentów. 
   Pozwala na konwersję zeskanowanych dokumentów do edytowalnego tekstu.

2. Kiedy używać OCR?
   - Gdy konwertujesz zeskanowane dokumenty
   - Gdy PDF zawiera obrazy tekstu
   - Gdy standardowa konwersja nie wydobywa tekstu

3. Jaki format wybrać?
   - DOCX: zachowuje formatowanie, idealne dla dokumentów biurowych
   - TXT: czysty tekst, mniejsze pliki, bez formatowania

4. Dlaczego konwersja trwa długo?
   - Przy włączonym OCR proces trwa dłużej ze względu na analizę tekstu
   - Duże pliki lub wiele stron wydłużają czas konwersji

5. Co jeśli wynik nie jest idealny?
   - Sprawdź czy dokument nie jest zabezpieczony
   - Przy skanach użyj OCR
   - Jakość wyniku zależy od jakości dokumentu źródłowego

6. Jak dodać pliki?
   - Przeciągnij pliki PDF do listy lub użyj przycisku 'Wybierz pliki'
   - Możesz dodać cały folder PDF (wraz z podfolderami)

7. Jak usunąć pliki z listy?
   - Zaznacz jeden lub więcej plików i kliknij 'Usuń wybrane'

8. Gdzie pobrać Poppler i Tesseract?
   - Linki znajdziesz w menu Pomoc oraz w README.txt"""

        faq_window = tk.Toplevel(self)
        faq_window.title("FAQ - Często zadawane pytania")
        faq_window.geometry("650x500")
        
        text_widget = scrolledtext.ScrolledText(faq_window, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_widget.insert(tk.END, faq_text)
        text_widget.config(state=tk.DISABLED)
        ttk.Button(faq_window, text="Zamknij", command=faq_window.destroy).pack(pady=5)

    def show_about(self):
        about_text = """Konwerter PDF -> DOCX

Program służy do konwersji dokumentów PDF na format DOCX lub TXT.

Główne funkcje:
- Konwersja wielu plików jednocześnie
- Możliwość użycia OCR dla skanowanych dokumentów
- Wybór formatu wyjściowego (DOCX/TXT)
- Szczegółowe logi procesu konwersji
- Wsparcie dla polskich znaków

Wymagania systemowe:
- Python 3.x
- pdf2docx (podstawowa konwersja)
- OCR wymaga dodatkowych bibliotek
"""
        messagebox.showinfo("O programie", about_text)

    def start_conversion(self):
        if not self.selected_files:
            messagebox.showwarning("Uwaga", "Nie wybrano żadnych plików!")
            return
        if not self.check_poppler():
            return
        self.convert_button.config(state=tk.DISABLED)
        self.cancel_button.config(state=tk.NORMAL)
        self.progress_bar['value'] = 0
        self.progress_bar['maximum'] = len(self.selected_files)
        self.update_status("Konwersja w toku...")
        self.conversion_thread = threading.Thread(target=self.convert_pdfs, daemon=True)
        self.conversion_thread.start()

    def cancel_conversion(self):
        """Ustawia flagę przerwania konwersji"""
        self.running = False
        self.add_log("Przerwano konwersję przez użytkownika.")
        self.update_status("Konwersja przerwana")
        self.cancel_button.config(state=tk.DISABLED)
        self.convert_button.config(state=tk.NORMAL)

    def convert_pdfs(self):
        """
        Główna funkcja konwersji plików PDF.
        Obsługuje:
        - Konwersję do DOCX/TXT
        - OCR dla skanów
        - Przetwarzanie wsadowe
        - Obsługę błędów
        """
        errors = []
        converted = []
        for idx, pdf_path in enumerate(self.selected_files):
            if not self.running:
                self.add_log("Konwersja została anulowana.")
                break
            basename = os.path.basename(pdf_path)
            try:
                self.update_status(f"Konwersja {idx + 1}/{len(self.selected_files)}")
                self.add_log(f"Rozpoczęto konwersję: {basename}")
                output_ext = ".docx" if self.output_format.get() == "docx" else ".txt"
                output_path = os.path.join(self.output_dir, os.path.splitext(basename)[0] + output_ext)
                needs_ocr = OCR_AVAILABLE and self.needs_ocr(pdf_path)
                if os.path.exists(output_path):
                    overwrite = messagebox.askyesno(
                        "Plik już istnieje",
                        f"Plik {os.path.basename(output_path)} już istnieje. Czy chcesz go nadpisać?"
                    )
                    if not overwrite:
                        self.add_log(f"Pominięto konwersję {basename} (plik już istnieje)")
                        self.progress_bar['value'] = idx + 1
                        continue
                if needs_ocr:
                    self.add_log(f"Używam OCR dla: {basename}")
                    images = convert_from_path(pdf_path, dpi=500)
                    self.add_log(f"Znaleziono {len(images)} stron w: {basename}")
                    if output_ext == ".docx":
                        self.add_log("OCR do DOCX nie jest wspierany. Zapisuję wynik OCR do pliku TXT.")
                        output_ext = ".txt"
                        output_path = os.path.join(self.output_dir, os.path.splitext(basename)[0] + output_ext)
                        messagebox.showinfo("OCR do DOCX", f"Plik {basename} to skan. Wynik OCR zostanie zapisany jako TXT.")
                    all_text = []
                    for page_num, img in enumerate(images, 1):
                        if not self.running:
                            self.add_log("Anulowano podczas OCR.")
                            break
                        self.add_log(f"OCR strony {page_num}/{len(images)}")
                        img = img.convert('L')
                        try:
                            from PIL import ImageFilter
                            img = img.filter(ImageFilter.SHARPEN)
                        except Exception:
                            pass
                        img = img.point(lambda x: 0 if x < 180 else 255, '1')
                        custom_config = r'--psm 6'
                        text = pytesseract.image_to_string(img, lang='pol+eng', config=custom_config)
                        text = self.clean_ocr_text(text)
                        all_text.append(text)
                    if self.running and all_text:
                        with open(output_path, 'w', encoding='utf-8') as f:
                            f.write("\n\n".join(all_text))
                        self.add_log(f"Plik TXT został zapisany: {os.path.basename(output_path)}")
                elif output_ext == ".docx":
                    if not self.running:
                        self.add_log("Anulowano przed konwersją do DOCX.")
                        break
                    cv = Converter(pdf_path)
                    cv.convert(output_path)
                    cv.close()
                else:
                    if not self.running:
                        self.add_log("Anulowano przed konwersją do TXT.")
                        break
                    self.add_log(f"Konwertuję {basename} do TXT...")
                    try:
                        text = extract_text(pdf_path)
                        text = self.clean_pdfminer_text(text)
                        with open(output_path, 'w', encoding='utf-8') as f:
                            f.write(text)
                        self.add_log(f"Plik TXT został zapisany: {os.path.basename(output_path)}")
                    except Exception as e:
                        raise Exception(f"Błąd konwersji do TXT: {str(e)}")
                if self.running and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    converted.append(output_path)
                    self.add_log(f"Pomyślnie zapisano: {os.path.basename(output_path)}")
                elif not self.running:
                    self.add_log("Anulowano przed zakończeniem pliku.")
                    break
                else:
                    raise Exception("Plik wyjściowy nie został utworzony")
                self.progress_bar['value'] = idx + 1
            except Exception as e:
                error_msg = f"Błąd podczas konwersji {basename}: {str(e)}"
                self.add_log(f"BŁĄD: {error_msg}")
                errors.append((basename, str(e)))
                continue
        self.progress_bar.stop()
        self.cancel_button.config(state=tk.DISABLED)
        self.convert_button.config(state=tk.NORMAL)
        self.running = True
        if errors:
            error_msg = "\n".join([f"- {name}: {err}" for name, err in errors])
            messagebox.showerror(
                "Błędy konwersji",
                f"Wystąpiły błędy podczas konwersji {len(errors)} plików:\n{error_msg}\n\n"
                f"Pomyślnie przekonwertowano {len(converted)} z {len(self.selected_files)} plików."
            )
        elif self.running:
            success_msg = (
                f"Wszystkie pliki zostały przekonwertowane!\n"
                f"Lokalizacja: {self.output_dir}\n\n"
                f"Czy chcesz otworzyć folder z przekonwertowanymi plikami?"
            )
            if messagebox.askyesno("Sukces", success_msg):
                self.open_output_dir()
        self.update_status(
            f"Zakończono: {len(converted)} z {len(self.selected_files)} plików"
        )

    def update_status(self, message):
        """Aktualizuje status w interfejsie"""
        self.status_label.config(text=f"Status: {message}")
        self.add_log(message)

    def needs_ocr(self, pdf_path):
        """
        Analizuje plik PDF aby określić czy wymaga OCR.
        Sprawdza:
        - Ilość tekstu w pliku
        - Proporcję tekstu do białych znaków
        - Jakość tekstu
        """
        try:
            # Próbujemy wydobyć tekst standardową metodą
            text = extract_text(pdf_path)
            # Jeśli tekst jest pusty lub zawiera bardzo mało znaków, prawdopodobnie potrzebuje OCR
            if len(text.strip()) < 100:
                self.add_log(f"Wykryto skan lub obraz - będzie użyte OCR")
                return True
                
            # Sprawdzamy proporcję tekstu do białych znaków
            text_chars = sum(1 for c in text if c.strip())
            if text_chars / len(text) < 0.1:  # Jeśli mniej niż 10% to znaki tekstowe
                self.add_log(f"Wykryto niską jakość tekstu - będzie użyte OCR")
                return True
                
            self.add_log(f"Wykryto dobrej jakości tekst - OCR nie jest potrzebne")
            return False
        except Exception as e:
            self.add_log(f"Błąd podczas analizy pliku - na wszelki wypadek użyję OCR: {str(e)}")
            return True

    def open_output_dir(self):
        """Otwiera folder z przekonwertowanymi plikami"""
        if os.path.exists(self.output_dir):
            subprocess.run(['explorer', self.output_dir])
        else:
            messagebox.showerror("Błąd", "Folder docelowy nie istnieje!")

    # =============================================================================
    # Text Processing
    # =============================================================================
    def clean_ocr_text(self, text):
        """
        Czyści tekst po OCR:
        - Usuwa nadmiarowe spacje i tabulatory
        - Zachowuje podział na akapity
        - Poprawia interpunkcję
        """
        # Usuwanie podwójnych spacji i tabulatorów, ale nie łączymy linii
        text = re.sub(r'[ \t]+', ' ', text)
        # Usuwanie nadmiarowych pustych linii (więcej niż 2)
        text = re.sub(r'\n{3,}', '\n\n', text)
        # Usuwanie spacji przed znakami interpunkcyjnymi
        text = re.sub(r'\s+([.,!?;:])', r'\1', text)
        return text.strip()

    def clean_pdfminer_text(self, text):
        """
        Czyści tekst po pdfminer:
        - Usuwa nadmiarowe spacje i tabulatory
        - Zachowuje podział na akapity
        - Poprawia interpunkcję
        """
        # Usuwanie podwójnych spacji i tabulatorów, ale nie łączymy linii
        text = re.sub(r'[ \t]+', ' ', text)
        # Usuwanie nadmiarowych pustych linii (więcej niż 2)
        text = re.sub(r'\n{3,}', '\n\n', text)
        # Usuwanie spacji przed znakami interpunkcyjnymi
        text = re.sub(r'\s+([.,!?;:])', r'\1', text)
        return text.strip()

    # =============================================================================
    # System Integration
    # =============================================================================
    def check_poppler(self):
        """
        Sprawdza dostępność Poppler:
        - Szuka w PATH
        - Szuka w AppData
        - Automatycznie dodaje do PATH
        - Wyświetla instrukcje instalacji
        """
        # Sprawdź czy Poppler jest w PATH
        if shutil.which('pdftocairo'):
            return True

        # Sprawdź Poppler w AppData (z uwzględnieniem podkatalogu wersji)
        poppler_base = os.path.expandvars(r'%USERPROFILE%\AppData\Local\Programs\poppler')
        if os.path.exists(poppler_base):
            # Znajdź najnowszy katalog Poppler (np. poppler-24.02.0)
            poppler_dirs = glob.glob(os.path.join(poppler_base, 'poppler-*'))
            if poppler_dirs:
                latest_poppler = max(poppler_dirs)  # Bierzemy najnowszą wersję
                bin_path = os.path.join(latest_poppler, 'Library', 'bin')
                if os.path.exists(os.path.join(bin_path, 'pdftocairo.exe')):
                    # Dodaj ścieżkę do PATH
                    os.environ['PATH'] = bin_path + os.pathsep + os.environ['PATH']
                    return True

        # Jeśli nie znaleziono, pokaż komunikat
        messagebox.showerror(
            "Błąd",
            "Nie znaleziono Poppler w zmiennej PATH.\n\n"
            "1. Poppler powinien być w jednej z lokalizacji:\n"
            "   - W zmiennej PATH\n"
            "   - W folderze AppData\\Local\\Programs\\poppler\n\n"
            "2. Jeśli nie masz Poppler:\n"
            "   - Pobierz ze strony: github.com/oschwartz10612/poppler-windows/releases\n"
            "   - Rozpakuj do folderu AppData\\Local\\Programs\\poppler"
        )
        if messagebox.askyesno("Pobierz Poppler", "Czy chcesz otworzyć stronę pobierania Poppler?"):
            self.open_url('https://github.com/oschwartz10612/poppler-windows/releases')
        return False

    def preview_pdf(self, pdf_path):
        """Wyświetla podgląd tekstu z pliku PDF"""
        try:
            # Próbujemy wydobyć tekst
            text = extract_text(pdf_path)
            if not text.strip():
                self.preview_text.delete('1.0', tk.END)
                self.preview_text.insert(tk.END, "[Ten PDF prawdopodobnie zawiera tylko obrazy - będzie użyte OCR]")
            else:
                self.preview_text.delete('1.0', tk.END)
                self.preview_text.insert(tk.END, text[:1000] + "\n\n[...]\n(pokazano pierwsze 1000 znaków)")
            
            # Aktualizujemy informacje o pliku
            file_size = os.path.getsize(pdf_path) / (1024 * 1024)  # Rozmiar w MB
            self.file_info_label.config(
                text=f"Wybrany plik: {os.path.basename(pdf_path)}\n"
                f"Rozmiar: {file_size:.2f} MB\n"
                f"Lokalizacja: {os.path.dirname(pdf_path)}"
            )
        except Exception as e:
            self.preview_text.delete('1.0', tk.END)
            self.preview_text.insert(tk.END, f"Błąd podglądu: {str(e)}")

    def preview_preprocessed_image(self, image):
        """
        Wyświetla podgląd przetworzonego obrazu w canvas.
        - Skaluje obraz zachowując proporcje
        - Centruje w obszarze wyświetlania
        - Obsługuje błędy wyświetlania
        """
        if hasattr(self, 'img_canvas'):
            self.img_canvas.delete('all')
            if image:
                try:
                    # Przeskaluj obraz do rozmiaru canvas z zachowaniem proporcji
                    canvas_width = self.img_canvas.winfo_width()
                    canvas_height = self.img_canvas.winfo_height()
                    
                    # Oblicz skalę zachowując proporcje
                    scale = min(canvas_width/image.width, canvas_height/image.height)
                    new_width = int(image.width * scale)
                    new_height = int(image.height * scale)
                    
                    # Przeskaluj obraz
                    image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    
                    # Konwertuj na format wyświetlania
                    photo = ImageTk.PhotoImage(image)
                    
                    # Zapamiętaj referencję (ważne!)
                    self.image_preview = photo
                    
                    # Wycentruj obraz na canvas
                    x = (canvas_width - new_width) // 2
                    y = (canvas_height - new_height) // 2
                    
                    # Wyświetl obraz
                    self.img_canvas.create_image(x, y, anchor=tk.NW, image=photo)
                    
                except Exception as e:
                    self.add_log(f"Błąd podczas wyświetlania podglądu: {str(e)}")

    def update_preview(self, pdf_path):
        """
        Aktualizuje podgląd tekstu i obrazu dla wybranego pliku PDF.
        - Wyświetla tekst lub informację o OCR
        - Generuje podgląd pierwszej strony dla skanów
        - Aktualizuje informacje o pliku
        """
        try:
            # Podgląd tekstu (istniejący kod)
            text = extract_text(pdf_path)
            if not text.strip():
                self.preview_text.delete('1.0', tk.END)
                self.preview_text.insert(tk.END, "[Ten PDF prawdopodobnie zawiera tylko obrazy - będzie użyte OCR]")
                
                # Dodaj podgląd pierwszej strony jako obraz
                if OCR_AVAILABLE:
                    try:
                        images = convert_from_path(pdf_path, dpi=200, first_page=1, last_page=1)
                        if images:
                            first_page = images[0]
                            # Konwersja do skali szarości
                            first_page = first_page.convert('L')
                            # Wyostrzenie
                            from PIL import ImageFilter
                            first_page = first_page.filter(ImageFilter.SHARPEN)
                            # Binaryzacja
                            first_page = first_page.point(lambda x: 0 if x < 180 else 255, '1')
                            self.preview_preprocessed_image(first_page)
                    except Exception as e:
                        self.add_log(f"Błąd podczas generowania podglądu obrazu: {str(e)}")
            else:
                self.preview_text.delete('1.0', tk.END)
                self.preview_text.insert(tk.END, text[:1000] + "\n\n[...]\n(pokazano pierwsze 1000 znaków)")
                # Wyczyść podgląd obrazu
                self.preview_preprocessed_image(None)
            
            # Aktualizacja informacji o pliku
            file_size = os.path.getsize(pdf_path) / (1024 * 1024)  # Rozmiar w MB
            self.file_info_label.config(
                text=f"Wybrany plik: {os.path.basename(pdf_path)}\n"
                f"Rozmiar: {file_size:.2f} MB\n"
                f"Lokalizacja: {os.path.dirname(pdf_path)}"
            )
        except Exception as e:
            self.preview_text.delete('1.0', tk.END)
            self.preview_text.insert(tk.END, f"Błąd podglądu: {str(e)}")
            self.preview_preprocessed_image(None)
    
    def on_file_select(self, event):
        """Obsługa zdarzenia wyboru pliku z listy"""
        selection = self.file_list.curselection()
        if selection:
            selected_index = selection[0]
            selected_file = self.selected_files[selected_index]
            self.update_preview(selected_file)

    # =============================================================================
    # Logging
    # =============================================================================
    def add_log(self, message):
        """
        Dodaje wpis do logów z timestampem.
        Automatycznie przewija do najnowszego wpisu.
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        
class GuiLogHandler(logging.Handler):
    """
    Handler do przekierowania logów do GUI.
    Integruje systemowy logging z interfejsem użytkownika.
    """
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.text_widget.insert(tk.END, f"[{timestamp}] {msg}\n")
        self.text_widget.see(tk.END)

if __name__ == "__main__":
    app = PDFtoDocxConverterApp()
    app.mainloop()
