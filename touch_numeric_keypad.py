"""Modal touch-friendly numeric keypad for tkinter (e.g. 10\" touchscreen)."""
import sys
import tkinter as tk
from tkinter import ttk

from keypad_layout import (
    create_keypad_preview_entry,
    focus_keypad_preview,
    install_keypad_keyboard,
    place_toplevel_keypad_by_side,
    remove_keypad_keyboard,
)


class TouchNumericKeypad(tk.Toplevel):
    """Modal toplevel with 0-9, decimal point, backspace, clear, and exit."""

    _BTN_FONT = ("Segoe UI", 22, "bold")
    _ACT_FONT = ("Segoe UI", 18, "bold")
    _MIN_BTN = 72

    def __init__(self, parent, string_var, on_exit=None, side=None, title=None):
        # Screen 2 is a borderless (overrideredirect) Toplevel. On Linux, a child
        # Toplevel of that window often never maps or stays invisible. Parent
        # this dialog to the real Tk root and only use the setup window for
        # placement/transient hints.
        top = parent.winfo_toplevel()
        root_master = getattr(top, "master", None)
        master_w = root_master if root_master is not None else top
        super().__init__(master_w)
        self._owner = top
        self._string_var = string_var
        self._on_exit = on_exit
        self._side = side
        self._closed = False
        self._preview = None
        self._title = title

        self._apply_title()
        # transient(overrideredirect_parent) prevents some Linux WMs from ever
        # showing the dialog; Windows still benefits from grouping with Screen 2.
        if sys.platform.startswith("linux"):
            pass
        else:
            try:
                self.transient(self._owner)
            except tk.TclError:
                pass
        try:
            # Some Linux/Pi window managers flash and immediately unmap topmost
            # dialog windows. Keep topmost for Windows only.
            self.attributes("-topmost", not sys.platform.startswith("linux"))
        except tk.TclError:
            pass
        self.resizable(False, False)

        outer = ttk.Frame(self, padding=12)
        outer.pack(fill=tk.BOTH, expand=True)

        self._preview = create_keypad_preview_entry(outer, string_var)
        self._preview.pack(fill=tk.X, pady=(0, 10), ipady=6)

        pad = ttk.Frame(outer)
        pad.pack()

        digits = [
            ("7", 0, 0),
            ("8", 0, 1),
            ("9", 0, 2),
            ("4", 1, 0),
            ("5", 1, 1),
            ("6", 1, 2),
            ("1", 2, 0),
            ("2", 2, 1),
            ("3", 2, 2),
        ]
        for text, r, c in digits:
            self._mk_btn(pad, text, r, c, lambda t=text: self._append(t))

        self._mk_btn(pad, ".", 3, 0, self._decimal)
        self._mk_btn(pad, "0", 3, 1, lambda: self._append("0"))
        self._mk_btn(pad, "⌫", 3, 2, self._backspace, font=self._ACT_FONT)

        row4 = ttk.Frame(outer)
        row4.pack(fill=tk.X, pady=(10, 0))
        self._mk_wide(row4, "Clear", self._clear, side=tk.LEFT, expand=True, padx=(0, 6))
        self._mk_wide(row4, "ENTER", self._exit, side=tk.LEFT, expand=True, padx=(6, 0))

        install_keypad_keyboard(
            self._preview,
            self._append,
            self._decimal,
            self._backspace,
            self._clear,
            self._exit,
        )

        self._clear()

        self.protocol("WM_DELETE_WINDOW", self._exit)
        self.bind("<Escape>", lambda e: self._exit())

        self.update_idletasks()
        self._position_window()
        try:
            self.deiconify()
            self.state('normal')
        except tk.TclError:
            pass
        try:
            self.lift(self._owner)
        except tk.TclError:
            pass
        self.after(10, self._take_grab)

    def _apply_title(self, title=None):
        if title is not None:
            self._title = title
        self.title(self._title or "Numeric entry")

    def _mk_btn(self, parent, text, row, col, command, font=None):
        f = font or self._BTN_FONT
        b = tk.Button(
            parent,
            text=text,
            font=f,
            width=3,
            height=1,
            command=command,
            takefocus=0,
        )
        b.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
        parent.grid_columnconfigure(col, minsize=self._MIN_BTN)
        parent.grid_rowconfigure(row, minsize=self._MIN_BTN)
        return b

    def _mk_wide(self, parent, text, command, side, expand, padx):
        b = tk.Button(
            parent,
            text=text,
            font=self._ACT_FONT,
            height=2,
            command=command,
            takefocus=0,
        )
        b.pack(side=side, fill=tk.BOTH, expand=expand, padx=padx)
        return b

    def _center_on_parent(self, parent):
        try:
            px = parent.winfo_rootx()
            py = parent.winfo_rooty()
            pw = parent.winfo_width()
            ph = parent.winfo_height()
        except tk.TclError:
            return
        ww = self.winfo_width()
        wh = self.winfo_height()
        x = px + max(0, (pw - ww) // 2)
        y = py + max(0, (ph - wh) // 2)
        self.geometry(f"+{x}+{y}")

    def _position_window(self):
        place_toplevel_keypad_by_side(self, self._owner, self._side)

    def _take_grab(self):
        try:
            # wait_visibility can block indefinitely if the WM never delivers
            # VisibilityNotify (seen with some overrideredirect / touch setups).
            if sys.platform.startswith("win"):
                self.wait_visibility()
            else:
                self.update_idletasks()
        except tk.TclError:
            pass
        try:
            self.lift()
        except tk.TclError:
            pass
        # On Raspberry Pi/X11 touch setups, modal grabs can lock pointer input
        # after dialog close. Keep grab/focus-force only on Windows.
        if sys.platform.startswith("win"):
            try:
                self.grab_set()
            except tk.TclError:
                pass
            try:
                self.focus_force()
            except tk.TclError:
                pass
        else:
            self.after(50, self._focus_preview)

    def _focus_preview(self):
        try:
            self._owner.focus_force()
        except tk.TclError:
            pass
        focus_keypad_preview(self._preview)

    def _edit_value(self):
        return (self._string_var.get() or "").strip()

    def _set_edit_value(self, s):
        self._string_var.set(s)
        self.after_idle(self._focus_preview)

    def _append(self, ch):
        cur = self._edit_value()
        if cur == "0" and ch != ".":
            cur = ""
        self._set_edit_value(cur + ch)

    def _decimal(self):
        cur = self._edit_value()
        if "." in cur:
            return
        if not cur:
            cur = "0"
        self._set_edit_value(cur + ".")

    def _backspace(self):
        cur = self._edit_value()
        if cur:
            self._set_edit_value(cur[:-1])

    def _clear(self):
        self._set_edit_value("")

    def close_modal(self):
        """Same as Exit: release grab, destroy, run commit callback."""
        self._exit()

    def set_target(self, string_var, on_exit=None, side=None, title=None):
        """Retarget this keypad to a different Entry/StringVar without recreating."""
        self._string_var = string_var
        if on_exit is not None:
            self._on_exit = on_exit
        if side is not None:
            self._side = side
        if title is not None:
            self._apply_title(title)
        if self._preview is not None:
            try:
                self._preview.configure(textvariable=string_var)
            except tk.TclError:
                pass
        self.update_idletasks()
        self._position_window()
        try:
            self.lift(self._owner)
        except tk.TclError:
            pass
        self._clear()

    def _exit(self):
        if self._closed:
            return
        self._closed = True
        cb = self._on_exit
        remove_keypad_keyboard()
        try:
            self.grab_release()
        except tk.TclError:
            pass
        self.destroy()
        if cb:
            cb()
