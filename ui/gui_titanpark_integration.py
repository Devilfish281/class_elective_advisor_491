# ui/gui_titanpark_integration.py
import os
import tkinter as tk
from tkinter import messagebox

from PIL import Image, ImageTk

from titanpark_integration.client import TitanParkError
from titanpark_integration.recommendation import recommend_parking_now

from ui import theme


def _clear_frame(frame) -> None:
    for widget in frame.winfo_children():
        widget.destroy()


def show_parking_helper(frame):
    _clear_frame(frame)

    try:
        frame.configure(bg=theme.CONTENT_BG)
    except Exception:
        pass

    # --- Logo (above header) ---
    try:
        here = os.path.dirname(__file__)  # .../ui
        logo_path = os.path.join(here, "assets", "titanpark_logo.png")

        img = Image.open(logo_path)
        target_width = 180
        w, h = img.size
        scale = target_width / float(w)
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

        logo = ImageTk.PhotoImage(img, master=frame.winfo_toplevel())

        logo_label = tk.Label(frame, image=logo, bg=theme.CONTENT_BG)
        logo_label.image = logo  # keep reference
        logo_label.pack(pady=(24, 10))
    except Exception as e:
        print(f"[TitanPark] Could not load logo: {e}")

    header = tk.Label(
        frame,
        text="Find Parking Fast, with TitanPark",
        font=theme.FONT_TITLE,
        bg=theme.CONTENT_BG,
        fg=theme.TEXT_PRIMARY,
    )
    header.pack(pady=(0, 12))

    result_label = tk.Label(
        frame,
        text="",
        wraplength=600,
        justify="left",
        font=theme.FONT_BODY,
        bg=theme.CONTENT_BG,
        fg=theme.TEXT_MUTED,
    )
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

    btn = tk.Button(frame, text="Check Parking Now", command=refresh)
    try:
        theme.style_primary_button(btn)
    except Exception:
        pass
    btn.pack(pady=10)
