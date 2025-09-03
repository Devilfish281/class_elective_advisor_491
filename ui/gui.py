import logging
import threading
import time
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

    def _on_close():
        logger.info("GUI received close request; shutting down.")
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", _on_close)

    # Start the Tk mainloop (this call blocks until the window closes)
    try:
        root.mainloop()
    except Exception:
        logger.exception("Error in GUI mainloop")
        raise


def main_test_ui(option: int) -> bool:
    """
    UI test dispatcher:
      option 1 -> launch the real GUI (blocking; user must close window)
      option 2 -> sanity create/destroy root without entering mainloop (fast)
      option 3 -> launch GUI and auto-close after 1 second (useful for CI)
    Returns True on success, False on failure.
    """
    logger.info("main_test_ui: selected option %s", option)

    if option == 1:
        try:
            main_int_ui()
            return True
        except Exception:
            logger.exception("main_test_ui option 1 failed")
            return False

    elif option == 2:
        try:
            root = tk.Tk()
            root.update_idletasks()
            root.destroy()
            logger.info("main_test_ui option 2: sanity create/destroy succeeded")
            return True
        except Exception:
            logger.exception("main_test_ui option 2 failed")
            return False

    elif option == 3:
        try:
            # Start the GUI in a separate thread and auto-close after 1 second.
            def _run_and_close():
                root = tk.Tk()
                root.title("Smart Elective Advisor (auto-close test)")
                label = tk.Label(root, text="Auto-close test (1s)")
                label.pack(padx=10, pady=10)
                # schedule close after 1000 ms
                root.after(1000, root.destroy)
                try:
                    root.mainloop()
                except Exception:
                    logger.exception("Exception in auto-close GUI thread")

            t = threading.Thread(target=_run_and_close, daemon=True)
            t.start()
            # wait a bit for thread to run and GUI to close
            time.sleep(1.5)
            logger.info("main_test_ui option 3: auto-close GUI test completed")
            return True
        except Exception:
            logger.exception("main_test_ui option 3 failed")
            return False

    else:
        logger.error("main_test_ui: unknown option %s", option)
        return False
