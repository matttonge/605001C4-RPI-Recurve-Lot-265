"""Modal touch-friendly alphanumeric keypad for tkinter (e.g. 10\" touchscreen)."""
import sys
import tkinter as tk
from tkinter import ttk

from keypad_layout import (
    create_alpha_keypad_preview_entry,
    focus_keypad_preview,
    install_alpha_keypad_keyboard,
    place_toplevel_keypad_by_side,
    remove_keypad_keyboard,
)


class TouchAlphaKeypad(tk.Toplevel):
    """Modal toplevel QWERTY keyboard for lot-number style text entry."""

    _BTN_FONT = ("Segoe UI", 16, "bold")
    _ACT_FONT = ("Segoe UI", 14, "bold")
    _MIN_BTN = 56

    _ROWS = (
        ("1", "2", "3", "4", "5", "6", "7", "8", "9", "0"),
        ("Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"),
        ("A", "S", "D", "F", "G", "H", "J", "K", "L", "⌫"),
        ("⇧", "Z", "X", "C", "V", "B", "N", "M", "-", "_"),
    )

    def __init__(self, parent, string_var, on_exit=None, side=None, title=None, initial=None):
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
        self._shift = True
        self._letter_buttons = []

        self._apply_title()
        if sys.platform.startswith("linux"):
            pass
        else:
            try:
                self.transient(self._owner)
            except tk.TclError:
                pass
        try:
            self.attributes("-topmost", not sys.platform.startswith("linux"))
        except tk.TclError:
            pass
        self.resizable(False, False)

        outer = ttk.Frame(self, padding=10)
        outer.pack(fill=tk.BOTH, expand=True)

        self._preview = create_alpha_keypad_preview_entry(outer, string_var)
        self._preview.pack(fill=tk.X, pady=(0, 8), ipady=6)

        pad = ttk.Frame(outer)
        pad.pack()

        for r, row in enumerate(self._ROWS):
            for c, text in enumerate(row):
                if text == "⌫":
                    self._mk_btn(pad, text, r, c, self._backspace, font=self._ACT_FONT)
                elif text == "⇧":
                    self._shift_btn = self._mk_btn(
                        pad, text, r, c, self._toggle_shift, font=self._ACT_FONT
                    )
                else:
                    b = self._mk_btn(pad, text, r, c, lambda t=text: self._append_key(t))
                    if text.isalpha():
                        self._letter_buttons.append((b, text))

        row4 = ttk.Frame(outer)
        row4.pack(fill=tk.X, pady=(8, 0))
        self._mk_wide(row4, "Clear", self._clear, side=tk.LEFT, expand=True, padx=(0, 6))
        self._mk_wide(row4, "ENTER", self._exit, side=tk.LEFT, expand=True, padx=(6, 0))

        install_alpha_keypad_keyboard(
            self._preview,
            self._append,
            self._backspace,
            self._clear,
            self._exit,
        )

        if initial is not None:
            self._set_edit_value(str(initial))
        else:
            self._clear()
        self._refresh_letter_case()

        self.protocol("WM_DELETE_WINDOW", self._exit)
        self.bind("<Escape>", lambda e: self._exit())

        self.update_idletasks()
        self._position_window()
        try:
            self.deiconify()
            self.state("normal")
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
        self.title(self._title or "Lot Number")

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
        b.grid(row=row, column=col, padx=3, pady=3, sticky="nsew")
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

    def _position_window(self):
        place_toplevel_keypad_by_side(self, self._owner, self._side)

    def _take_grab(self):
        try:
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
        return self._string_var.get() or ""

    def _set_edit_value(self, s):
        self._string_var.set(s)
        self.after_idle(self._focus_preview)

    def _append(self, ch):
        self._set_edit_value(self._edit_value() + ch)

    def _append_key(self, key):
        if key.isalpha():
            ch = key.upper() if self._shift else key.lower()
        else:
            ch = key
        self._append(ch)
        if self._shift and key.isalpha():
            # One-shot shift like a phone keyboard after first letter.
            self._shift = False
            self._refresh_letter_case()

    def _toggle_shift(self):
        self._shift = not self._shift
        self._refresh_letter_case()

    def _refresh_letter_case(self):
        for btn, letter in self._letter_buttons:
            try:
                btn.configure(text=letter.upper() if self._shift else letter.lower())
            except tk.TclError:
                pass
        try:
            self._shift_btn.configure(relief=tk.SUNKEN if self._shift else tk.RAISED)
        except (tk.TclError, AttributeError):
            pass

    def _backspace(self):
        cur = self._edit_value()
        if cur:
            self._set_edit_value(cur[:-1])

    def _clear(self):
        self._set_edit_value("")
        self._shift = True
        self._refresh_letter_case()

    def close_modal(self):
        self._exit()

    def set_target(self, string_var, on_exit=None, side=None, title=None, initial=None):
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
        if initial is not None:
            self._set_edit_value(str(initial))
        else:
            self._clear()
        self._shift = True
        self._refresh_letter_case()

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
