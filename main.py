import sys
import os

# Make sure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import customtkinter as ctk
from database.connection import initialize_db
from ui.app import App

if __name__ == "__main__":
    initialize_db()
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")
    app = App()
    app.mainloop()
