# =============================================================================
# PDF to DOCX/TXT Converter with OCR
# Author: Alan Steinbarth
# Version: 3.2 - Cross-platform support (Windows, macOS, Linux)
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
import platform
from datetime import datetime
from pdfminer.high_level import extract_text

# Dynamiczne importowanie modułów OCR
OCR_MODULES = {}
required_modules = ['pdf2docx', 'pdf2image', 'pytesseract', 'PIL']

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
        elif module == 'PIL':
            from PIL import Image
            OCR_MODULES[module] = Image
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
        Image = OCR_MODULES['PIL']
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
    - Wieloplatformowość (Windows, macOS, Linux)
    """

    def get_default_output_dir(self):
        """Określa domyślny folder wyjściowy w zależności od systemu operacyjnego"""
        system = platform.system()
        try:
            if system == "Windows":
                # Windows: próbuj Pulpit z OneDrive lub lokalny pulpit
                onedrive_desktop = os.path.expanduser("~/OneDrive/Pulpit")
                local_desktop = os.path.expanduser("~/Desktop")
                if os.path.exists(onedrive_desktop):
                    return onedrive_desktop
                elif os.path.exists(local_desktop):
                    return local_desktop
                else:
                    return os.path.expanduser("~")
            elif system == "Darwin":  # macOS
                desktop = os.path.expanduser("~/Desktop")
                return desktop if os.path.exists(desktop) else os.path.expanduser("~")
            else:  # Linux i inne systemy Unix
                desktop = os.path.expanduser("~/Desktop")
                return desktop if os.path.exists(desktop) else os.path.expanduser("~")
        except Exception:
            return os.path.expanduser("~")  # Fallback na folder domowy

    def __init__(self):
        super().__init__()
        self.title("Konwerter PDF -> DOCX")
        self.geometry("900x800")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.pdf_path = None
        
        # Ustawienie domyślnego folderu na pulpit w zależności od systemu
        self.output_dir = self.get_default_output_dir()
        
        self.use_ocr = tk.BooleanVar()
        self.output_format = tk.StringVar(value="docx")
        self.selected_files = []
        self.image_preview = None
        self.create_menu()
        self.create_widgets()
        self.conversion_thread = None
        self.running = True
        self.log_handler = GuiLogHandler(self.log_text)
        logging.getLogger().addHandler(self.log_handler)
        self.enable_drag_and_drop()

    def enable_drag_and_drop(self):
        """Konfiguruje obsługę przeciągania i upuszczania plików"""
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

    def add_files_to_list(self, file_paths):
        """Dodaje pliki PDF do listy konwersji"""
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
        """Tworzy wszystkie widżety interfejsu"""
        main_container = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Panel lewy
        left_frame = ttk.Frame(main_container)
        main_container.add(left_frame, weight=2)

        # Sekcja wyboru plików
        file_frame = ttk.LabelFrame(left_frame, text="Wybór plików PDF", padding=5)
        file_frame.pack(fill=tk.X, padx=5, pady=5)

        btn_frame = ttk.Frame(file_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="Dodaj pliki", command=self.select_files).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Usuń wybrane", command=self.remove_selected_file).pack(side=tk.LEFT, padx=2)

        # Lista plików
        list_frame = ttk.Frame(file_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        self.file_list = tk.Listbox(list_frame, height=8, selectmode=tk.EXTENDED)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.file_list.yview)
        self.file_list.configure(yscrollcommand=scrollbar.set)
        self.file_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Folder docelowy
        output_frame = ttk.LabelFrame(left_frame, text="Folder docelowy", padding=5)
        output_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.output_label = ttk.Label(output_frame, text=f"Folder zapisu: {self.output_dir}")
        self.output_label.pack(side=tk.LEFT, pady=5)
        
        ttk.Button(output_frame, text="Zmień folder", command=self.select_output_dir).pack(side=tk.RIGHT, pady=5, padx=2)

        # Opcje konwersji
        options_frame = ttk.LabelFrame(left_frame, text="Opcje konwersji", padding=5)
        options_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(options_frame, text="Format wyjściowy:").pack(anchor=tk.W)
        ttk.Radiobutton(options_frame, text="DOCX", variable=self.output_format, value="docx").pack(anchor=tk.W)
        ttk.Radiobutton(options_frame, text="TXT", variable=self.output_format, value="txt").pack(anchor=tk.W)

        # Kontrola konwersji
        control_frame = ttk.Frame(left_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.convert_button = ttk.Button(control_frame, text="Konwertuj", command=self.start_conversion, 
                                       state=tk.NORMAL if self.selected_files else tk.DISABLED)
        self.convert_button.pack(pady=5)
        
        self.progress_bar = ttk.Progressbar(control_frame, length=300, mode='determinate')
        self.progress_bar.pack(pady=5, fill=tk.X)
        
        self.status_label = ttk.Label(control_frame, text="Status: Oczekiwanie")
        self.status_label.pack(pady=5)
        
        self.cancel_button = ttk.Button(control_frame, text="Anuluj", command=self.cancel_conversion, state=tk.DISABLED)
        self.cancel_button.pack(pady=5)

        # Panel prawy
        right_frame = ttk.Frame(main_container)
        main_container.add(right_frame, weight=1)

        # Podgląd tekstu
        preview_frame = ttk.LabelFrame(right_frame, text="Podgląd tekstu", padding=5)
        preview_frame.pack(fill=tk.BOTH, expand=True)
        self.preview_text = scrolledtext.ScrolledText(preview_frame, height=10, wrap=tk.WORD)
        self.preview_text.pack(fill=tk.BOTH, expand=True)

        # Logi
        log_frame = ttk.LabelFrame(right_frame, text="Logi", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=False)
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Informacje
        self.file_info_label = tk.Label(self, text="", justify=tk.LEFT, wraplength=550)
        self.file_info_label.pack(pady=5)
        
        self.author_label = tk.Label(self, text="Autor: Alan Steinbarth", fg="gray")
        self.author_label.pack(side=tk.BOTTOM, pady=5)

        self.file_list.bind('<<ListboxSelect>>', self.on_file_select)

    def on_file_select(self, event):
        """Obsługuje wybór pliku z listy"""
        selection = self.file_list.curselection()
        if selection:
            selected_index = selection[0]
            selected_file = self.selected_files[selected_index]
            self.update_preview(selected_file)

    def update_preview(self, pdf_path):
        """Aktualizuje podgląd tekstu dla wybranego pliku"""
        try:
            text = extract_text(pdf_path)
            preview = text[:1000] + "..." if len(text) > 1000 else text
            self.preview_text.delete('1.0', tk.END)
            self.preview_text.insert('1.0', preview)
        except Exception as e:
            self.preview_text.delete('1.0', tk.END)
            self.preview_text.insert('1.0', f"Błąd podczas podglądu: {str(e)}")

    def add_log(self, message):
        """Dodaje wpis do logów"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)

    def select_files(self):
        """Otwiera okno dialogowe wyboru plików PDF"""
        file_paths = filedialog.askopenfilenames(
            title="Wybierz pliki PDF",
            filetypes=[("PDF files", "*.pdf")],
            initialdir=self.output_dir
        )
        if file_paths:
            self.add_files_to_list(file_paths)

    def remove_selected_file(self):
        """Usuwa zaznaczone pliki z listy konwersji"""
        selection = list(self.file_list.curselection())
        if selection:
            for index in reversed(selection):
                removed_file = self.selected_files.pop(index)
                self.file_list.delete(index)
                self.add_log(f"Usunięto plik: {os.path.basename(removed_file)}")
            if not self.selected_files:
                self.convert_button.config(state=tk.DISABLED)
            self.update_status(f"Pozostało {len(self.selected_files)} plików")

    def select_output_dir(self):
        """Otwiera okno dialogowe wyboru folderu docelowego"""
        directory = filedialog.askdirectory(title="Wybierz folder docelowy", initialdir=self.output_dir)
        if directory:
            self.output_dir = directory
            self.output_label.config(text=f"Folder zapisu: {self.output_dir}")
            self.update_status(f"Zmieniono folder zapisu na: {self.output_dir}")

    def on_closing(self):
        """Obsługuje zamykanie aplikacji"""
        if self.conversion_thread and self.conversion_thread.is_alive():
            if messagebox.askokcancel("Wyjście", "Konwersja jest w toku. Czy na pewno chcesz zamknąć aplikację?"):
                self.running = False
                self.destroy()
        else:
            self.running = False
            self.destroy()

    def show_install_instructions(self):
        """Wyświetla instrukcje instalacji specyficzne dla systemu operacyjnego"""
        system = platform.system()
        
        if system == "Windows":
            text = """INSTRUKCJA INSTALACJI - WINDOWS

1. Poppler:
   - Pobierz Poppler dla Windows: https://github.com/oschwartz10612/poppler-windows/releases
   - Rozpakuj do folderu, np. C:/Program Files/poppler
   - Dodaj ścieżkę do bin do zmiennej PATH (np. .../poppler/Library/bin)

2. Tesseract OCR:
   - Pobierz Tesseract: https://github.com/tesseract-ocr/tesseract
   - Zainstaluj i dodaj do PATH (np. C:/Program Files/Tesseract-OCR)
   - Dla polskiego OCR doinstaluj język polski (pol)

3. Wymagane biblioteki Python:
   pip install pdf2docx pdf2image pytesseract pillow pdfminer.six
"""
        elif system == "Darwin":  # macOS
            text = """INSTRUKCJA INSTALACJI - macOS

1. Poppler (przez Homebrew):
   brew install poppler
   
   Alternatywnie (MacPorts):
   sudo port install poppler

2. Tesseract OCR:
   brew install tesseract
   brew install tesseract-lang
   
   Dla polskiego OCR:
   Języki są już włączone w Homebrew

3. Wymagane biblioteki Python:
   pip install pdf2docx pdf2image pytesseract pillow pdfminer.six

4. Jeśli nie masz Homebrew:
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
"""
        else:  # Linux
            text = """INSTRUKCJA INSTALACJI - LINUX

1. Poppler (Ubuntu/Debian):
   sudo apt-get update
   sudo apt-get install poppler-utils
   
   (CentOS/RHEL/Fedora):
   sudo yum install poppler-utils  # lub dnf install

2. Tesseract OCR:
   sudo apt-get install tesseract-ocr tesseract-ocr-pol tesseract-ocr-eng
   
   (CentOS/RHEL/Fedora):
   sudo yum install tesseract tesseract-langpack-pol tesseract-langpack-eng

3. Wymagane biblioteki Python:
   pip install pdf2docx pdf2image pytesseract pillow pdfminer.six
   
   Lub (dla systemów z pip3):
   pip3 install pdf2docx pdf2image pytesseract pillow pdfminer.six
"""
        
        win = tk.Toplevel(self)
        win.title(f"Instrukcja instalacji - {system}")
        win.geometry("750x500")
        text_widget = scrolledtext.ScrolledText(win, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_widget.insert(tk.END, text)
        text_widget.config(state=tk.DISABLED)
        ttk.Button(win, text="Zamknij", command=win.destroy).pack(pady=5)

    def show_author_info(self):
        """Wyświetla informacje o autorze wraz z informacjami o systemie"""
        system_info = f"System: {platform.system()} {platform.release()}"
        messagebox.showinfo("O autorze", 
                          f"Autor: Alan Steinbarth\nWersja: 3.2 (wieloplatformowa)\nEmail: alan.steinbarth@gmail.com\n{system_info}")

    def create_menu(self):
        """Tworzy menu aplikacji"""
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
        """Otwiera URL w przeglądarce"""
        webbrowser.open(url)

    def show_faq(self):
        """Wyświetla FAQ"""
        faq_text = """Często zadawane pytania (FAQ):

1. Na jakich systemach operacyjnych działa program?
   Program działa na Windows, macOS i Linux z automatyczną detekcją systemu operacyjnego.

2. Co to jest OCR?
   OCR (Optical Character Recognition) to technologia rozpoznawania tekstu ze skanowanych dokumentów.

3. Kiedy używać OCR?
   - Gdy konwertujesz zeskanowane dokumenty
   - Gdy PDF zawiera obrazy tekstu
   - Gdy standardowa konwersja nie wydobywa tekstu

4. Jaki format wybrać?
   - DOCX: zachowuje formatowanie, idealne dla dokumentów biurowych
   - TXT: czysty tekst, mniejsze pliki, bez formatowania

5. Dlaczego konwersja trwa długo?
   - Przy włączonym OCR proces trwa dłużej ze względu na analizę tekstu
   - Duże pliki lub wiele stron wydłużają czas konwersji

6. Jak dodać pliki?
   - Przeciągnij pliki PDF do listy lub użyj przycisku 'Wybierz pliki'

7. Jak usunąć pliki z listy?
   - Zaznacz jeden lub więcej plików i kliknij 'Usuń wybrane'

8. Gdzie pobrać Poppler i Tesseract?
   - Linki znajdziesz w menu Pomoc oraz w README.md"""

        faq_window = tk.Toplevel(self)
        faq_window.title("FAQ - Często zadawane pytania")
        faq_window.geometry("650x500")
        
        text_widget = scrolledtext.ScrolledText(faq_window, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_widget.insert(tk.END, faq_text)
        text_widget.config(state=tk.DISABLED)
        ttk.Button(faq_window, text="Zamknij", command=faq_window.destroy).pack(pady=5)

    def show_about(self):
        """Wyświetla informacje o programie"""
        about_text = """Konwerter PDF -> DOCX

Program służy do konwersji dokumentów PDF na format DOCX lub TXT.

Główne funkcje:
- Konwersja wielu plików jednocześnie
- Możliwość użycia OCR dla skanowanych dokumentów
- Wybór formatu wyjściowego (DOCX/TXT)
- Szczegółowe logi procesu konwersji
- Wsparcie dla polskich znaków
- Wieloplatformowość (Windows, macOS, Linux)

Wymagania systemowe:
- Python 3.x
- pdf2docx (podstawowa konwersja)
- OCR wymaga dodatkowych bibliotek
"""
        messagebox.showinfo("O programie", about_text)

    def start_conversion(self):
        """Rozpoczyna konwersję plików"""
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
        """Anuluje konwersję"""
        self.running = False
        self.add_log("Przerwano konwersję przez użytkownika.")
        self.update_status("Konwersja przerwana")
        self.cancel_button.config(state=tk.DISABLED)
        self.convert_button.config(state=tk.NORMAL)

    def convert_pdfs(self):
        """Główna funkcja konwersji plików PDF"""
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
                
                # Sprawdź czy plik już istnieje
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
                    self.convert_with_ocr(pdf_path, output_path, output_ext)
                elif output_ext == ".docx":
                    self.convert_to_docx(pdf_path, output_path)
                else:
                    self.convert_to_txt(pdf_path, output_path)
                
                if self.running and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    converted.append(output_path)
                    self.add_log(f"Pomyślnie zapisano: {os.path.basename(output_path)}")
                elif not self.running:
                    break
                else:
                    errors.append((basename, "Plik nie został utworzony lub jest pusty"))
                
                self.progress_bar['value'] = idx + 1
                
            except Exception as e:
                error_msg = f"Błąd podczas konwersji {basename}: {str(e)}"
                self.add_log(f"BŁĄD: {error_msg}")
                errors.append((basename, str(e)))
                continue

        # Zakończenie konwersji
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

        self.update_status(f"Zakończono: {len(converted)} z {len(self.selected_files)} plików")

    def convert_with_ocr(self, pdf_path, output_path, output_ext):
        """Konwersja z użyciem OCR"""
        images = convert_from_path(pdf_path, dpi=500)
        self.add_log(f"Znaleziono {len(images)} stron")
        
        if output_ext == ".docx":
            self.add_log("OCR do DOCX nie jest wspierany. Zapisuję wynik OCR do pliku TXT.")
            output_path = output_path.replace(".docx", ".txt")
            messagebox.showinfo("OCR do DOCX", "Plik to skan. Wynik OCR zostanie zapisany jako TXT.")
        
        all_text = []
        for page_num, img in enumerate(images, 1):
            if not self.running:
                break
            
            self.add_log(f"OCR strony {page_num}/{len(images)}")
            img = img.convert('L')
            # Binaryzacja obrazu dla lepszego OCR
            import numpy as np
            img_array = np.array(img)
            threshold = 180
            img_array = np.where(img_array > threshold, 255, 0)
            img = Image.fromarray(img_array.astype('uint8'))
            
            custom_config = r'--psm 6'
            text = pytesseract.image_to_string(img, lang='pol+eng', config=custom_config)
            text = self.clean_ocr_text(text)
            all_text.append(text)
        
        if self.running and all_text:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("\n\n".join(all_text))

    def convert_to_docx(self, pdf_path, output_path):
        """Konwersja do DOCX"""
        if not self.running:
            return
        cv = Converter(pdf_path)
        cv.convert(output_path)
        cv.close()

    def convert_to_txt(self, pdf_path, output_path):
        """Konwersja do TXT"""
        if not self.running:
            return
        self.add_log("Konwertuję do TXT...")
        try:
            text = extract_text(pdf_path)
            cleaned_text = self.clean_pdfminer_text(text)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(cleaned_text)
        except Exception as e:
            raise Exception(f"Błąd podczas konwersji do TXT: {str(e)}")

    def update_status(self, message):
        """Aktualizuje status w interfejsie"""
        self.status_label.config(text=f"Status: {message}")
        self.add_log(message)

    def needs_ocr(self, pdf_path):
        """Analizuje plik PDF aby określić czy wymaga OCR"""
        try:
            text = extract_text(pdf_path)
            if len(text.strip()) < 100:
                self.add_log("Wykryto skan lub obraz - będzie użyte OCR")
                return True
                
            text_chars = sum(1 for c in text if c.strip())
            if text_chars / len(text) < 0.1:
                self.add_log("Wykryto niską jakość tekstu - będzie użyte OCR")
                return True
                
            self.add_log("Wykryto dobrej jakości tekst - OCR nie jest potrzebne")
            return False
        except Exception as e:
            self.add_log(f"Błąd podczas analizy pliku - na wszelki wypadek użyję OCR: {str(e)}")
            return True

    def open_output_dir(self):
        """Otwiera folder z przekonwertowanymi plikami - wieloplatformowo"""
        if os.path.exists(self.output_dir):
            system = platform.system()
            try:
                if system == "Windows":
                    subprocess.run(['explorer', self.output_dir], check=True)
                elif system == "Darwin":  # macOS
                    subprocess.run(['open', self.output_dir], check=True)
                else:  # Linux i inne systemy Unix
                    subprocess.run(['xdg-open', self.output_dir], check=True)
            except subprocess.CalledProcessError:
                messagebox.showinfo("Folder", f"Folder z plikami: {self.output_dir}")
            except FileNotFoundError:
                messagebox.showinfo("Folder", f"Folder z plikami: {self.output_dir}")
        else:
            messagebox.showwarning("Błąd", f"Folder {self.output_dir} nie istnieje!")

    def check_poppler(self):
        """Sprawdza dostępność Poppler wieloplatformowo"""
        system = platform.system()
        
        # Sprawdź czy Poppler jest w PATH
        if shutil.which('pdftocairo'):
            return True

        if system == "Windows":
            # Sprawdź Poppler w AppData
            poppler_base = os.path.expandvars(r'%USERPROFILE%\\AppData\\Local\\Programs\\poppler')
            if os.path.exists(poppler_base):
                poppler_dirs = glob.glob(os.path.join(poppler_base, 'poppler-*'))
                if poppler_dirs:
                    poppler_bin = os.path.join(max(poppler_dirs), 'Library', 'bin')
                    if os.path.exists(poppler_bin):
                        os.environ['PATH'] = f"{poppler_bin};{os.environ['PATH']}"
                        self.add_log(f"Dodano Poppler do PATH: {poppler_bin}")
                        return True

        # Jeśli nie znaleziono Poppler
        if system == "Windows":
            error_msg = ("Poppler nie został znaleziony!\n\n"
                        "Pobierz i zainstaluj Poppler dla Windows:\n"
                        "https://github.com/oschwartz10612/poppler-windows/releases\n\n"
                        "Więcej informacji w menu Pomoc > Instrukcja instalacji")
        elif system == "Darwin":  # macOS
            error_msg = ("Poppler nie został znaleziony!\n\n"
                        "Zainstaluj Poppler przez Homebrew:\n"
                        "brew install poppler\n\n"
                        "Więcej informacji w menu Pomoc > Instrukcja instalacji")
        else:  # Linux
            error_msg = ("Poppler nie został znaleziony!\n\n"
                        "Zainstaluj Poppler przez menedżer pakietów:\n"
                        "sudo apt-get install poppler-utils  # Ubuntu/Debian\n"
                        "sudo yum install poppler-utils      # CentOS/RHEL\n\n"
                        "Więcej informacji w menu Pomoc > Instrukcja instalacji")

        messagebox.showerror("Brak Poppler", error_msg)
        return False

    def clean_ocr_text(self, text):
        """Czyści tekst po OCR"""
        if not text.strip():
            return ""
        
        # Usuwamy znaki kontrolne i nadmierne białe znaki
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)  # Podwójne nowe linie
        text = re.sub(r'[ \t]+', ' ', text)  # Wielokrotne spacje/taby
        text = text.strip()
        
        return text

    def clean_pdfminer_text(self, text):
        """Czyści tekst z pdfminer"""
        if not text.strip():
            return ""
        
        # Usuwamy znaki kontrolne
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # Wielokrotne nowe linie
        text = re.sub(r'[ \t]+', ' ', text)  # Wielokrotne spacje
        text = text.strip()
        
        return text


# =============================================================================
# Log Handler for GUI
# =============================================================================
class GuiLogHandler(logging.Handler):
    """Handler do przekierowania logów do GUI"""
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
