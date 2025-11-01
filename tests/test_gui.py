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

    # Tk geometry managers — noops for tests
    def pack(self, *a, **kw):
        self._packed = True

    def grid(self, *a, **kw):
        self._gridded = True

    def place(self, *a, **kw):
        self._placed = True

    # Common config helpers used by real widgets — also noops
    def config(self, *a, **kw):
        return None

    configure = config

    # Some UIs call column/row configure on frames
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
