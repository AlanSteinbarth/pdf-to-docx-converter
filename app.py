# =============================================================================
# PDF to DOCX/TXT Converter with OCR
# Author: Alan Steinbarth
# Version: 4.0 - Advanced PDF Converter with Preview and OCR
# =============================================================================

# =============================================================================
# Imports and Configuration
# =============================================================================
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, Toplevel, messagebox
import os
import platform
import threading
import logging
from pdfminer.high_level import extract_text, extract_pages
from PIL import Image, ImageTk
import fitz
import logging.handlers
import yaml

try:
    import pytesseract as pt_module
    if platform.system() == "Darwin":  # macOS
        tesseract_paths = [
            "/opt/homebrew/bin/tesseract",
            "/usr/local/bin/tesseract"
        ]
        for path in tesseract_paths:
            if os.path.exists(path):
                pt_module.pytesseract.tesseract_cmd = path
                break
    pytesseract = pt_module
    TESSERACT_AVAILABLE = True
    logging.info("Tesseract OCR został pomyślnie zainicjowany.")
except ImportError:
    TESSERACT_AVAILABLE = False
    logging.warning("Pytesseract nie jest zainstalowany. Funkcje OCR będą niedostępne.")
except Exception as e:
    TESSERACT_AVAILABLE = False
    logging.error(f"Błąd podczas inicjalizacji Tesseract: {e}")

# Ustawienie zmiennej środowiskowej dla macOS - ZAWSZE na początku
if platform.system() == "Darwin":
    os.environ['TK_SILENCE_DEPRECATION'] = '1'

class GuiLogHandler(logging.Handler):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget
        self.formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')
        self.setFormatter(self.formatter)

    def emit(self, record):
        msg = self.format(record)
        def append():
            self.text_widget.config(state=tk.NORMAL)
            self.text_widget.insert(tk.END, msg + "\n")  # Każdy log w osobnej linii
            self.text_widget.config(state=tk.DISABLED)
            self.text_widget.see(tk.END)
        if hasattr(self.text_widget, 'after'):
            self.text_widget.after(0, append)

# Inicjalizacja głównego loggera
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

# --- Enterprise: logowanie do pliku z rotacją ---
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)
LOG_FILE = os.path.join(LOG_DIR, 'app.log')
file_handler = logging.handlers.RotatingFileHandler(
    LOG_FILE, maxBytes=2*1024*1024, backupCount=5, encoding='utf-8'
)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
logging.getLogger().addHandler(file_handler)

# --- Enterprise: ładowanie konfiguracji z config.yaml ---
def load_config():
    # Szukaj config.yaml w bieżącym katalogu roboczym (dla testów i uruchomień enterprise)
    config_path = os.path.join(os.getcwd(), 'config.yaml')
    default = {
        'output_dir': os.path.expanduser('~/Desktop'),
        'log_level': 'INFO',
        'ocr_lang': 'pol',
    }
    if not os.path.exists(config_path):
        return default
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            cfg = yaml.safe_load(f)
        if not isinstance(cfg, dict):
            return default
        # Rozszerz domyślne o wartości z pliku
        merged = default.copy()
        merged.update({k: v for k, v in cfg.items() if v is not None})
        merged['output_dir'] = os.path.expanduser(merged['output_dir'])
        return merged
    except Exception as e:
        logging.warning(f"Nie udało się wczytać config.yaml: {e}")
        return default

class PDFtoDocxConverterApp(tk.Tk):
    def get_default_output_dir(self):
        """Określa domyślny folder wyjściowy w zależności od systemu operacyjnego"""
        system = platform.system()
        try:
            if system == "Windows":
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
            return os.path.expanduser("~")

    def _bring_to_front_macos(self):
        """Wymusza pokazanie okna na wierzchu na macOS po pełnej inicjalizacji."""
        self.deiconify()
        self.lift()
        self.focus_force()
        self.attributes('-topmost', True)
        self.after(300, lambda: self.attributes('-topmost', False))

    def __init__(self):
        self.app_config = load_config()
        # Ustaw poziom logowania z config.yaml
        logging.getLogger().setLevel(self.app_config.get('log_level', 'INFO'))
        super().__init__()
        self.title("Zaawansowany Konwerter PDF v4.1.0 Enterprise Edition")
        self.geometry("1024x768")
        self.minsize(900, 600)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.selected_files = []
        self.output_dir = self.app_config.get('output_dir', self.get_default_output_dir())
        self.output_format = tk.StringVar(value="docx")
        self.conversion_thread = None
        self.cancel_event = threading.Event()
        self.current_preview_image = None
        self.ocr_lang = self.app_config.get('ocr_lang', 'pol')

        self.create_widgets()
        self._setup_logging()
        self.create_menu()

        self.center_window()
        self.update_idletasks()
        self.update()

        logging.info("Aplikacja uruchomiona.")
        self.on_file_select()

        # Tekst pomocy do okna 'O programie'
        self.help_text = (
            "Instrukcja obsługi:\n"
            "1. Dodaj pliki PDF do listy przyciskiem 'Wybierz pliki' lub 'Dodaj folder'.\n"
            "2. (Opcjonalnie) Zmień folder docelowy.\n"
            "3. Wybierz format wyjściowy (DOCX lub TXT).\n"
            "4. Kliknij 'Konwertuj', aby rozpocząć.\n"
            "5. Postęp i logi pojawią się na dole okna.\n"
            "\n"
            "Wymagane narzędzia zewnętrzne:\n"
            "- Poppler (do konwersji PDF na obrazy)\n"
            "- Tesseract OCR (do rozpoznawania tekstu ze skanów)\n"
            "\n"
            "Pobierz Poppler:\n"
            "  Windows: https://github.com/oschwartz10612/poppler-windows/releases\n"
            "  macOS: brew install poppler\n"
            "  Linux: sudo apt install poppler-utils\n"
            "\n"
            "Pobierz Tesseract OCR:\n"
            "  Windows: https://github.com/tesseract-ocr/tesseract\n"
            "  macOS: brew install tesseract tesseract-lang\n"
            "  Linux: sudo apt install tesseract-ocr tesseract-ocr-pol\n"
            "\n"
            "Więcej informacji i FAQ znajdziesz w pliku README.md."
        )

        # Wymuś pokazanie okna na wierzchu na macOS po pełnej inicjalizacji
        if platform.system() == "Darwin":
            self.after(200, self._bring_to_front_macos)

    def _setup_logging(self):
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        logging.getLogger('pdfminer').setLevel(logging.ERROR)
        logging.getLogger('PIL').setLevel(logging.WARNING)
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        # Tworzenie widgetu logów jeśli nie istnieje
        if not hasattr(self, 'log_text_widget'):
            self.log_text_widget = scrolledtext.ScrolledText(self, height=8, state=tk.DISABLED)
            self.log_text_widget.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(0, 5))
        gui_handler = GuiLogHandler(self.log_text_widget)
        logger.addHandler(gui_handler)

    def create_menu(self):
        """Tworzy pasek menu aplikacji."""
        self.menubar = tk.Menu(self)
        filemenu = tk.Menu(self.menubar, tearoff=0)
        filemenu.add_command(label="Wybierz pliki...", command=self.select_files, accelerator="Cmd+O" if platform.system() == "Darwin" else "Ctrl+O")
        filemenu.add_command(label="Dodaj folder...", command=self.add_folder, accelerator="Cmd+Shift+O" if platform.system() == "Darwin" else "Ctrl+Shift+O")
        filemenu.add_separator()
        filemenu.add_command(label="Wyczyść listę plików", command=self.clear_file_list)
        filemenu.add_separator()
        filemenu.add_command(label="Wyjdź", command=self.on_closing, accelerator="Cmd+Q" if platform.system() == "Darwin" else "Alt+F4")
        self.menubar.add_cascade(label="Plik", menu=filemenu)
        # Usunięto menu Opcje (OCR)
        helpmenu = tk.Menu(self.menubar, tearoff=0)
        helpmenu.add_command(label="O programie...", command=self.show_about_dialog)
        self.menubar.add_cascade(label="Pomoc", menu=helpmenu)
        self.config(menu=self.menubar)

    def show_about_dialog(self):
        """Wyświetla okno dialogowe 'O programie' oraz instrukcję i linki do Poppler/Tesseract."""
        about_win = Toplevel(self)
        about_win.title("O programie - PDF Converter v4.1.0 Enterprise Edition")
        dialog_width = 500
        dialog_height = 420  # zwiększona wysokość
        about_win.resizable(False, False)
        about_win.transient(self)
        about_win.grab_set()
        parent_x = self.winfo_x()
        parent_y = self.winfo_y()
        parent_width = self.winfo_width()
        parent_height = self.winfo_height()
        pos_x = parent_x + (parent_width // 2) - (dialog_width // 2)
        pos_y = parent_y + (parent_height // 2) - (dialog_height // 2)
        about_win.geometry(f"{dialog_width}x{dialog_height}+{pos_x}+{pos_y}")
        main_frame = ttk.Frame(about_win, padding=15)
        main_frame.pack(expand=True, fill=tk.BOTH)
        ttk.Label(main_frame, text="Zaawansowany Konwerter PDF", font=("Helvetica", 14, "bold")).pack(pady=(0,10))
        ttk.Label(main_frame, text="Wersja: 4.1.0 Enterprise Edition").pack(pady=3)
        ttk.Label(main_frame, text="Autor: Alan Steinbarth").pack(pady=3)
        ttk.Label(main_frame, text="Wykorzystuje biblioteki: pdf2docx, pdfminer.six, PyMuPDF, Pillow, (opcjonalnie) Pytesseract.").pack(pady=3)
        ttk.Label(main_frame, text="© 2025").pack(pady=3)
        # Instrukcja i linki
        help_textbox = scrolledtext.ScrolledText(main_frame, height=12, wrap=tk.WORD, state=tk.NORMAL)
        help_textbox.insert(tk.END, self.help_text)
        help_textbox.config(state=tk.DISABLED)
        help_textbox.pack(fill=tk.BOTH, expand=True, pady=(10,0))
        close_button = ttk.Button(main_frame, text="Zamknij", command=about_win.destroy)
        close_button.pack(pady=(20,0))
        about_win.protocol("WM_DELETE_WINDOW", about_win.destroy)

    def center_window(self):
        """Centruje okno na ekranie"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        # Upewnijmy się, że width i height nie są zerowe (co może się zdarzyć na początku)
        if width <= 1: # Czasami winfo_width() może zwrócić 1 na starcie
            width = int(self.geometry().split('x')[0].split('+')[0]) # Próba odczydu z geometrii
        if height <= 1:
            height = int(self.geometry().split('x')[1].split('+')[0]) # Próba odczydu z geometrii
        
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        pos_x = (screen_width // 2) - (width // 2)
        pos_y = (screen_height // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{pos_x}+{pos_y}")

    def on_closing(self):
        """Obsługuje zamykanie aplikacji."""
        if self.conversion_thread and self.conversion_thread.is_alive():
            if messagebox.askyesno("Potwierdzenie", "Trwa konwersja. Czy na pewno chcesz przerwać i zamknąć aplikację?"):
                logging.warning("Przerwanie konwersji i zamknięcie aplikacji przez użytkownika.")
                self.cancel_conversion(wait_for_thread=False) # Anuluj bez czekania, jeśli użytkownik chce szybko zamknąć
                self.destroy()
            else:
                return # Nie zamykaj
        else:
            self.destroy()

    def select_files(self):
        """Otwiera okno dialogowe do wyboru plików PDF i aktualizuje listę."""
        initial_dir = self.output_dir if os.path.isdir(self.output_dir) else os.path.expanduser("~")
        
        new_files = filedialog.askopenfilenames(
            title="Wybierz pliki PDF",
            initialdir=initial_dir,
            filetypes=(("Pliki PDF", "*.pdf"), ("Wszystkie pliki", "*.*"))
        )
        if new_files:
            for f in new_files:
                if f not in self.selected_files:
                    self.selected_files.append(f)
            self.update_files_listbox()
            if not self.files_listbox.curselection() and self.selected_files:
                self.files_listbox.selection_set(0) # Zaznacz pierwszy, jeśli lista niepusta
            self.on_file_select() # Zaktualizuj informacje o pliku

    def update_files_listbox(self):
        """Aktualizuje listę plików w Listbox."""
        self.files_listbox.delete(0, tk.END)
        for f_path in self.selected_files:
            self.files_listbox.insert(tk.END, os.path.basename(f_path))
        # Można dodać logikę aktualizacji statusu, np. liczby plików

    def add_folder(self):
        """Otwiera okno dialogowe do wyboru folderu i dodaje pliki PDF."""
        initial_dir = self.output_dir if os.path.isdir(self.output_dir) else os.path.expanduser("~")
        folder_path = filedialog.askdirectory(title="Wybierz folder z plikami PDF", initialdir=initial_dir)
        
        if folder_path:
            found_files = []
            for root, _, files in os.walk(folder_path):
                for file in files:
                    if file.lower().endswith(".pdf"):
                        full_path = os.path.join(root, file)
                        if full_path not in self.selected_files and full_path not in found_files:
                            found_files.append(full_path)
            
            if found_files:
                self.selected_files.extend(found_files)
                self.update_files_listbox()
                logging.info(f"Dodano {len(found_files)} plików PDF z folderu: {folder_path}")
                if not self.files_listbox.curselection() and self.selected_files:
                    self.files_listbox.selection_set(0)
                self.on_file_select()
            else:
                logging.warning(f"Nie znaleziono plików PDF w folderze: {folder_path}")

    def remove_selected_files(self):
        """Usuwa zaznaczone pliki z listy."""
        selected_indices = self.files_listbox.curselection()
        if not selected_indices:
            logging.warning("Nie wybrano plików do usunięcia.")
            return

        # Usuwamy od końca, aby uniknąć problemów z indeksami
        for index in reversed(selected_indices):
            del self.selected_files[index]
        
        self.update_files_listbox()
        logging.info(f"Usunięto {len(selected_indices)} plików z listy.")
        if self.selected_files and not self.files_listbox.curselection():
            self.files_listbox.selection_set(0) # Zaznacz pierwszy, jeśli coś zostało
        self.on_file_select() # Zaktualizuj info (wyczyści, jeśli lista pusta)

    def clear_file_list(self):
        """Czyści listę wybranych plików."""
        if not self.selected_files:
            logging.info("Lista plików jest już pusta.")
            return
        
        self.selected_files.clear()
        self.update_files_listbox()
        logging.info("Wyczyszczono listę plików.")
        self.on_file_select() # Wywoła _clear_file_info_display

    def select_output_dir(self):
        """Otwiera okno dialogowe do wyboru folderu docelowego."""
        initial_dir = self.output_dir if os.path.isdir(self.output_dir) else os.path.expanduser("~")
        new_dir = filedialog.askdirectory(title="Wybierz folder docelowy", initialdir=initial_dir)
        if new_dir:
            self.output_dir = new_dir
            self.output_dir_entry.config(state=tk.NORMAL)
            self.output_dir_entry.delete(0, tk.END)
            self.output_dir_entry.insert(0, self.output_dir)
            self.output_dir_entry.config(state="readonly")
            logging.info(f"Zmieniono folder docelowy na: {self.output_dir}")

    def _toggle_controls_state(self, state):
        """Włącza lub wyłącza główne kontrolki."""
        widgets_to_toggle = [
            self.select_files_button, self.add_folder_button,
            self.remove_button, self.clear_list_button,
            self.select_output_dir_button, self.docx_radio, self.txt_radio
        ]
        for widget in widgets_to_toggle:
            if widget:
                widget.config(state=state)

    def start_conversion(self):
        """Rozpoczyna proces konwersji plików w osobnym wątku."""
        # print("DEBUG: start_conversion called") # DEBUG
        if not self.selected_files:
            logging.warning("Nie wybrano plików do konwersji.")
            messagebox.showwarning("Brak plików", "Proszę wybrać pliki do konwersji.")
            return

        if self.conversion_thread and self.conversion_thread.is_alive():
            logging.warning("Konwersja jest już w toku.")
            messagebox.showwarning("Konwersja w toku", "Poczekaj na zakończenie bieżącej konwersji.")
            return

        # print(f"DEBUG: Starting conversion for {len(self.selected_files)} files. Output format: {self.output_format.get()}") # DEBUG
        logging.info(f"Rozpoczynanie konwersji {len(self.selected_files)} plików do formatu {self.output_format.get().upper()}...")
        self._toggle_controls_state(tk.DISABLED)
        self.convert_button.config(state=tk.DISABLED)
        self.cancel_button.config(state=tk.NORMAL)
        
        self.cancel_event.clear()
        self.progress_bar["value"] = 0
        self.progress_bar["maximum"] = len(self.selected_files)
        # print(f"DEBUG: Progress bar max set to {self.progress_bar['maximum']}") # DEBUG

        self.conversion_thread = threading.Thread(target=self._perform_conversion_threaded, daemon=True)
        self.conversion_thread.start()
        # print("DEBUG: Conversion thread started") # DEBUG

    def _convert_single_file(self, file_path):
        base_name = os.path.basename(file_path)
        name_without_ext = os.path.splitext(base_name)[0]
        output_format_val = self.output_format.get()
        output_file_name = f"{name_without_ext}.{output_format_val}"
        output_file_path = os.path.join(self.output_dir, output_file_name)
        try:
            text_content = extract_text(file_path)
            # Jeśli tekst jest pusty lub bardzo krótki, automatycznie uruchom OCR
            if not text_content or len(text_content.strip()) < 20:
                logging.info(f"Automatyczne uruchamianie OCR dla '{base_name}' (brak tekstu w PDF)...")
                ocr_texts = []
                ocr_pages_with_text = 0
                if TESSERACT_AVAILABLE and pytesseract:
                    try:
                        from PIL import ImageOps, ImageFilter
                        doc = fitz.open(file_path)
                        for page_num in range(len(doc)):
                            page = doc[page_num]
                            try:
                                pix = self._get_pixmap_compat(page, fitz.Matrix(3, 3))  # DPI x3 dla lepszej jakości
                            except Exception as e:
                                logging.error(f"Błąd generowania obrazu do OCR: {e}")
                                continue
                            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
                            img = img.convert("L")
                            img = ImageOps.autocontrast(img)
                            img = img.filter(ImageFilter.SHARPEN)
                            threshold = 150  # mocniejsza binarizacja
                            table = [0 if i < threshold else 255 for i in range(256)]
                            img = img.point(table, 'L')
                            ocr_text = pytesseract.image_to_string(img, lang=self.ocr_lang, config='--psm 6')
                            ocr_text = ocr_text.strip()
                            if ocr_text:
                                ocr_pages_with_text += 1
                            ocr_texts.append(ocr_text)
                            pix = None
                        doc.close()
                        text_content = "\n\n--- Koniec strony ---\n\n".join(ocr_texts)
                        logging.info(f"OCR zakończony: {ocr_pages_with_text}/{len(ocr_texts)} stron zawierało tekst.")
                    except Exception as ocr_err:
                        logging.error(f"Błąd OCR: {ocr_err}. Nie udało się wyciągnąć tekstu z obrazu.")
                        text_content = ""
                else:
                    logging.warning("OCR niedostępny – nie można przetworzyć pliku graficznego.")
                    text_content = ""
            if output_format_val == "docx":
                from docx import Document
                docx_doc = Document()
                # Dodajemy tekst z OCR jako osobne paragrafy dla każdej strony
                if text_content.strip():
                    for page_text in text_content.split("\n\n--- Koniec strony ---\n\n"):
                        lines = [line for line in page_text.splitlines() if line.strip()]
                        if lines:
                            for line in lines:
                                docx_doc.add_paragraph(line)
                            docx_doc.add_paragraph("")  # pusta linia między stronami
                    # Usuń ostatni pusty akapit jeśli jest
                    if docx_doc.paragraphs and not docx_doc.paragraphs[-1].text.strip():
                        p = docx_doc.paragraphs[-1]._element
                        p.getparent().remove(p)
                    docx_doc.save(output_file_path)
                    logging.info(f"Pomyślnie zapisano '{base_name}' jako '{output_file_name}'.")
                    return True
                else:
                    logging.warning(f"Nie udało się wyodrębnić tekstu z pliku '{base_name}'. Plik DOCX nie został utworzony.")
                    return False
            elif output_format_val == "txt":
                if text_content.strip():
                    with open(output_file_path, "w", encoding="utf-8") as f:
                        f.write(text_content)
                    logging.info(f"Pomyślnie zapisano '{base_name}' jako '{output_file_name}'.")
                    return True
                else:
                    logging.warning(f"Nie udało się wyodrębnić tekstu z pliku '{base_name}'. Plik TXT nie został utworzony.")
                    return False
        except Exception as e:
            logging.error(f"Błąd podczas konwersji pliku '{base_name}': {e}")
            return False

    def _perform_conversion_threaded(self):
        """Główna logika konwersji wykonywana w wątku."""
        # print("DEBUG: _perform_conversion_threaded started") # DEBUG
        files_converted_count = 0
        try:
            for i, file_path in enumerate(self.selected_files):
                if self.cancel_event.is_set():
                    logging.warning("Konwersja przerwana przez użytkownika.")
                    break
                logging.info(f"Przetwarzanie pliku ({i+1}/{len(self.selected_files)}): {os.path.basename(file_path)}")
                try:
                    success = self._convert_single_file(file_path)
                except Exception as file_exc:
                    logging.error(f"Błąd krytyczny podczas konwersji pliku {file_path}: {file_exc}")
                    success = False
                if success:
                    files_converted_count += 1
                else:
                    logging.warning(f"Pominięto plik {os.path.basename(file_path)} z powodu błędu.")
                current_progress = i + 1
                self.after(0, lambda val=current_progress: self.progress_bar.config(value=val))
        except Exception as e:
            logging.error(f"Wystąpił krytyczny błąd w głównym wątku konwersji: {e}")
        finally:
            self.after(0, self._finalize_conversion)

    def cancel_conversion(self, wait_for_thread=True):
        """Anuluje trwającą konwersję."""
        if self.conversion_thread and self.conversion_thread.is_alive():
            if not self.cancel_event.is_set():
                self.cancel_event.set()
                logging.info("Anulowanie konwersji...")
                if wait_for_thread:
                    self.conversion_thread.join(timeout=2)
                self._toggle_controls_state(tk.NORMAL)
                self.convert_button.config(state=tk.NORMAL)
                self.cancel_button.config(state=tk.DISABLED)
            else:
                logging.info("Anulowanie jest już w toku.")
        else:
            logging.info("Brak aktywnej konwersji do anulowania.")
            self.cancel_button.config(state=tk.DISABLED)

    def _finalize_conversion(self):
        self._toggle_controls_state(tk.NORMAL)
        self.convert_button.config(state=tk.NORMAL)
        self.cancel_button.config(state=tk.DISABLED)
        logging.info("Konwersja zakończona.")

    def _get_pdf_page_count(self, pdf_path):
        """Pobiera liczbę stron z pliku PDF."""
        try:
            count = 0
            for _ in extract_pages(pdf_path): # extract_pages jest generatorem
                count += 1
            return count
        except Exception as e:
            logging.warning(f"Nie udało się pobrać liczby stron dla '{os.path.basename(pdf_path)}': {type(e).__name__}. Szczegóły w logach konsoli, jeśli dostępne.")
            # print(f"DEBUG: Pełny błąd przy get_pdf_page_count dla {pdf_path}: {e}") # Do debugowania
            return None

    def on_file_select(self, event=None):
        """Obsługuje zdarzenie wyboru pliku na liście i aktualizuje informacje oraz podgląd."""
        if not hasattr(self, 'files_listbox') or not hasattr(self, 'selected_files'):
            return

        selected_indices = self.files_listbox.curselection()
        if not selected_indices:
            self._clear_file_info_display()
            return
        selected_index = selected_indices[0]
        if 0 <= selected_index < len(self.selected_files):
            file_path = self.selected_files[selected_index]
            self._display_file_info(file_path)
            self._preview_pdf_page(file_path)  # natychmiastowe odświeżenie podglądu
            self.preview_canvas.update_idletasks()  # wymuszenie aktualizacji
        else:
            self._clear_file_info_display()
            self._clear_pdf_preview()
            logging.debug(f"Niespójność indeksu w on_file_select: {selected_index} vs len {len(self.selected_files)}")

    def _display_file_info(self, file_path):
        """Wyświetla informacje o podanym pliku PDF."""
        if not hasattr(self, 'info_file_name_var'): 
            return 
        
        if not os.path.exists(file_path):
            self._clear_file_info_display()
            logging.warning(f"Plik nie istnieje w _display_file_info: {file_path}")
            return

        file_name = os.path.basename(file_path)
        size_str = "N/A" # Inicjalizacja
        
        try:
            file_size_bytes = os.path.getsize(file_path)
            if file_size_bytes < 1024:
                size_str = f"{file_size_bytes} B"
            elif file_size_bytes < 1024 * 1024:
                size_str = f"{file_size_bytes / 1024:.2f} KB"
            else:
                size_str = f"{file_size_bytes / (1024 * 1024):.2f} MB"
        except OSError as e:
            logging.warning(f"Nie udało się pobrać rozmiaru pliku '{file_name}': {e}")
            size_str = "N/A" # Upewnij się, że size_str jest ustawione w przypadku błędu

        page_count = self._get_pdf_page_count(file_path)
        page_count_str = str(page_count) if page_count is not None else "N/A"

        self.info_file_name_var.set(f"{file_name}")
        self.info_file_size_var.set(f"{size_str}")
        self.info_file_pages_var.set(f"{page_count_str}")

    def _clear_file_info_display(self):
        """Czyści wyświetlane informacje o pliku."""
        if hasattr(self, 'info_file_name_var'):
            self.info_file_name_var.set("-")
            self.info_file_size_var.set("-")
            self.info_file_pages_var.set("-")
            self._clear_pdf_preview() # Wyczyść również podgląd

    def _clear_pdf_preview(self):
        """Czyści canvas podglądu PDF."""
        if hasattr(self, 'preview_canvas'):
            self.preview_canvas.delete("all")
            self.current_preview_image = None

    def _get_pixmap_compat(self, page, matrix):
        """Zwraca pixmapę strony PDF, obsługując różne wersje PyMuPDF."""
        if hasattr(page, 'get_pixmap'):
            return page.get_pixmap(matrix=matrix)
        elif hasattr(page, 'getPixmap'):
            return page.getPixmap(matrix=matrix)
        else:
            raise RuntimeError("Brak kompatybilnej metody get_pixmap/getPixmap w obiekcie Page.")

    def _preview_pdf_page(self, pdf_path, page_num=0):
        if not hasattr(self, 'preview_canvas'):
            return
        self._clear_pdf_preview()
        try:
            doc = fitz.open(pdf_path)
            if not doc:
                logging.error(f"Nie można otworzyć pliku PDF: {pdf_path}")
                return
            if page_num >= len(doc):
                logging.error(f"Nieprawidłowy numer strony: {page_num}")
                doc.close()
                return
            page = doc[page_num]
            preview_width = self.preview_canvas.winfo_width()
            preview_height = self.preview_canvas.winfo_height()
            if preview_width <= 1 or preview_height <= 1:
                # macOS-safe: ponów próbę po 200 ms
                self.after(200, lambda: self._preview_pdf_page(pdf_path, page_num))
                doc.close()
                return
            scale = min(preview_width / page.rect.width, preview_height / page.rect.height)
            mat = fitz.Matrix(scale, scale)
            try:
                pix = self._get_pixmap_compat(page, mat)
            except Exception as e:
                logging.error(f"Błąd generowania podglądu PDF: {e}")
                doc.close()
                return
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            self.current_preview_image = ImageTk.PhotoImage(img)
            self.preview_canvas.delete("all")
            self.preview_canvas.create_image(preview_width/2, preview_height/2, image=self.current_preview_image, anchor=tk.CENTER)
            pix = None
            doc.close()
        except Exception as e:
            logging.error(f"Błąd podczas generowania podglądu PDF: {e}")
            self._clear_pdf_preview()

    def create_widgets(self):
        # Główny kontener (wszystko poza stopką)
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(0, weight=1)

        # PanedWindow: lewy panel (kontrolki) i prawy panel (podgląd)
        self.main_pane = ttk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL)
        self.main_pane.grid(row=0, column=0, sticky="nsew")

        # --- Lewy panel (Kontrolki i Lista plików) ---
        self.left_panel_frame = ttk.Frame(self.main_pane, padding=5, width=400)
        self.left_panel_frame.pack_propagate(False)
        self.left_panel_frame.rowconfigure(0, weight=1)
        self.main_pane.add(self.left_panel_frame, weight=0)

        # Przycisk Pomoc/FAQ NA GÓRZE
        self.help_button = ttk.Button(self.left_panel_frame, text="Pomoc / O programie", command=self.show_about_dialog)
        self.help_button.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        # Lista wybranych plików
        self.files_listbox_frame = ttk.Frame(self.left_panel_frame)
        self.files_listbox_frame.grid(row=1, column=0, sticky="nsew")
        self.left_panel_frame.rowconfigure(1, weight=2)
        self.left_panel_frame.columnconfigure(0, weight=1)
        self.files_listbox = tk.Listbox(self.files_listbox_frame, selectmode=tk.EXTENDED, exportselection=False)
        self.files_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.files_listbox.bind('<<ListboxSelect>>', self.on_file_select)
        self.files_scrollbar = ttk.Scrollbar(self.files_listbox_frame, orient=tk.VERTICAL, command=self.files_listbox.yview)
        self.files_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.files_listbox.config(yscrollcommand=self.files_scrollbar.set)

        # Przyciski zarządzania plikami pod listą
        self.file_buttons_frame = ttk.Frame(self.left_panel_frame)
        self.file_buttons_frame.grid(row=2, column=0, sticky="ew", pady=(2, 0))
        # Pierwszy rząd: Wybierz pliki, Dodaj folder
        self.file_select_row = ttk.Frame(self.file_buttons_frame)
        self.file_select_row.pack(fill=tk.X, pady=1)
        self.select_files_button = ttk.Button(self.file_select_row, text="Wybierz pliki", command=self.select_files, width=12)
        self.select_files_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0,2))
        self.add_folder_button = ttk.Button(self.file_select_row, text="Dodaj folder", command=self.add_folder, width=12)
        self.add_folder_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(2,0))
        # Drugi rząd: Usuń wybrane, Wyczyść listę
        self.file_remove_row = ttk.Frame(self.file_buttons_frame)
        self.file_remove_row.pack(fill=tk.X, pady=1)
        self.remove_button = ttk.Button(self.file_remove_row, text="Usuń wybrane", command=self.remove_selected_files, width=12)
        self.remove_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0,2))
        self.clear_list_button = ttk.Button(self.file_remove_row, text="Wyczyść listę", command=self.clear_file_list, width=12)
        self.clear_list_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(2,0))

        # --- Sekcja informacji o pliku ---
        self.file_info_frame = ttk.LabelFrame(self.left_panel_frame, text="Informacje o pliku", padding="10 5 10 5")
        self.file_info_frame.grid(row=3, column=0, sticky="ew", pady=(10, 5))
        ttk.Label(self.file_info_frame, text="Nazwa:").grid(row=0, column=0, sticky=tk.W, padx=(0,5), pady=1)
        self.info_file_name_var = tk.StringVar(value="-")
        self.info_file_name_label = ttk.Label(self.file_info_frame, textvariable=self.info_file_name_var, anchor=tk.W, wraplength=200)
        self.info_file_name_label.grid(row=0, column=1, sticky=tk.EW, pady=1)
        ttk.Label(self.file_info_frame, text="Rozmiar:").grid(row=1, column=0, sticky=tk.W, padx=(0,5), pady=1)
        self.info_file_size_var = tk.StringVar(value="-")
        self.info_file_size_label = ttk.Label(self.file_info_frame, textvariable=self.info_file_size_var, anchor=tk.W)
        self.info_file_size_label.grid(row=1, column=1, sticky=tk.EW, pady=1)
        ttk.Label(self.file_info_frame, text="Liczba stron:").grid(row=2, column=0, sticky=tk.W, padx=(0,5), pady=1)
        self.info_file_pages_var = tk.StringVar(value="-")
        self.info_file_pages_label = ttk.Label(self.file_info_frame, textvariable=self.info_file_pages_var, anchor=tk.W)
        self.info_file_pages_label.grid(row=2, column=1, sticky=tk.EW, pady=1)
        self.file_info_frame.columnconfigure(1, weight=1)

        # --- Sekcja folderu docelowego i formatu ---
        self.output_settings_frame = ttk.Frame(self.left_panel_frame)
        self.output_settings_frame.grid(row=4, column=0, sticky="ew", pady=(10,5))
        self.output_dir_label = ttk.Label(self.output_settings_frame, text="Folder docelowy:")
        self.output_dir_label.pack(side=tk.TOP, anchor=tk.W)
        self.output_dir_entry_frame = ttk.Frame(self.output_settings_frame)
        self.output_dir_entry_frame.pack(fill=tk.X)
        self.output_dir_entry = ttk.Entry(self.output_dir_entry_frame, state="readonly")
        self.output_dir_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        self.output_dir_entry.config(state=tk.NORMAL)
        self.output_dir_entry.insert(0, self.output_dir)
        self.output_dir_entry.config(state="readonly")
        self.select_output_dir_button = ttk.Button(self.output_dir_entry_frame, text="Zmień", command=self.select_output_dir, width=8)
        self.select_output_dir_button.pack(side=tk.LEFT)
        self.format_frame = ttk.LabelFrame(self.output_settings_frame, text="Format wyjściowy", padding="5")
        self.format_frame.pack(fill=tk.X, pady=(10,5), anchor=tk.W)
        self.docx_radio = ttk.Radiobutton(self.format_frame, text="DOCX", variable=self.output_format, value="docx")
        self.docx_radio.pack(side=tk.LEFT, padx=(0,10), expand=True)
        self.txt_radio = ttk.Radiobutton(self.format_frame, text="TXT", variable=self.output_format, value="txt")
        self.txt_radio.pack(side=tk.LEFT, padx=(0,10), expand=True)

        # Pasek postępu
        self.progress_bar = ttk.Progressbar(self.left_panel_frame, orient=tk.HORIZONTAL, mode='determinate')
        self.progress_bar.grid(row=5, column=0, sticky="ew", pady=(10, 5))

        # Przyciski akcji na dole lewego panelu
        self.action_buttons_frame = ttk.Frame(self.left_panel_frame)
        self.action_buttons_frame.grid(row=6, column=0, sticky="ew", pady=(5,0))
        self.convert_button = ttk.Button(self.action_buttons_frame, text="Konwertuj", command=self.start_conversion, width=12)
        self.convert_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0,2))
        self.cancel_button = ttk.Button(self.action_buttons_frame, text="Anuluj", command=self.cancel_conversion, state=tk.DISABLED, width=12)
        self.cancel_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(2,0))

        # --- Prawy panel (podgląd PDF) ---
        self.right_panel_frame = ttk.Frame(self.main_pane, padding=5)
        self.main_pane.add(self.right_panel_frame, weight=3)
        self.right_panel_frame.rowconfigure(0, weight=1)
        self.right_panel_frame.columnconfigure(0, weight=1)
        self.preview_canvas = tk.Canvas(self.right_panel_frame, bg="#f0f0f0", height=320)
        self.preview_canvas.grid(row=0, column=0, sticky="nsew", padx=10, pady=(0, 5))

        # --- Stopka z informacją o autorze ---
        self.footer_label = ttk.Label(self, text="Autor: Alan Steinbarth | © 2025", anchor=tk.CENTER, font=("Arial", 10, "italic"))
        self.footer_label.pack(side=tk.BOTTOM, fill=tk.X, pady=(2, 2))

    # Usunięto metodę _on_drop_files oraz wszelkie odniesienia do DnD

if __name__ == "__main__":
    app = PDFtoDocxConverterApp()
    app.update_idletasks()
    app.deiconify()
    app.lift()
    app.focus_force()
    app.geometry("1024x768+100+100")
    app.mainloop()
