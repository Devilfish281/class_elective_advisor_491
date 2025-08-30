import logging
import tkinter as tk
from typing import Optional

logger = logging.getLogger(__name__)  # Reuse the global logger


def main_int_ui() -> None:
    """Initializes and runs the main interface of the Smart Elective Advisor."""

    logger.info("Initializing the Smart Elective Advisor GUI.")

    # Minimal Tkinter window
    root = tk.Tk()
    root.title("Smart Elective Advisor")
    root.geometry("800x600")

    # Example label
    label = tk.Label(root, text="Welcome to Smart Elective Advisor")
    label.pack(padx=20, pady=20)

    # Start the Tk mainloop (this call blocks until the window closes)
    try:
        root.mainloop()
    except Exception as e:
        logger.exception("Error in GUI mainloop: %s", e)
        raise
