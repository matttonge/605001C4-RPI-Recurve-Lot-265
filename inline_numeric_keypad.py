"""In-window touch numeric keypad for Linux/Pi stability."""
import tkinter as tk
from tkinter import ttk

from keypad_layout import (
    create_keypad_preview_entry,
    focus_keypad_preview,
    install_keypad_keyboard,
    place_inline_keypad_by_side,
    remove_keypad_keyboard,
)


class InlineNumericKeypad:
    _BTN_FONT = ("Segoe UI", 22, "bold")
    _ACT_FONT = ("Segoe UI", 18, "bold")
    _MIN_BTN = 72

    def __init__(self, parent, string_var, on_exit=None, side=None, title=None):
        self._owner = parent.winfo_toplevel()
        self._string_var = string_var
        self._on_exit = on_exit
        self._side = side
        self._closed = False
        self._title = title

        self._panel = tk.Frame(parent, bd=2, relief=tk.RIDGE, bg="#d9d9d9")

        outer = ttk.Frame(self._panel, padding=12)
        outer.pack(fill=tk.BOTH, expand=True)

        self._title_label = ttk.Label(
            outer,
            text="",
            font=("Segoe UI", 14, "bold"),
            anchor=tk.CENTER,
        )
        self._title_label.pack(fill=tk.X, pady=(0, 8))
        self._apply_title()

        self._preview = create_keypad_preview_entry(outer, string_var)
        self._preview.pack(fill=tk.X, pady=(0, 10), ipady=6)

        pad = ttk.Frame(outer)
        pad.pack()

        digits = [
            ("7", 0, 0), ("8", 0, 1), ("9", 0, 2),
            ("4", 1, 0), ("5", 1, 1), ("6", 1, 2),
            ("1", 2, 0), ("2", 2, 1), ("3", 2, 2),
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

        self._panel.update_idletasks()
        self._position_panel()
        self.lift()
        self._owner.after(50, self._focus_preview)

    def _apply_title(self, title=None):
        if title is not None:
            self._title = title
        text = self._title or "Numeric entry"
        try:
            self._title_label.configure(text=text)
        except (tk.TclError, AttributeError):
            pass

    def _mk_btn(self, parent, text, row, col, command, font=None):
        f = font or self._BTN_FONT
        b = tk.Button(parent, text=text, font=f, width=3, height=1, command=command, takefocus=0)
        b.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
        parent.grid_columnconfigure(col, minsize=self._MIN_BTN)
        parent.grid_rowconfigure(row, minsize=self._MIN_BTN)
        return b

    def _mk_wide(self, parent, text, command, side, expand, padx):
        b = tk.Button(parent, text=text, font=self._ACT_FONT, height=2, command=command, takefocus=0)
        b.pack(side=side, fill=tk.BOTH, expand=expand, padx=padx)
        return b

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
        self._owner.after_idle(self._focus_preview)

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

    def set_target(self, string_var, on_exit=None, side=None, title=None):
        self._string_var = string_var
        if on_exit is not None:
            self._on_exit = on_exit
        if side is not None:
            self._side = side
        if title is not None:
            self._apply_title(title)
        self._preview.configure(textvariable=string_var)
        install_keypad_keyboard(
            self._preview,
            self._append,
            self._decimal,
            self._backspace,
            self._clear,
            self._exit,
        )
        self._position_panel()
        self.lift()
        self._clear()

    def _position_panel(self):
        place_inline_keypad_by_side(self._panel, self._owner, self._side)

    def winfo_exists(self):
        return int(self._panel.winfo_exists())

    def lift(self):
        try:
            self._panel.lift()
            self._panel.tkraise()
        except tk.TclError:
            pass

    def close_modal(self):
        self._exit()

    def _exit(self):
        if self._closed:
            return
        self._closed = True
        cb = self._on_exit
        remove_keypad_keyboard()
        try:
            self._panel.destroy()
        except tk.TclError:
            pass
        if cb:
            cb()
