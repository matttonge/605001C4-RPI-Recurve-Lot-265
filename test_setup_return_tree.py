"""Regression: returning from Setup must not touch a destroyed Screen 1 tree."""

from __future__ import annotations

import inspect
import tkinter as tk
from tkinter import ttk
import unittest

import screen_2_app
from Run_Screen_1b import RcPage1bApp


class SetupReturnTreeTests(unittest.TestCase):
    def test_setup_run_uses_wait_window_not_nested_mainloop(self):
        src = inspect.getsource(screen_2_app.RcSetupPage2App.run)
        self.assertIn("wait_window", src)
        self.assertNotIn(".mainloop(", src)

    def test_clear_treeview_ignores_destroyed_widget(self):
        root = tk.Tk()
        root.withdraw()
        try:
            top = tk.Toplevel(root)
            tree = ttk.Treeview(top)
            tree.insert("", tk.END, values=(1,))
            top.destroy()
            root.update_idletasks()
            # Should not raise TclError once Screen 1 widgets are gone.
            RcPage1bApp.clear_treeview(None, tree)
        finally:
            try:
                root.destroy()
            except tk.TclError:
                pass

    def test_wait_window_keeps_parent_tree_alive(self):
        """Modal Setup must not nest mainloop; parent tree stays valid after close."""
        root = tk.Tk()
        root.withdraw()
        parent = tk.Toplevel(root)
        tree = ttk.Treeview(parent)
        tree.insert("", tk.END, iid="1", values=(1,))
        setup = tk.Toplevel(root)

        def close_setup():
            setup.destroy()

        setup.after(50, close_setup)
        # Mimic fixed Setup.run(): block on this window only.
        setup.wait_window(setup)
        self.assertTrue(parent.winfo_exists())
        self.assertTrue(tree.winfo_exists())
        self.assertEqual(tree.get_children(), ("1",))
        parent.destroy()
        root.destroy()

    def test_screen1_stays_mapped_under_setup(self):
        """Screen 1 must stay mapped so closing Setup never reveals the desktop."""
        src = inspect.getsource(RcPage1bApp.btn_setup)
        self.assertNotIn("withdraw", src)
        self.assertNotIn("deiconify", src)
        exit_src = inspect.getsource(screen_2_app.RcSetupPage2App.btn_exit)
        self.assertIn("reload_current_lot", exit_src)
        lift_at = exit_src.find("balloonwindow.lift")
        destroy_at = exit_src.find("mainwindow.destroy")
        self.assertGreater(lift_at, 0)
        self.assertGreater(destroy_at, 0)
        self.assertLess(lift_at, destroy_at)


if __name__ == "__main__":
    unittest.main()
