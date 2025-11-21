# tests/test_gui.py
"""
Unit tests for ui.gui using lightweight 'Dummy' tkinter widgets so the tests
can run headless and deterministically (no real windows, no blocking mainloops).
"""

import threading  # used by gui.main_test_ui option 3 implementation (it spawns a thread)
import time  # only imported here historically; not required for the dummy approach
import tkinter as tk  # we patch attributes on this module during tests
import tkinter.ttk as ttk

from ui import gui  # module under test (contains main_int_ui and main_test_ui)


# --- Dummy replacements for tkinter widgets to avoid opening real windows ---
#
# We implement only the small subset of the Tk API that gui.py uses:
#  - Tk(): title(), geometry(), update_idletasks(), protocol(), after(), mainloop(), destroy()
#  - Label(parent, text=""): pack()
#
# This keeps tests fast and avoids requiring an X display / GUI environment.
# See pytest's monkeypatch docs for replacing attributes at runtime.
class DummyTk:
    def __init__(self):
        # track whether destroy() was called (useful for debug/asserts if needed)
        self._destroyed = False
        self.tk = object()  # minimal placeholder so attributes exist
        self._children = []  #: track children like real Tk

        # Register the Tk "default root" so ttk.Style() doesn't assert.
        import tkinter as _tk

        _tk._default_root = self

    # NEW: Tkinter variables call master._root(), so provide it.
    def _root(self):
        return self

    def title(self, *args, **kwargs):
        # GUI sets window title — noop in tests
        return None

    def columnconfigure(self, *args, **kwargs):
        return None

    def rowconfigure(self, *args, **kwargs):
        return None

    def geometry(self, *args, **kwargs):
        # GUI sets geometry — noop in tests
        return None

    def update_idletasks(self):
        # Called by option 2 for a quick create/destroy sanity check — noop.
        return None

    def destroy(self):
        # mark destroyed quickly so tests observing state can detect it
        self._destroyed = True
        # detach children
        for c in list(self._children):
            try:
                c.destroy()
            except Exception:
                pass
        self._children.clear()
        return None

    def protocol(self, *args, **kwargs):
        # used to register WM_DELETE_WINDOW handler — noop in tests
        return None

    def after(self, ms, func, *a, **kw):
        """
        Tk.after normally schedules `func` to run after `ms` milliseconds.
        For unit tests we call it *immediately* so tests don't sleep.

        This simulates the *behavior* (the callback executes) without timing.
        If you need to assert timing behavior specifically, write an integration test
        that uses the real Tk and a short ms value instead.
        See Tkinter 'after' documentation.
        """
        try:
            func(*a, **kw)
        except Exception:
            # swallow exceptions from callbacks so test harness can handle them explicitly
            pass
        return None

    def mainloop(self):
        # Real mainloop blocks; our Dummy mainloop returns immediately so tests don't hang.
        # This is the key to avoiding an infinite-blocking call in tests.
        return None


# minimal stand-in for tk.StringVar used by Label(textvariable=...)
class DummyStringVar:
    def __init__(self, master=None, value="", name=None):
        self._value = value

    def set(self, value):
        self._value = value

    def get(self):
        return self._value

    # Tkinter exposes trace_add/trace in modern/legacy APIs; keep as no-ops.
    def trace_add(self, mode, callback):
        return None

    def trace(self, mode, callback):
        return None


# Added Code: a tiny generic widget used to stand in for tk.Frame (and could be re-used if we need more)
class _DummyWidget:
    def __init__(self, *a, **kw):
        self._packed = False
        self._gridded = False
        self._placed = False
        self._children = []
        self.master = None

    def pack(self, *a, **kw):
        self._packed = True

    def grid(self, *a, **kw):
        self._gridded = True

    def place(self, *a, **kw):
        self._placed = True

    def config(self, *a, **kw):
        return None

    configure = config

    def columnconfigure(self, *a, **kw):
        return None

    def rowconfigure(self, *a, **kw):
        return None

    def grid_propagate(self, flag):
        return None

    def grid_remove(self, *a, **kw):
        """Simulate hiding the widget while preserving grid options."""
        self._gridded = False
        return None

    def grid_forget(self, *a, **kw):
        """Simulate removing the widget from the grid entirely."""
        self._gridded = False
        return None

    def winfo_children(self):
        """Return a shallow copy of children like real Tk."""
        return list(self._children)

    def destroy(self):
        self._packed = self._gridded = self._placed = False
        for c in list(self._children):
            try:
                c.destroy()
            except Exception:
                pass
        self._children.clear()
        if self.master and hasattr(self.master, "_children"):
            try:
                self.master._children.remove(self)
            except ValueError:
                pass

    # ---- New helpers so GUI code works under tests ----

    def bind(self, *a, **kw):  # Added Code
        """No-op event binding (for .bind calls on Labels/Entries)."""  # Added Code
        return None  # Added Code

    def pack_propagate(self, flag):  # Added Code
        """No-op for pack_propagate used on Frames in the Help page."""  # Added Code
        return None  # Added Code

    def winfo_toplevel(self):  # Added Code
        """Return the logical root window for Toplevel parenting."""  # Added Code
        if getattr(self, "master", None) is not None:  # Added Code
            return self.master  # Added Code
        return self  # Added Code

    def title(self, *a, **kw):  # Added Code
        """No-op window title setter for dummy Toplevels."""  # Added Code
        return None  # Added Code

    def geometry(self, *a, **kw):  # Added Code
        """No-op geometry setter for dummy Toplevels."""  # Added Code
        return None  # Added Code

    def transient(self, *a, **kw):  # Added Code
        """No-op transient() for dummy Toplevels."""  # Added Code
        return None  # Added Code

    def grab_set(self, *a, **kw):  # Added Code
        """No-op grab_set() for dummy Toplevels."""  # Added Code
        return None  # Added Code

    def focus_set(self, *a, **kw):  # Added Code
        """No-op focus_set() for dummy widgets (entries, windows)."""  # Added Code
        return None  # Added Code


class DummyFrame(_DummyWidget):
    """Drop-in stand-in for tk.Frame in tests (no real Tk calls)."""

    def __init__(self, master, *a, **kw):
        super().__init__()
        self.master = master
        if hasattr(master, "_children"):
            master._children.append(self)


class DummyButton(_DummyWidget):  # (future-proofing if gui creates buttons)
    def __init__(self, master=None, *a, **kw):
        super().__init__()
        self.master = master
        if master is not None and hasattr(master, "_children"):
            master._children.append(self)


class DummyLabel(_DummyWidget):
    """
    Drop-in stand-in for tk.Label with support for text/textvariable and
    no-op geometry managers (pack/grid/place).
    """

    def __init__(self, parent, text="", textvariable=None, **kwargs):
        super().__init__()
        # store a couple fields in case tests want to inspect them
        self.parent = parent
        self.text = text
        self.textvariable = textvariable
        # swallow any other Label options (bd, relief, anchor, padx, pady, etc.)
        self._options = dict(kwargs)
        self.master = parent
        if hasattr(parent, "_children"):
            parent._children.append(self)

    # Allow runtime updates (e.g., .config(text="...") or .config(textvariable=var))
    def config(self, **kwargs):
        if "text" in kwargs:
            self.text = kwargs["text"]
        if "textvariable" in kwargs:
            self.textvariable = kwargs["textvariable"]
        # retain anything else to mimic Tk option bag
        self._options.update(kwargs)

    configure = config


class DummyStyle:
    """No-op replacement for ttk.Style used by main_int_ui during tests."""

    def __init__(self, *a, **kw):
        pass

    def theme_use(self, *a, **kw):
        return None

    def configure(self, *a, **kw):
        return None

    def map(self, *a, **kw):
        return {}


# --- New stubs used only in tests to avoid a real Tcl/Tk interpreter ---
class DummyPhotoImage:
    def __init__(self, *a, **kw):
        pass


# --- Tests ---
def test_main_test_ui_option1_monkeypatched(monkeypatch):
    """
    Option 1 in gui.main_test_ui calls main_int_ui() which launches the GUI and
    usually enters mainloop(). We patch Tk and Label so main_int_ui uses Dummy
    widgets and returns immediately.
    """
    # Replace tkinter.Tk and tkinter.Label with our dummies for this test only.
    # pytest.monkeypatch will undo these replacements at test teardown.
    monkeypatch.setattr(tk, "Tk", DummyTk, raising=False)
    monkeypatch.setattr(tk, "Label", DummyLabel, raising=False)
    monkeypatch.setattr(tk, "Frame", DummyFrame, raising=False)
    monkeypatch.setattr(tk, "Button", DummyButton, raising=False)
    monkeypatch.setattr(tk, "StringVar", DummyStringVar, raising=False)
    monkeypatch.setattr(ttk, "Style", DummyStyle, raising=False)
    monkeypatch.setattr(ttk, "Button", DummyButton, raising=False)

    # Critical: ui.gui imports PhotoImage directly; stub it at the module-under-test symbol.
    monkeypatch.setattr(gui, "PhotoImage", DummyPhotoImage, raising=False)
    # Also patch Toplevel since main_int_ui creates one.
    monkeypatch.setattr(tk, "Toplevel", DummyFrame, raising=False)

    # Now gui.main_test_ui(1) executes the same code paths but with Dummy widgets.
    assert gui.main_test_ui(1) is True


def test_main_test_ui_option2_headless(monkeypatch):
    """
    Option 2 path creates a Tk root, calls update_idletasks(), then destroys it.
    Patching Tk to DummyTk makes the create/destroy fast and safe for headless CI.
    """
    monkeypatch.setattr(tk, "Tk", DummyTk, raising=False)

    # main_test_ui option 2 should succeed quickly (create/destroy) with DummyTk.
    assert gui.main_test_ui(2) is True


def test_main_test_ui_option3_auto_close(monkeypatch):
    """
    Option 3 spawns a daemon thread that runs a GUI and schedules an auto-close
    using root.after(). Our DummyTk.after() calls the callback immediately, so
    the thread runs and exits quickly without sleeps.
    """
    monkeypatch.setattr(tk, "Tk", DummyTk, raising=False)
    monkeypatch.setattr(tk, "Label", DummyLabel, raising=False)

    # Because DummyTk.after() executes the scheduled callback immediately,
    # this test runs fast and deterministically.
    assert gui.main_test_ui(3) is True


# --- Additional tests for individual UI functions to ensure they build without errors ---


def test_show_home(monkeypatch):
    """Ensure show_home builds UI without errors."""
    monkeypatch.setattr(tk, "Label", DummyLabel)
    monkeypatch.setattr(gui, "set_active_button", lambda *args, **kwargs: None)

    root = DummyTk()
    frame = DummyFrame(root)

    gui.show_home(frame)

    # home view creates labels inside the frame
    assert len(frame._children) > 0


def test_show_login(monkeypatch):
    """Ensure show_login builds UI without errors."""
    monkeypatch.setattr(tk, "Label", DummyLabel)
    monkeypatch.setattr(tk, "Entry", DummyFrame)
    monkeypatch.setattr(tk, "Button", DummyButton)
    monkeypatch.setattr(tk, "StringVar", DummyStringVar)

    monkeypatch.setattr(ttk, "Frame", DummyFrame)
    monkeypatch.setattr(ttk, "Button", DummyButton)
    monkeypatch.setattr(gui, "set_active_button", lambda *args, **kwargs: None)

    root = DummyTk()
    frame = DummyFrame(root)

    gui.show_login(frame)

    assert len(frame._children) > 0


def test_show_forgot_password(monkeypatch):
    """Ensure forgot-password modal builds UI without errors."""
    monkeypatch.setattr(tk, "Toplevel", DummyFrame)
    monkeypatch.setattr(tk, "Label", DummyLabel)
    monkeypatch.setattr(tk, "StringVar", DummyStringVar)

    monkeypatch.setattr(ttk, "Entry", DummyFrame)
    monkeypatch.setattr(ttk, "Button", DummyButton)
    monkeypatch.setattr(gui, "set_active_button", lambda *args, **kwargs: None)

    root = DummyTk()
    frame = DummyFrame(root)

    gui.show_forgot_password(frame)


def test_update_nav_buttons_logged_out():
    gui.nav_buttons = {
        "Login": DummyButton(),
        "Logout": DummyButton(),
        "Home": DummyButton(),
        "Preferences": DummyButton(),
        "Recommendations": DummyButton(),
        "Profile": DummyButton(),
        "Help": DummyButton(),
    }
    gui.login_status = False
    gui.current_user = None

    gui.update_nav_buttons()

    assert gui.nav_buttons["Login"]._gridded is True
    assert gui.nav_buttons["Logout"]._gridded is False


def test_show_registration(monkeypatch):
    """Ensure show_registration builds UI without errors."""
    monkeypatch.setattr(tk, "Label", DummyLabel)
    monkeypatch.setattr(tk, "StringVar", DummyStringVar)

    monkeypatch.setattr(ttk, "Frame", DummyFrame)
    monkeypatch.setattr(ttk, "Entry", DummyFrame)
    monkeypatch.setattr(ttk, "Button", DummyButton)
    monkeypatch.setattr(ttk, "Label", DummyLabel)

    monkeypatch.setattr(gui, "set_active_button", lambda *args, **kwargs: None)

    root = DummyTk()
    frame = DummyFrame(root)

    gui.show_registration(frame)

    # Should create many fields: labels, entries, frames
    assert len(frame._children) > 0


def test_show_help(monkeypatch):
    """Ensure the Help page builds without errors."""
    monkeypatch.setattr(tk, "Label", DummyLabel)
    monkeypatch.setattr(ttk, "Label", DummyLabel)
    monkeypatch.setattr(ttk, "Entry", DummyFrame)
    monkeypatch.setattr(ttk, "Button", DummyButton)
    monkeypatch.setattr(ttk, "Frame", DummyFrame)

    monkeypatch.setattr(gui, "set_active_button", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        gui, "show_about_dialog", lambda *args, **kwargs: None
    )  # stub for About

    root = DummyTk()
    frame = DummyFrame(root)

    gui.show_help(frame)

    # Should have help content and search area
    assert len(frame._children) > 0


def test_show_profile(monkeypatch):
    """Ensure profile page builds without errors with a mock current_user."""
    # Patch widgets
    monkeypatch.setattr(tk, "Label", DummyLabel)
    monkeypatch.setattr(ttk, "Label", DummyLabel)
    monkeypatch.setattr(ttk, "LabelFrame", DummyFrame)
    monkeypatch.setattr(ttk, "Button", DummyButton)
    monkeypatch.setattr(tk, "Toplevel", DummyFrame)
    monkeypatch.setattr(gui, "set_active_button", lambda *args, **kwargs: None)

    # Fake logged-in user
    gui.current_user = {
        "first_name": "Test",
        "last_name": "User",
        "email": "test@example.com",
    }

    root = DummyTk()
    frame = DummyFrame(root)

    gui.show_profile(frame)

    # Should create child widgets: labels, settings frame, button(s)
    assert len(frame._children) > 0

    # Grab first label - profile header exists
    header = frame._children[0]
    assert isinstance(header, DummyLabel)

    # Ensure email/name were inserted somewhere in UI
    texts = [w.text for w in frame._children if hasattr(w, "text")]
    assert any("Test User" in t for t in texts if t)
    assert any("test@example.com" in t for t in texts if t)


def test_show_logout(monkeypatch):
    """Ensure show_logout logs out user, clears state, and rebuilds UI without errors."""

    # Patch set_active_button
    monkeypatch.setattr(gui, "set_active_button", lambda *a, **k: None)

    # Patch messagebox.showinfo so it doesn't open real popups
    monkeypatch.setattr(gui.tk, "Label", DummyLabel)
    monkeypatch.setattr(gui.messagebox, "showinfo", lambda *a, **k: None)

    # Patch update_nav_buttons so it doesn’t expect real buttons
    monkeypatch.setattr(gui, "update_nav_buttons", lambda *a, **k: None)

    # Fake user is currently logged in
    gui.login_status = True
    gui.current_user = {"email": "test@example.com"}

    # Prepare a dummy frame
    root = DummyTk()
    frame = DummyFrame(root)

    monkeypatch.setattr(
        gui, "show_home", lambda f: DummyLabel(f, text="HomePageLoaded")
    )

    # Call function under test
    gui.show_logout(frame)

    # logout should clear login state
    assert gui.login_status is False
    assert gui.current_user is None

    # After logout, show_home should have been invoked → frame contains label "HomePageLoaded"
    assert len(frame._children) > 0
    texts = [child.text for child in frame._children if hasattr(child, "text")]
    assert "HomePageLoaded" in texts
