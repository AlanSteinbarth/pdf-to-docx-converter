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

# Zmienne globalne dla modułów OCR
Converter = None
convert_from_path = None
pytesseract = None

# =============================================================================
# OCR Support Detection
# Sprawdzanie dostępności modułów OCR i konfiguracja fallback
# =============================================================================
OCR_AVAILABLE = False
try:
    # Sprawdź dostępność każdego modułu osobno
    pdf2docx_spec = importlib.util.find_spec("pdf2docx")
    pdf2image_spec = importlib.util.find_spec("pdf2image")
    pytesseract_spec = importlib.util.find_spec("pytesseract")

    if pdf2docx_spec and pdf2image_spec and pytesseract_spec:
        from pdf2docx import Converter
        from pdf2image import convert_from_path
        import pytesseract
        OCR_AVAILABLE = True
except Exception as e:
    print(f"OCR-related modules not fully available: {e}")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
