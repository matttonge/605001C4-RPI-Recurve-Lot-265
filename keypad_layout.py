"""Shared placement for Screen 2 touch numeric keypads."""

import os
import sys
import tkinter as tk

# Vertical center of keypad as fraction of window height (above message box at ~0.78).
_KEYPAD_RELY = 0.42

_active_keypad_binding = []
_active_keypad_window = None
_linux_wm_decorated = 0
_linux_wm_decorated_window = None
_KIOSK_W = 1024
_KIOSK_H = 600


def use_kiosk_mode():
    """True on Raspberry Pi kiosk; False on Ubuntu/Windows/Jetson desktop development.

    Override with RECURVE_KIOSK=1|0.
    """
    env = os.environ.get("RECURVE_KIOSK", "").strip().lower()
    if env in ("1", "true", "yes", "on"):
        return True
    if env in ("0", "false", "no", "off"):
        return False
    try:
        with open("/proc/device-tree/model", "rb") as f:
            model = f.read().decode("utf-8", "ignore")
        if "Raspberry Pi" in model:
            return True
    except OSError:
        pass
    return False


def _configure_dev_window(window, target_w=_KIOSK_W, target_h=_KIOSK_H):
    """Movable decorated 1024x600 window for Ubuntu / Windows development."""
    geom = f"{target_w}x{target_h}"

    def _apply():
        try:
            window.overrideredirect(False)
            window.title("Recurve")
            window.configure(takefocus=True)
            window.resizable(False, False)
            window.minsize(target_w, target_h)
            window.maxsize(target_w, target_h)
            window.geometry(geom)
            window.update_idletasks()
        except tk.TclError:
            pass

    try:
        window.withdraw()
        _apply()
        window.deiconify()
        window.lift()
        _apply()
    except tk.TclError:
        _apply()

    window.after_idle(_apply)


def _force_linux_wm_borderless(window, target_w=_KIOSK_W, target_h=_KIOSK_H):
    """Unconditionally restore borderless kiosk geometry (ignore decoration refcount)."""
    global _linux_wm_decorated, _linux_wm_decorated_window
    if not use_kiosk_mode():
        _linux_wm_decorated = 0
        _linux_wm_decorated_window = None
        _configure_dev_window(window, target_w, target_h)
        return
    try:
        window.overrideredirect(True)
        window.title("")
        window.geometry(f"{target_w}x{target_h}+0+0")
        window.update_idletasks()
    except tk.TclError:
        pass
    _linux_wm_decorated = 0
    _linux_wm_decorated_window = None


def force_linux_kiosk_layout(window, target_w=_KIOSK_W, target_h=_KIOSK_H):
    """Clear keyboard WM state and restore window layout (kiosk or desktop)."""
    remove_keypad_keyboard()
    if use_kiosk_mode():
        _force_linux_wm_borderless(window, target_w, target_h)
    configure_linux_kiosk_window(window, target_w, target_h)


def release_linux_keyboard_field(widget):
    """Force-release a keyboard-enabled field (e.g. lot number cb before Setup)."""
    if not sys.platform.startswith("linux") or not use_kiosk_mode():
        return
    release = getattr(widget, "_release_linux_keyboard", None)
    if release is not None:
        release()


def prepare_linux_kiosk_for_hide(window, field=None, target_w=_KIOSK_W, target_h=_KIOSK_H):
    """Drop keyboard decorations before hiding Screen 1 (e.g. lot number cb was focused)."""
    if not sys.platform.startswith("linux"):
        return
    if field is not None:
        release_linux_keyboard_field(field)
    force_linux_kiosk_layout(window, target_w, target_h)
    try:
        window.update_idletasks()
    except tk.TclError:
        pass


def prime_linux_kiosk_keyboard(window, target_w=_KIOSK_W, target_h=_KIOSK_H):
    """Reset Pi keyboard delivery after Screen 1 is shown again."""
    if not sys.platform.startswith("linux"):
        return
    force_linux_kiosk_layout(window, target_w, target_h)
    try:
        window.update_idletasks()
        window.focus_force()
    except tk.TclError:
        pass


def configure_linux_kiosk_window(window, target_w=_KIOSK_W, target_h=_KIOSK_H):
    """Configure main Screen 1/2 window: Pi kiosk or movable 1024x600 on desktop OS."""
    if not use_kiosk_mode():
        _configure_dev_window(window, target_w, target_h)
        return
    if not sys.platform.startswith("linux"):
        return
    try:
        window.title("")
        window.configure(takefocus=True)
        window.overrideredirect(True)
        window.geometry(f"{target_w}x{target_h}+0+0")
    except tk.TclError:
        pass

    def _reposition():
        try:
            window.update_idletasks()
            window.overrideredirect(True)
            window.geometry(f"{target_w}x{target_h}+0+0")
        except tk.TclError:
            pass

    window.after_idle(_reposition)


def _linux_keypad_enter(window):
    """Briefly allow WM decorations so Pi/X11 delivers USB key events."""
    global _linux_wm_decorated, _linux_wm_decorated_window
    if not sys.platform.startswith("linux") or not use_kiosk_mode():
        return
    if _linux_wm_decorated == 0:
        _linux_wm_decorated_window = window
        try:
            window.overrideredirect(False)
            window.title("")
            window.lift()
            window.update_idletasks()
        except tk.TclError:
            pass
    _linux_wm_decorated += 1


def _linux_keypad_leave(window):
    global _linux_wm_decorated, _linux_wm_decorated_window
    if not sys.platform.startswith("linux") or not use_kiosk_mode():
        return
    if _linux_wm_decorated <= 0:
        return
    _linux_wm_decorated -= 1
    if _linux_wm_decorated == 0:
        target = _linux_wm_decorated_window or window
        _linux_wm_decorated_window = None
        try:
            if target.winfo_exists():
                target.overrideredirect(True)
                target.geometry(f"{_KIOSK_W}x{_KIOSK_H}+0+0")
                target.update_idletasks()
        except tk.TclError:
            pass


def install_linux_keyboard_field(widget):
    """Enable USB keyboard typing in a field on borderless Pi windows."""
    if not sys.platform.startswith("linux") or not use_kiosk_mode():
        return

    top = widget.winfo_toplevel()
    focus_epoch = [0]

    def release_field():
        focus_epoch[0] += 1
        root = widget._root()
        _force_linux_wm_borderless(top)
        try:
            root.focus_set()
            widget.tk.call("focus", root._w)
        except tk.TclError:
            pass
        try:
            top.update_idletasks()
        except tk.TclError:
            pass

    widget._release_linux_keyboard = release_field

    def on_focus_in(_event=None):
        focus_epoch[0] += 1
        _linux_keypad_enter(top)
        try:
            widget.focus_set()
            widget.tk.call("focus", widget._w)
        except tk.TclError:
            pass

    def on_focus_out(_event=None):
        epoch = focus_epoch[0]

        def check():
            if epoch != focus_epoch[0]:
                return
            try:
                focused = top.focus_get()
            except tk.TclError:
                focused = None
            if focused is widget:
                return
            _linux_keypad_leave(top)

        top.after(150, check)

    widget.bind("<FocusIn>", on_focus_in, add="+")
    widget.bind("<Button-1>", on_focus_in, add="+")
    widget.bind("<ButtonRelease-1>", on_focus_in, add="+")
    widget.bind("<FocusOut>", on_focus_out, add="+")


def configure_linux_app_root(root):
    """Keep Tk root mapped but invisible so the focus chain can receive keys (Pi kiosk)."""
    if not use_kiosk_mode():
        try:
            root.withdraw()
        except tk.TclError:
            pass
        return
    if not sys.platform.startswith("linux"):
        try:
            root.withdraw()
        except tk.TclError:
            pass
        return
    try:
        root.title("")
        root.overrideredirect(True)
        root.geometry("1x1+0+0")
        root.attributes("-alpha", 0.0)
        root.lower()
    except tk.TclError:
        try:
            root.withdraw()
        except tk.TclError:
            pass


def _keypad_bind_targets(widget):
    """Bind on the visible toplevel chain (withdrawn Tk root never gets keys on Pi)."""
    top = widget.winfo_toplevel()
    targets = []
    w = widget
    while w is not None:
        targets.append(w)
        if w is top:
            break
        w = w.master
    seen = set()
    ordered = []
    for t in targets:
        tid = id(t)
        if tid not in seen:
            seen.add(tid)
            ordered.append(t)
    return ordered


def _make_keypad_key_handler(append_fn, decimal_fn, backspace_fn, clear_fn, exit_fn):
    def on_key(event):
        keysym = event.keysym
        if keysym in ("Return", "KP_Enter"):
            exit_fn()
            return "break"
        if keysym == "Escape":
            exit_fn()
            return "break"
        if keysym == "BackSpace":
            backspace_fn()
            return "break"
        if keysym == "Delete":
            clear_fn()
            return "break"
        if keysym in "0123456789":
            append_fn(keysym)
            return "break"
        if keysym.startswith("KP_"):
            tail = keysym[3:]
            if tail.isdigit():
                append_fn(tail)
                return "break"
            if tail in ("Decimal", "Separator"):
                decimal_fn()
                return "break"
        if keysym in ("period", "KP_Decimal"):
            decimal_fn()
            return "break"

        ch = event.char
        if ch and len(ch) == 1:
            if ch in "0123456789":
                append_fn(ch)
                return "break"
            if ch == ".":
                decimal_fn()
                return "break"
            return "break"
        return None

    return on_key


def install_keypad_keyboard(widget, append_fn, decimal_fn, backspace_fn, clear_fn, exit_fn):
    """Bind keyboard on the preview entry and its visible windows."""
    global _active_keypad_binding, _active_keypad_window
    remove_keypad_keyboard()

    handler = _make_keypad_key_handler(
        append_fn, decimal_fn, backspace_fn, clear_fn, exit_fn
    )
    bindings = []
    for w in _keypad_bind_targets(widget):
        for seq in ("<KeyPress>", "<Key>"):
            funcid = w.bind(seq, handler, add="+")
            bindings.append(("widget", w, seq, funcid))

    if sys.platform.startswith("linux"):
        root = widget._root()
        for seq in ("<KeyPress>", "<Key>"):
            funcid = root.bind_all(seq, handler, add="+")
            bindings.append(("all", root, seq, funcid))

    _active_keypad_binding = bindings
    _active_keypad_window = widget.winfo_toplevel()
    _linux_keypad_enter(_active_keypad_window)

    top = _active_keypad_window
    try:
        top.focus_force()
    except tk.TclError:
        pass
    if getattr(widget, "_keypad_preview", False):
        focus_keypad_preview(widget)
        try:
            widget.tk.call("focus", widget._w)
        except tk.TclError:
            pass
    return handler


def remove_keypad_keyboard():
    """Release keyboard capture when the keypad closes."""
    global _active_keypad_binding, _active_keypad_window
    for item in _active_keypad_binding:
        _, target, seq, funcid = item
        try:
            target.unbind(seq, funcid)
        except tk.TclError:
            pass
    _active_keypad_binding = []
    if _active_keypad_window is not None:
        _linux_keypad_leave(_active_keypad_window)
        _active_keypad_window = None


def create_keypad_preview_entry(parent, string_var):
    """Editable preview field for numeric keypad (replaces read-only label)."""
    entry = tk.Entry(
        parent,
        textvariable=string_var,
        font=("Segoe UI", 20),
        justify=tk.CENTER,
        relief=tk.SUNKEN,
        width=10,
        exportselection=False,
    )
    try:
        entry.configure(takefocus=1)
    except tk.TclError:
        pass
    entry._keypad_preview = True
    return entry


def create_alpha_keypad_preview_entry(parent, string_var):
    """Editable preview field for alphanumeric keypad (wider for lot names)."""
    entry = tk.Entry(
        parent,
        textvariable=string_var,
        font=("Segoe UI", 20),
        justify=tk.CENTER,
        relief=tk.SUNKEN,
        width=18,
        exportselection=False,
    )
    try:
        entry.configure(takefocus=1)
    except tk.TclError:
        pass
    entry._keypad_preview = True
    return entry


def _make_alpha_keypad_key_handler(append_fn, backspace_fn, clear_fn, exit_fn):
    def on_key(event):
        keysym = event.keysym
        if keysym in ("Return", "KP_Enter"):
            exit_fn()
            return "break"
        if keysym == "Escape":
            exit_fn()
            return "break"
        if keysym == "BackSpace":
            backspace_fn()
            return "break"
        if keysym == "Delete":
            clear_fn()
            return "break"
        if keysym in ("Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R", "Caps_Lock"):
            return None
        if keysym in ("Left", "Right", "Home", "End", "Tab"):
            return None
        if keysym.startswith("KP_") and keysym[3:].isdigit():
            append_fn(keysym[3:])
            return "break"
        ch = event.char
        if ch and len(ch) == 1 and ch.isprintable() and not ch.isspace():
            append_fn(ch)
            return "break"
        return "break"

    return on_key


def install_alpha_keypad_keyboard(widget, append_fn, backspace_fn, clear_fn, exit_fn):
    """Bind USB keyboard for alphanumeric keypad preview entry."""
    global _active_keypad_binding, _active_keypad_window
    remove_keypad_keyboard()

    handler = _make_alpha_keypad_key_handler(append_fn, backspace_fn, clear_fn, exit_fn)
    bindings = []
    for w in _keypad_bind_targets(widget):
        for seq in ("<KeyPress>", "<Key>"):
            funcid = w.bind(seq, handler, add="+")
            bindings.append(("widget", w, seq, funcid))

    if sys.platform.startswith("linux"):
        root = widget._root()
        for seq in ("<KeyPress>", "<Key>"):
            funcid = root.bind_all(seq, handler, add="+")
            bindings.append(("all", root, seq, funcid))

    _active_keypad_binding = bindings
    _active_keypad_window = widget.winfo_toplevel()
    _linux_keypad_enter(_active_keypad_window)

    top = _active_keypad_window
    try:
        top.focus_force()
    except tk.TclError:
        pass
    if getattr(widget, "_keypad_preview", False):
        focus_keypad_preview(widget)
        try:
            widget.tk.call("focus", widget._w)
        except tk.TclError:
            pass
    return handler


def bind_keypad_preview_entry(entry, exit_fn):
    """Allow digits in the preview entry; Enter/Escape commit/close."""

    def on_key(event):
        keysym = event.keysym
        if keysym in ("Return", "KP_Enter"):
            exit_fn()
            return "break"
        if keysym == "Escape":
            exit_fn()
            return "break"
        if keysym in ("BackSpace", "Delete", "Left", "Right", "Home", "End", "Tab"):
            return None
        if keysym.startswith("KP_"):
            tail = keysym[3:]
            if tail.isdigit() or tail in ("Decimal", "Separator"):
                return None
        ch = event.char
        if ch and len(ch) == 1 and ch not in "0123456789.":
            return "break"
        return None

    entry.bind("<KeyPress>", on_key, add="+")


def focus_keypad_preview(entry):
    try:
        entry.focus_set()
        entry.icursor(tk.END)
        entry.selection_clear()
    except tk.TclError:
        pass


def _parse_input_device_blocks(content):
    blocks = []
    for block in content.strip().split("\n\n"):
        name = ""
        handlers = []
        ev_caps = ""
        for line in block.split("\n"):
            if line.startswith("N: Name="):
                name = line.split("=", 1)[1].strip().strip('"')
            elif "Handlers=" in line:
                handlers = line.split("Handlers=", 1)[1].strip().split()
            elif line.startswith("B: EV="):
                ev_caps = line.split("=", 1)[1].strip()
        blocks.append({"name": name, "handlers": handlers, "ev_caps": ev_caps})
    return blocks


def _is_real_keyboard_device(name, handlers, ev_caps):
    if "kbd" not in handlers:
        return False

    lowered = name.lower()
    if "vc4-hdmi" in lowered or "hdmi jack" in lowered:
        return False
    if "consumer control" in lowered:
        return False

    if ev_caps in ("120013", "12001f"):
        return True
    if "keyboard" in lowered:
        return True

    return False


def linux_has_physical_keyboard():
    """Return True if a USB/physical keyboard is present (Linux only)."""
    try:
        with open("/proc/bus/input/devices", "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except OSError:
        return False

    for device in _parse_input_device_blocks(content):
        if _is_real_keyboard_device(device["name"], device["handlers"], device["ev_caps"]):
            return True

    return False


def keypad_relx_for_side(side):
    """Horizontal center of keypad: left column at 75%, right column at 25%."""
    if side == "left":
        return 0.75
    if side == "right":
        return 0.25
    return 0.5


def place_inline_keypad_by_side(panel, owner_widget, side=None):
    """Place inline keypad using relative coords (stable on Pi touch displays)."""
    relx = keypad_relx_for_side(side)
    panel.place(relx=relx, rely=_KEYPAD_RELY, anchor="center")
    try:
        panel.lift()
    except tk.TclError:
        pass


def place_toplevel_keypad_by_side(toplevel, owner_widget, side=None):
    """Place modal keypad using window-relative pixel math."""
    owner_widget.update_idletasks()
    toplevel.update_idletasks()

    owner_w = owner_widget.winfo_width()
    owner_h = owner_widget.winfo_height()
    keypad_w = toplevel.winfo_width()
    keypad_h = toplevel.winfo_height()

    center_x = keypad_relx_for_side(side) * owner_w
    center_y = _KEYPAD_RELY * owner_h

    x = int(round(center_x - keypad_w / 2.0))
    y = int(round(center_y - keypad_h / 2.0))
    x = max(0, min(x, max(0, owner_w - keypad_w)))
    y = max(0, min(y, max(0, owner_h - keypad_h)))

    root_x = owner_widget.winfo_rootx() + x
    root_y = owner_widget.winfo_rooty() + y
    toplevel.geometry(f"+{root_x}+{root_y}")
