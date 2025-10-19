# tests/test_gui.py
"""
Unit tests for ui.gui using lightweight 'Dummy' tkinter widgets so the tests
can run headless and deterministically (no real windows, no blocking mainloops).
"""

import threading  # used by gui.main_test_ui option 3 implementation (it spawns a thread)
import time  # only imported here historically; not required for the dummy approach
import tkinter as tk  # we patch attributes on this module during tests

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

    def title(self, *args, **kwargs):
        # GUI sets window title — noop in tests
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


class DummyLabel:
    def __init__(self, parent, text=""):
        # store a couple fields in case tests want to inspect them
        self.parent = parent
        self.text = text

    def pack(self, *args, **kwargs):
        # GUI calls pack(); noop here
        return None


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
