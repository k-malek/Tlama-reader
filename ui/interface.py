"""
Graphical User Interface for Tlama Caller.
Re-exports for backward compatibility.
"""

import customtkinter as ctk
from ui.game_details import GameDetailsWindow
from ui.main_window import TlamaCallerGUI, run_interface

# Set appearance mode and color theme (must run before creating windows)
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

__all__ = ["GameDetailsWindow", "TlamaCallerGUI", "run_interface"]


if __name__ == "__main__":
    run_interface()
