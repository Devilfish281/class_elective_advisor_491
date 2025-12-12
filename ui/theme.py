# ui/theme.py
from tkinter import ttk

TITAN_BG = "#050816"        # overall background
SIDEBAR_BG = "#050816"      # left nav
CONTENT_BG = "#050816"      # main content
CARD_BG = "#111827"         # panels/cards
CARD_BORDER = "#1F2933"
ACCENT_ORANGE = "#F97316"   # TitanPark orange
ACCENT_BLUE = "#1D4ED8"     # TitanPark blue
TEXT_PRIMARY = "#F9FAFB"
TEXT_MUTED = "#9CA3AF"
INPUT_BG = "#111827"
INPUT_BORDER = "#374151"


def apply_root_theme(root):
    root.configure(bg=TITAN_BG)


def style_main_frame(frame):
    frame.configure(bg=CONTENT_BG)


def style_sidebar_frame(frame):
    frame.configure(bg=SIDEBAR_BG, bd=0, highlightthickness=0)


def style_status_bar(label):
    label.configure(bg="#020617", fg=TEXT_MUTED)


def init_sidebar_styles(style: ttk.Style):
    style.theme_use("clam")
    style.configure(
        "TButton",
        padding=8,
        anchor="w",
        font=("Helvetica", 12),
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
        font=("Helvetica", 12, "bold"),
        background=ACCENT_ORANGE,
        foreground=TEXT_PRIMARY,
        borderwidth=0,
    )


def style_card_frame(frame):
    frame.configure(
        bg=CARD_BG,
        bd=0,
        highlightbackground=CARD_BORDER,
        highlightthickness=1,
    )


def style_label_title(label):
    label.configure(bg=CARD_BG, fg=TEXT_PRIMARY, font=("Helvetica", 18, "bold"))


def style_label_body(label):
    label.configure(bg=CARD_BG, fg=TEXT_MUTED, font=("Helvetica", 11))


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
        font=("Helvetica", 11, "bold"),
        cursor="hand2",
    )


def style_entry(entry):
    entry.configure(
        bg=INPUT_BG,
        fg=TEXT_PRIMARY,
        insertbackground=TEXT_PRIMARY,
        relief="flat",
        highlightthickness=1,
        highlightbackground=INPUT_BORDER,
    )
