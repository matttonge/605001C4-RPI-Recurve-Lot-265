"""System Python on Ubuntu must pick up the project venv (pygubu)."""

import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SYSTEM_PYTHON = "/bin/python"


class EnsureVenvTests(unittest.TestCase):
    def test_system_python_imports_pygubu_after_ensure_venv(self):
        """Cursor 'Run Python File' uses /bin/python, which has no pygubu."""
        result = subprocess.run(
            [
                SYSTEM_PYTHON,
                "-c",
                "import ensure_venv; import pygubu; print('ok')",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=15,
        )
        self.assertEqual(
            result.returncode,
            0,
            f"stdout={result.stdout!r}\nstderr={result.stderr!r}",
        )
        self.assertIn("ok", result.stdout)


if __name__ == "__main__":
    unittest.main()
