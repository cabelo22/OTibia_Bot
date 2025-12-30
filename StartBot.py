from PyQt5.QtWidgets import QApplication
import pytesseract
import Addresses
import os
import sys
import platform
import shutil

# Set Tesseract Path - Multi-platform support
if getattr(sys, 'frozen', False):
    # If running from EXE, Tesseract will be in the internal _MEIPASS folder
    if platform.system() == 'Windows':
        tesseract_path = os.path.join(sys._MEIPASS, 'Tesseract-OCR', 'tesseract.exe')
    else:
        tesseract_path = os.path.join(sys._MEIPASS, 'tesseract')
else:
    # If running from source, detect OS and find Tesseract
    if platform.system() == 'Windows':
        # Windows: Try common installation paths
        possible_paths = [
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
        ]
        tesseract_path = None
        for path in possible_paths:
            if os.path.exists(path):
                tesseract_path = path
                break
        if not tesseract_path:
            tesseract_path = 'tesseract'  # Try PATH
    else:
        # Linux/Unix: Use system tesseract
        tesseract_path = shutil.which('tesseract') or 'tesseract'

pytesseract.pytesseract.tesseract_cmd = tesseract_path

from General.SelectTibiaTab import SelectTibiaTab


def main():
    # Make directories
    os.makedirs("Images", exist_ok=True)
    os.makedirs("Save", exist_ok=True)
    os.makedirs("Save/Targeting", exist_ok=True)
    os.makedirs("Save/Settings", exist_ok=True)
    os.makedirs("Save/Waypoints", exist_ok=True)
    os.makedirs("Save/HealingAttack", exist_ok=True)
    os.makedirs("Save/SmartHotkeys", exist_ok=True)
    os.makedirs("Save/Hotkeys", exist_ok=True)
    app = QApplication([])
    app.setStyle('Fusion')
    app.setStyleSheet(Addresses.dark_theme)
    
    login_window = SelectTibiaTab()
    login_window.show()

    app.exec()


if __name__ == '__main__':
    main()