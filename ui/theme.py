from tkinter import ttk
import tkinter as tk
import tkinter.font as tkfont

# Colors

TITAN_BG = "#050816"
SIDEBAR_BG = "#050816"
CONTENT_BG = "#050816"
CARD_BG = "#111827"
CARD_BORDER = "#1F2933"

ACCENT_ORANGE = "#F97316"
ACCENT_BLUE = "#1D4ED8"

TEXT_PRIMARY = "#F9FAFB"
TEXT_MUTED = "#9CA3AF"

INPUT_BG = "#111827"
INPUT_BORDER = "#374151"


# Font Initialization

def _pick_font_family(
    preferred=("Museo Sans", "MuseoSans", "Poppins", "Helvetica", "Arial")
):
    available = set(tkfont.families())
    for fam in preferred:
        if fam in available:
            return fam
    return "Arial"


def init_fonts(root: tk.Tk):
    """
    Must be called ONCE after root = tk.Tk()
    """
    family = _pick_font_family()

    global FONT_FAMILY
    global FONT_BASE
    global FONT_BODY
    global FONT_TITLE
    global FONT_SUBTITLE
    global FONT_SIDEBAR
    global FONT_BUTTON

    FONT_FAMILY = family
    FONT_BASE = (family, 12)
    FONT_BODY = (family, 11)
    FONT_TITLE = (family, 18, "bold")
    FONT_SUBTITLE = (family, 14, "bold")
    FONT_SIDEBAR = (family, 12)
    FONT_BUTTON = (family, 11, "bold")

    print(f"[theme] Using font family: {family}")


# Root and Frame Styles

def apply_root_theme(root):
    root.configure(bg=TITAN_BG)


def style_main_frame(frame):
    frame.configure(bg=CONTENT_BG)


def style_sidebar_frame(frame):
    frame.configure(bg=SIDEBAR_BG, bd=0, highlightthickness=0)


def style_status_bar(label):
    label.configure(bg="#020617", fg=TEXT_MUTED, font=FONT_BODY)


def style_card_frame(frame):
    frame.configure(
        bg=CARD_BG,
        bd=0,
        highlightbackground=CARD_BORDER,
        highlightthickness=1,
    )


# Label styles

def style_label_title(label):
    label.configure(
        bg=CARD_BG,
        fg=TEXT_PRIMARY,
        font=FONT_TITLE,
    )


def style_label_body(label):
    label.configure(
        bg=CARD_BG,
        fg=TEXT_MUTED,
        font=FONT_BODY,
    )


# Button styles

def init_sidebar_styles(style: ttk.Style):
    style.theme_use("clam")

    style.configure(
        "TButton",
        padding=8,
        anchor="w",
        font=FONT_SIDEBAR,
        background=SIDEBAR_BG,
        foreground=TEXT_MUTED,
        borderwidth=0,
    )

    style.map(
        "TButton",
        background=[("active", "#1F2937"), ("pressed", "#1F2937")],
        foreground=[("active", TEXT_PRIMARY)],
    )

    style.configure(
        "Active.TButton",
        padding=8,
        anchor="w",
        font=(FONT_FAMILY, 12, "bold"),
        background=ACCENT_ORANGE,
        foreground=TEXT_PRIMARY,
        borderwidth=0,
    )


def style_primary_button(button):
    button.configure(
        bg=ACCENT_BLUE,
        fg="white",
        activebackground="#1E40AF",
        activeforeground="white",
        relief="flat",
        borderwidth=0,
        padx=16,
        pady=8,
        font=FONT_BUTTON,
        cursor="hand2",
    )


# Input Styles
def style_entry(entry):
    entry.configure(
        bg=INPUT_BG,
        fg=TEXT_PRIMARY,
        insertbackground=TEXT_PRIMARY,
        relief="flat",
        highlightthickness=1,
        highlightbackground=INPUT_BORDER,
        font=FONT_BODY,
    )
