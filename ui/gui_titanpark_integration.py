# ui/gui_titanpark_integration.py
import os
import requests
import pandas as pd
import tkinter as tk
from tkinter import messagebox
from tkcalendar import Calendar
from datetime import date
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

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

    tk.Button(frame, text="Check Parking Now", command=refresh).pack(pady=5)

def show_parking_history_helper(frame):
    """Display the TitanPark parking history helper UI in the given frame."""
    _clear_frame(frame)
    if hasattr(frame, 'set_active_button'):
        frame.set_active_button("Parking History")
    parking_url = os.getenv('TITANPARK_API_BASE_URL')

    def _refresh():
        graph_frame.pack_forget()
        result_label.pack_forget()
        m,d,y = cal.get_date().split('/')
        selected_date = f'20{y}-{m.zfill(2)}-{d.zfill(2)}'
        res = requests.get(f"{parking_url}/history/parking_data/{selected_date}")
        history = res.json()['history']
        if len(history) == 0:
            result_label.config(text="There is no data for this day")
            result_label.pack(pady=10)
        else:
            history_df = pd.DataFrame(history)
            # Convert datetime to Pacific time
            history_df['datetime'] = pd.to_datetime(history_df['datetime'])
            history_df['datetime'] = history_df['datetime'].dt.tz_localize('US/Pacific')

            # Create graph
            fig = Figure(figsize=(10, 6), dpi=100)
            ax = fig.add_subplot(111)

            # Plot each structure
            for struct_name in history_df['struct_name'].unique():
                struct_data = history_df[history_df['struct_name'] == struct_name]
                struct_data = struct_data.sort_values('datetime')
                ax.plot(
                    struct_data['datetime'],
                    struct_data['perc_full'] * 100,
                    marker='o',
                    label=struct_name,
                    linewidth=2
                    )
                
            # Set labels
            ax.set_xlabel("Time", fontsize=12)
            ax.set_ylabel("Percent Full (%)", fontsize=12)
            ax.set_title(f"Parking Structure Occupancy ({selected_date})")
            ax.legend(loc='best')
            ax.grid(True, alpha=0.3)
            ax.set_ylim(0, 100)

            # Format x-axis time
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%I:%M %p', tz='US/Pacific'))
            fig.autofmt_xdate()

            # Show graph
            canvas = FigureCanvasTkAgg(fig, master=graph_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            graph_frame.pack(pady=0, fill=tk.BOTH, expand=True)

    # Header
    header = tk.Label(frame, text="Parking Occupancy History", font=("Helvetica", 16))

    # Calendar
    today = date.today()
    cal = Calendar(frame, selectmode = 'day', 
                   year = today.year, month = today.month, day = today.day)

    data_btn = tk.Button(frame, text = "Update Graph", command = _refresh)
    graph_frame = tk.Frame(frame)
    result_label = tk.Label(frame, text="", wraplength=600, justify="left")

    # Display elements
    header.pack(pady=10)
    cal.pack(pady=10)
    data_btn.pack(pady = 10)

    _refresh()
    btn = tk.Button(frame, text="Check Parking Now", command=refresh)
    try:
        theme.style_primary_button(btn)
    except Exception:
        pass
    btn.pack(pady=10)
