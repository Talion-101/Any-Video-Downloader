import customtkinter as ctk
from app.ui.main_window import MainWindow

if __name__ == "__main__":
    # Set the theme
    ctk.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"
    ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

    app = MainWindow()
    app.mainloop()
