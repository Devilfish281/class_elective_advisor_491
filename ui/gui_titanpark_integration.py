# ui/gui_titanpark_integration.py
import tkinter as tk
from tkinter import messagebox

from titanpark_integration.client import TitanParkError
from titanpark_integration.recommendation import recommend_parking_now


def _clear_frame(frame) -> None:
    """Destroy all child widgets in the given frame."""
    for widget in frame.winfo_children():
        widget.destroy()


def show_parking_helper(frame):
    """Display the TitanPark parking helper UI in the given frame."""
    _clear_frame(frame)
    header = tk.Label(frame, text="Find Parking Fast", font=("Helvetica", 16))
    header.pack(pady=10)

    result_label = tk.Label(frame, text="", wraplength=600, justify="left")
    result_label.pack(pady=10)

    def refresh():
        try:
            rec = recommend_parking_now(
                preferred_structures=["Nutwood Structure", "State College Structure"]
            )
        except TitanParkError as exc:
            messagebox.showerror("TitanPark Error", str(exc))
            return
        except Exception as exc:
            messagebox.showerror("Unexpected error", str(exc))
            return
        if rec is None:
            result_label.config(text="No good parking options are available right now.")
        else:
            result_label.config(text=rec.explanation)

    tk.Button(frame, text="Check Parking Now", command=refresh).pack(pady=5)
