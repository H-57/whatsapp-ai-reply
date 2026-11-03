import sys
import os
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow

def main():
    # Ensure profile directory exists relative to app.py
    base_dir = os.path.dirname(os.path.abspath(__file__))
    profile_dir = os.path.join(base_dir, "whatsapp-profile")
    os.makedirs(profile_dir, exist_ok=True)

    app = QApplication(sys.argv)
    window = MainWindow(profile_dir)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
